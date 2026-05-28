"""Single-file node package loader for PocketFlow Creator.

Bundled node packages ship with Creator under
``pocketflow_creator/bundled_nodes/`` and are loaded at startup before user
packages.  They appear in the palette under a "Scientific & Engineering" banner
(or grouped by their own categories) before the user-node section.



A **node package** is a single ``.py`` file.  All metadata is declared in a
module-level ``__node_meta__`` dict so it is plain Python — no parsing, no
special syntax, easy to write and validate in any editor:

.. code-block:: python

    __node_meta__ = {
        # ── Identity ──────────────────────────────────────────────────────
        "node":               "Weather Fetch",
        "category":           "Web / Search",
        # ── Package info ──────────────────────────────────────────────────
        "version":            "1.0.0",
        "author":             "Jane Dev",
        "website":            "https://janedev.com",
        "repo":               "https://github.com/janedev/weather-node",
        "description":        "Fetches current weather conditions for a city.",
        "tags":               ["weather", "api", "http"],
        "license":            "MIT",
        "min_creator_version": "0.2.0",
        # ── Node behaviour ────────────────────────────────────────────────
        "actions":    ["default", "error"],
        "properties": {
            "city_key": {
                "type": "string",
                "default": "city",
                "description": "Shared-store key for the target city name",
            },
        },
        # ── Visual ────────────────────────────────────────────────────────
        "color": "#0277bd",   # hex background colour for the palette icon
    }

    # Optional: provide a custom icon draw-function.
    # Signature must be (p: QPainter, sz: float, bg: QColor) -> None.
    # Omit (or set to None) to use the auto-generated two-letter initials icon.
    __node_icon__ = None

    class WeatherFetchNode:
        def prep(self, shared): ...
        def exec(self, prep_res): ...
        def post(self, shared, prep_res, exec_res): ...

The module docstring is free for human-readable documentation.

Loader behaviour
----------------
- Files are loaded from ``~/.pocketflow_creator/nodes/`` by default.
- Each file is wrapped in a ``try/except`` so a bad package never crashes
  the application; errors are collected and returned.
- The loader registers the background colour in ``NODE_TYPE_COLOR`` and the
  optional draw-function in ``_ICON_DRAW`` so ``make_node_icon`` works
  immediately for every loaded type.
"""
from __future__ import annotations

import importlib.util
import inspect
import logging
import re
import sys
import types
from pathlib import Path
from typing import Any

from pocketflow_creator.model.node_type import NodeTypeDefinition

_log = logging.getLogger(__name__)

# ── User node directory ───────────────────────────────────────────────────────

_USER_NODES_DIR = Path.home() / ".pocketflow_creator" / "nodes"


def get_user_nodes_dir() -> Path:
    """Return (and create if necessary) the user node packages directory."""
    _USER_NODES_DIR.mkdir(parents=True, exist_ok=True)
    return _USER_NODES_DIR


# ── type_id derivation ────────────────────────────────────────────────────────

def _to_type_id(display_name: str) -> str:
    """Convert a display name or class name to a snake_case ``type_id``.

    Examples::

        "Weather Fetch"  → "weather_fetch_node"
        "MyCustomNode"   → "my_custom_node"
        "SQLRunner"      → "sql_runner_node"
        "sql_runner"     → "sql_runner_node"
        "rag_node"       → "rag_node"          (already ends with _node)
    """
    # CamelCase → snake_case: insert _ before UpperLower boundary inside runs
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", display_name)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", s)
    # Spaces, hyphens, dots → underscore
    s = re.sub(r"[ \-\.]+", "_", s)
    s = s.lower()
    # Collapse repeated underscores
    s = re.sub(r"_+", "_", s).strip("_")
    if not s.endswith("_node"):
        s = s + "_node"
    return s


# ── Node subclass detection ───────────────────────────────────────────────────

