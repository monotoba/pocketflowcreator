"""Single-file node package loader for PocketFlow Creator.

A **node package** is a single ``.py`` file that follows the documented
convention:

1. **Module docstring** — RFC-822-style key/value pairs that carry human-
   readable metadata:

   .. code-block:: text

       Node: Weather Fetch
       Category: Web / Search
       Version: 1.0.0
       Author: Jane Dev
       Website: https://janedev.com
       Repo: https://github.com/janedev/weather-node
       Description: Fetches current weather conditions for a city.
       Tags: weather, api, http
       Min-Creator-Version: 0.2.0
       License: MIT

2. **Optional dunders** — machine-readable metadata at module scope:

   .. code-block:: python

       __node_actions__: list[str] = ["default", "error"]
       __node_properties__: dict = {
           "city_key": {"type": "string", "default": "city", "description": "..."},
       }
       __node_color__: str = "#0277bd"        # hex bg colour for the icon
       __node_icon__ = None                   # or a (p, sz, bg) -> None callable

3. **A Node subclass** — exactly one class that either inherits from
   ``pocketflow.Node`` or has ``prep`` / ``exec`` / ``post`` methods. The
   class name becomes the node's ``type_id`` (snake_cased).

Loader behaviour:

- Files are loaded from ``~/.pocketflow_creator/nodes/`` by default.
- Each file is wrapped in a ``try/except`` so a bad package never crashes
  the application; errors are collected and returned.
- The loader registers the background colour in ``NODE_TYPE_COLOR`` and
  an optional draw-function in ``_ICON_DRAW`` so ``make_node_icon`` works
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


# ── Docstring metadata parser ─────────────────────────────────────────────────

_RFC822_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 _-]*):\s*(.+)$")


def _parse_docstring(doc: str) -> dict[str, str]:
    """Extract RFC-822-style key/value pairs from a module docstring.

    Only lines of the form ``Key: value`` are extracted; blank lines and
    plain prose are ignored.  Keys are normalised to lower-case with spaces
    replaced by underscores (e.g. ``Min-Creator-Version`` → ``min_creator_version``).
    """
    meta: dict[str, str] = {}
    for line in doc.splitlines():
        m = _RFC822_RE.match(line.strip())
        if m:
            key = m.group(1).strip().lower().replace(" ", "_").replace("-", "_")
            meta[key] = m.group(2).strip()
    return meta


# ── type_id derivation ────────────────────────────────────────────────────────

def _to_type_id(display_name: str) -> str:
    """Convert a display name to a snake_case type_id.

    Examples::

        "Weather Fetch"  → "weather_fetch_node"
        "MyCustomNode"   → "my_custom_node"
        "sql_runner"     → "sql_runner_node"
        "rag_node"       → "rag_node"          (already ends with _node)
    """
    # Insert underscores before upper-case runs (CamelCase → snake_case)
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", display_name)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", s)
    # Replace spaces/hyphens/dots with underscores
    s = re.sub(r"[ \-\.]+", "_", s)
    s = s.lower()
    # Collapse multiple underscores
    s = re.sub(r"_+", "_", s).strip("_")
    if not s.endswith("_node"):
        s = s + "_node"
    return s


# ── Node subclass detection ───────────────────────────────────────────────────

def _find_node_class(module: types.ModuleType) -> type | None:
    """Return the first Node subclass defined in the module, or None.

    Heuristics (tried in order):
    1. A class that subclasses ``pocketflow.Node`` (or any class named ``Node``
       from any module).
    2. A class that has ``prep``, ``exec``, and ``post`` methods.

    Built-in classes (defined outside the loaded file) are skipped.
    """
    source_file = getattr(module, "__file__", None)
    candidates: list[type] = []
    for _name, obj in inspect.getmembers(module, inspect.isclass):
        # Skip classes not defined in this module
        if getattr(obj, "__module__", None) != module.__name__:
            continue
        # Accept if it looks like a PocketFlow Node subclass
        for base in inspect.getmro(obj)[1:]:
            if base.__name__ == "Node":
                candidates.append(obj)
                break
        else:
            # Fallback: duck-type check for prep/exec/post
            if all(hasattr(obj, m) for m in ("prep", "exec", "post")):
                candidates.append(obj)
    return candidates[0] if candidates else None


# ── Icon registration ─────────────────────────────────────────────────────────

_DEFAULT_CUSTOM_COLOR = "#555555"


def _register_icon(type_id: str, color: str, draw_fn: Any | None) -> None:
    """Register ``type_id`` in the icons module's lookup tables.

    This is intentionally done at the module level of ``icons.py`` so that
    ``make_node_icon(type_id)`` works without any additional plumbing.
    """
    try:
        from pocketflow_creator.app.canvas import icons as _icons

        _icons.NODE_TYPE_COLOR[type_id] = color
        if callable(draw_fn):
            _icons._ICON_DRAW[type_id] = draw_fn
    except Exception:
        # Qt may not be available in test environments — silently skip.
        pass


# ── Core loader ───────────────────────────────────────────────────────────────

class PackageLoadError(Exception):
    """Raised when a node package file cannot be loaded."""


def load_node_package(path: Path) -> NodeTypeDefinition:
    """Load a single ``.py`` node package file.

    Parameters
    ----------
    path:
        Absolute path to the ``.py`` file.

    Returns
    -------
    NodeTypeDefinition
        Ready-to-use definition with ``source_file`` set to *path*.

    Raises
    ------
    PackageLoadError
        On any error (import failure, no Node subclass found, etc.).
    """
    if not path.is_file():
        raise PackageLoadError(f"File not found: {path}")
    if path.suffix != ".py":
        raise PackageLoadError(f"Expected a .py file, got: {path.name}")

    # Build a unique module name to avoid collisions
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

    # ── Parse docstring metadata ──────────────────────────────────────────
    doc = inspect.getdoc(module) or ""
    meta = _parse_docstring(doc)

    display_name: str = meta.get("node", "").strip() or path.stem.replace("_", " ").title()
    category: str = meta.get("category", "Custom").strip()
    version: str = meta.get("version", "0.0.0").strip()
    author: str = meta.get("author", "").strip()
    website: str = meta.get("website", "").strip()
    repo: str = meta.get("repo", "").strip()
    description: str = meta.get("description", "").strip()
    tags_raw: str = meta.get("tags", "").strip()
    tags: list[str] = [t.strip() for t in tags_raw.split(",") if t.strip()]
    license_: str = meta.get("license", "").strip()
    min_creator: str = meta.get("min_creator_version", "").strip()

    # ── Read dunders ──────────────────────────────────────────────────────
    actions: list[str] = list(getattr(module, "__node_actions__", ["default"]))
    properties: dict[str, Any] = dict(getattr(module, "__node_properties__", {}))
    color: str = str(getattr(module, "__node_color__", _DEFAULT_CUSTOM_COLOR)).strip()
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

    # Extended metadata lives in the separate _PACKAGE_META dict because
    # NodeTypeDefinition uses slots=True and cannot hold extra attributes.
    meta: dict[str, Any] = {
        "source_file": str(path),
        "version": version,
        "author": author,
        "website": website,
        "repo": repo,
        "tags": tags,
        "license": license_,
        "min_creator_version": min_creator,
    }
    _PACKAGE_META[type_id] = meta

    return defn


# ── In-process registry ───────────────────────────────────────────────────────
# Populated by discover_user_nodes(); queried by the palette and toolbar.
# _PACKAGE_META holds the extended metadata (version, author, etc.) keyed by
# type_id, since NodeTypeDefinition uses slots=True and can't store extras.

_USER_NODE_REGISTRY: dict[str, NodeTypeDefinition] = {}
_PACKAGE_META: dict[str, dict[str, Any]] = {}


def register_user_node(defn: NodeTypeDefinition, meta: dict[str, Any] | None = None) -> None:
    """Add *defn* (and optional extended *meta*) to the in-process registry."""
    _USER_NODE_REGISTRY[defn.node_type_id] = defn
    if meta is not None:
        _PACKAGE_META[defn.node_type_id] = meta


def get_package_meta(type_id: str) -> dict[str, Any]:
    """Return extended package metadata for *type_id*, or an empty dict."""
    return dict(_PACKAGE_META.get(type_id, {}))


def get_all_user_nodes() -> dict[str, NodeTypeDefinition]:
    """Return a shallow copy of the current user-node registry."""
    return dict(_USER_NODE_REGISTRY)


def get_user_node_groups() -> list[tuple[str, list[tuple[str, NodeTypeDefinition]]]]:
    """Return user nodes grouped by category (alphabetical within each group)."""
    from collections import defaultdict

    groups: dict[str, list[tuple[str, NodeTypeDefinition]]] = defaultdict(list)
    for type_id, defn in _USER_NODE_REGISTRY.items():
        groups[defn.category].append((type_id, defn))
    return [(cat, items) for cat, items in sorted(groups.items())]


# ── Discovery ─────────────────────────────────────────────────────────────────

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
            register_user_node(defn)
            _log.info("Loaded node package: %s (%s)", defn.display_name, py_file.name)
        except PackageLoadError as exc:
            errors.append((py_file.name, str(exc)))
            _log.warning("Failed to load node package %s: %s", py_file.name, exc)

    return definitions, errors


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