def _find_node_class(module: types.ModuleType) -> type | None:
    """Return the first Node subclass defined in *module*, or ``None``.

    Heuristics (tried in order):

    1. A class that subclasses any class named ``Node`` (covers
       ``pocketflow.Node`` and any other base named Node).
    2. Duck-type: a class with ``prep``, ``exec``, and ``post`` methods.

    Classes not defined in this module (imported helpers, etc.) are skipped.
    """
    candidates: list[type] = []
    for _name, obj in inspect.getmembers(module, inspect.isclass):
        if getattr(obj, "__module__", None) != module.__name__:
            continue
        for base in inspect.getmro(obj)[1:]:
            if base.__name__ == "Node":
                candidates.append(obj)
                break
        else:
            if all(hasattr(obj, m) for m in ("prep", "exec", "post")):
                candidates.append(obj)
    return candidates[0] if candidates else None


# ── Icon registration ─────────────────────────────────────────────────────────

_DEFAULT_CUSTOM_COLOR = "#555555"


def _register_icon(type_id: str, color: str, draw_fn: Any | None) -> None:
    """Register *type_id* colour and optional draw-fn in the icons module."""
    try:
        from pocketflow_creator.app.canvas import icons as _icons

        _icons.NODE_TYPE_COLOR[type_id] = color
        if callable(draw_fn):
            _icons._ICON_DRAW[type_id] = draw_fn
    except Exception:
        # Qt may not be available in test environments — silently skip.
        pass


# ── In-process registry ───────────────────────────────────────────────────────
# Populated by discover_user_nodes() / discover_bundled_nodes().
# _PACKAGE_META holds extended metadata keyed by type_id.
# NodeTypeDefinition uses slots=True so we cannot attach extra attributes.
#
# Two separate registries so the palette can show bundled nodes in their own
# section, distinct from the user's custom nodes.

_USER_NODE_REGISTRY: dict[str, NodeTypeDefinition] = {}
_BUNDLED_NODE_REGISTRY: dict[str, NodeTypeDefinition] = {}
_PACKAGE_META: dict[str, dict[str, Any]] = {}


def register_user_node(
    defn: NodeTypeDefinition,
    meta: dict[str, Any] | None = None,
    bundled: bool = False,
) -> None:
    """Add *defn* to the user (or bundled) registry.

    Parameters
    ----------
    defn:
        Node type definition to register.
    meta:
        Optional extended metadata dict (version, author, etc.).
    bundled:
        If ``True``, register in ``_BUNDLED_NODE_REGISTRY`` instead of
        ``_USER_NODE_REGISTRY``.
    """
    if bundled:
        _BUNDLED_NODE_REGISTRY[defn.node_type_id] = defn
    else:
        _USER_NODE_REGISTRY[defn.node_type_id] = defn
    if meta is not None:
        _PACKAGE_META[defn.node_type_id] = meta


def get_package_meta(type_id: str) -> dict[str, Any]:
    """Return extended package metadata for *type_id*, or an empty dict."""
    return dict(_PACKAGE_META.get(type_id, {}))


def get_all_user_nodes() -> dict[str, NodeTypeDefinition]:
    """Return a shallow copy of the current user-node registry."""
    return dict(_USER_NODE_REGISTRY)


def get_all_bundled_nodes() -> dict[str, NodeTypeDefinition]:
    """Return a shallow copy of the bundled-node registry."""
    return dict(_BUNDLED_NODE_REGISTRY)


def get_user_node_groups() -> list[tuple[str, list[tuple[str, NodeTypeDefinition]]]]:
    """Return user nodes grouped by category (alphabetical within each group)."""
    from collections import defaultdict

    groups: dict[str, list[tuple[str, NodeTypeDefinition]]] = defaultdict(list)
    for type_id, defn in _USER_NODE_REGISTRY.items():
        groups[defn.category].append((type_id, defn))
    return [(cat, items) for cat, items in sorted(groups.items())]


def get_bundled_node_groups() -> list[tuple[str, list[tuple[str, NodeTypeDefinition]]]]:
    """Return bundled nodes grouped by category, sorted by category name."""
    from collections import defaultdict

    # Preferred display order for bundled categories
    _BUNDLED_CATEGORY_ORDER = [
        "Scientific Computing",
        "Aerospace",
        "Wind Energy",
        "Weather / Atmosphere",
        "Building Energy",
        "Hydrology / Water",
        "Geospatial",
        "Data Catalog",
    ]

    groups: dict[str, list[tuple[str, NodeTypeDefinition]]] = defaultdict(list)
    for type_id, defn in _BUNDLED_NODE_REGISTRY.items():
        groups[defn.category].append((type_id, defn))

    result = []
    seen: set[str] = set()
    for cat in _BUNDLED_CATEGORY_ORDER:
        if cat in groups:
            result.append((cat, sorted(groups[cat], key=lambda x: x[1].display_name)))
            seen.add(cat)
    for cat in sorted(groups):
        if cat not in seen:
            result.append((cat, sorted(groups[cat], key=lambda x: x[1].display_name)))
    return result


# ── Core loader ───────────────────────────────────────────────────────────────

class PackageLoadError(Exception):
    """Raised when a node package file cannot be loaded."""


def load_node_package(path: Path) -> NodeTypeDefinition:
    """Load a single ``.py`` node package file.

    Reads all metadata from the module-level ``__node_meta__`` dict and the
    optional ``__node_icon__`` dunder.  See the module docstring for the full
    key reference.

    Parameters
    ----------
    path:
        Absolute path to the ``.py`` file.

    Returns
    -------
    NodeTypeDefinition
        Ready-to-use definition.  Extended metadata (version, author, etc.)
        is stored in ``_PACKAGE_META[type_id]`` and accessible via
        :func:`get_package_meta`.

    Raises
    ------
    PackageLoadError
        On any error (import failure, missing ``__node_meta__``, no Node
        subclass found, etc.).
    """
    if not path.is_file():
        raise PackageLoadError(f"File not found: {path}")
    if path.suffix != ".py":
        raise PackageLoadError(f"Expected a .py file, got: {path.name}")

    # ── Import the module ─────────────────────────────────────────────────
    module_name = f"_pfc_node_pkg_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise PackageLoadError(f"Cannot create module spec for: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception as exc:
        del sys.modules[module_name]
        raise PackageLoadError(f"Import error in {path.name}: {exc}") from exc

    # ── Read __node_meta__ ────────────────────────────────────────────────
    raw_meta = getattr(module, "__node_meta__", None)
    if raw_meta is None:
        del sys.modules[module_name]
        raise PackageLoadError(
            f"No __node_meta__ dict found in {path.name}. "
            "Add a module-level __node_meta__ = {...} declaration."
        )
    if not isinstance(raw_meta, dict):
        del sys.modules[module_name]
        raise PackageLoadError(
            f"__node_meta__ in {path.name} must be a dict, "
            f"got {type(raw_meta).__name__}."
        )

    # ── Extract fields with defaults ──────────────────────────────────────
    display_name: str = str(raw_meta.get("node", "")).strip() or path.stem.replace("_", " ").title()
    category: str     = str(raw_meta.get("category", "Custom")).strip()
    version: str      = str(raw_meta.get("version", "0.0.0")).strip()
    author: str       = str(raw_meta.get("author", "")).strip()
    website: str      = str(raw_meta.get("website", "")).strip()
    repo: str         = str(raw_meta.get("repo", "")).strip()
    description: str  = str(raw_meta.get("description", "")).strip()
    license_: str     = str(raw_meta.get("license", "")).strip()
    min_creator: str  = str(raw_meta.get("min_creator_version", "")).strip()
    color: str        = str(raw_meta.get("color", _DEFAULT_CUSTOM_COLOR)).strip()

    # tags may be a list or a comma-separated string
    raw_tags = raw_meta.get("tags", [])
    if isinstance(raw_tags, str):
        tags: list[str] = [t.strip() for t in raw_tags.split(",") if t.strip()]
    else:
        tags = [str(t).strip() for t in raw_tags if str(t).strip()]

    actions: list[str]      = list(raw_meta.get("actions", ["default"]))
    properties: dict[str, Any] = dict(raw_meta.get("properties", {}))

    # __node_icon__ stays as a separate dunder since it's a callable
    icon_draw = getattr(module, "__node_icon__", None)

    # ── Locate the Node subclass to derive type_id ────────────────────────
    node_cls = _find_node_class(module)
    if node_cls is None:
        del sys.modules[module_name]
        raise PackageLoadError(
            f"No Node subclass found in {path.name}. "
            "Define a class that extends pocketflow.Node."
        )

    type_id = _to_type_id(node_cls.__name__)

    # ── Register icon ─────────────────────────────────────────────────────
    _register_icon(type_id, color, icon_draw)

    # ── Build NodeTypeDefinition ──────────────────────────────────────────
    defn = NodeTypeDefinition(
        node_type_id=type_id,
        display_name=display_name,
        category=category,
        base_class="Node",
        description=description,
        actions=actions,
        properties=properties,
    )

    # Store extended metadata separately (NodeTypeDefinition is slotted)
    _PACKAGE_META[type_id] = {
        "source_file":        str(path),
        "version":            version,
        "author":             author,
        "website":            website,
        "repo":               repo,
        "tags":               tags,
        "license":            license_,
        "min_creator_version": min_creator,
    }

    return defn


# ── Discovery ─────────────────────────────────────────────────────────────────

def _scan_directory(
    directory: Path,
    bundled: bool = False,
) -> tuple[list[NodeTypeDefinition], list[tuple[str, str]]]:
    """Internal: scan *directory* for node packages and register them."""
    definitions: list[NodeTypeDefinition] = []
    errors: list[tuple[str, str]] = []

    if not directory.exists():
        return definitions, errors

    for py_file in sorted(directory.glob("*.py")):
        if py_file.name.startswith("_"):
            continue  # skip __init__.py and private helpers
        try:
            defn = load_node_package(py_file)  # also populates _PACKAGE_META
            definitions.append(defn)
            register_user_node(defn, bundled=bundled)
            label = "bundled" if bundled else "user"
            _log.info("Loaded %s node package: %s (%s)", label, defn.display_name, py_file.name)
        except PackageLoadError as exc:
            errors.append((py_file.name, str(exc)))
            _log.warning("Failed to load node package %s: %s", py_file.name, exc)

    return definitions, errors


def discover_bundled_nodes() -> tuple[list[NodeTypeDefinition], list[tuple[str, str]]]:
    """Load the node packages that ship with PocketFlow Creator.

    Packages live in ``pocketflow_creator/bundled_nodes/`` inside the installed
    package.  They are registered in ``_BUNDLED_NODE_REGISTRY`` so the palette
    can show them in a dedicated section separate from the user's own nodes.

    Returns
    -------
    (definitions, errors)
    """
    bundled_dir = Path(__file__).parent / "bundled_nodes"
    return _scan_directory(bundled_dir, bundled=True)


def discover_user_nodes(
    nodes_dir: Path | None = None,
) -> tuple[list[NodeTypeDefinition], list[tuple[str, str]]]:
    """Scan *nodes_dir* for ``.py`` node packages and load them all.

    Parameters
    ----------
    nodes_dir:
        Directory to scan.  Defaults to ``~/.pocketflow_creator/nodes/``.

    Returns
    -------
    (definitions, errors)
        *definitions* — successfully loaded ``NodeTypeDefinition`` objects.
        *errors* — list of ``(filename, error_message)`` pairs for failures.
    """
    directory = nodes_dir or get_user_nodes_dir()
    return _scan_directory(directory, bundled=False)


# ── Install helper ────────────────────────────────────────────────────────────

def install_node_package(src: Path, overwrite: bool = False) -> Path:
    """Copy *src* into the user nodes directory.

    Parameters
    ----------
    src:
        Source ``.py`` file to install.
    overwrite:
        If ``False`` (default) and the destination already exists, raise
        ``FileExistsError``.

    Returns
    -------
    Path
        The destination path inside the user nodes directory.
    """
    dest = get_user_nodes_dir() / src.name
    if dest.exists() and not overwrite:
        raise FileExistsError(
            f"{dest.name} is already installed. "
            "Pass overwrite=True to replace it."
        )
    import shutil
    shutil.copy2(src, dest)
    return dest
