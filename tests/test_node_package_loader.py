"""Tests for the node package loader (single-file and multi-file)."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from pocketflow_creator.node_package_loader import (
    _PACKAGE_META,
    PackageLoadError,
    _to_type_id,
    discover_addon_nodes,
    discover_user_nodes,
    install_node_package,
    load_node_package,
)

# ── _to_type_id ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name,expected", [
    ("WeatherFetch",        "weather_fetch_node"),
    ("Weather Fetch",       "weather_fetch_node"),
    ("weather_fetch",       "weather_fetch_node"),
    ("rag_node",            "rag_node"),              # already ends in _node
    ("MyCustomNode",        "my_custom_node"),
    ("SQLRunner",           "sql_runner_node"),        # CamelCase with acronym
    ("api_call",            "api_call_node"),
])
def test_to_type_id(name, expected):
    assert _to_type_id(name) == expected


# ── load_node_package ─────────────────────────────────────────────────────────

_GOOD_PACKAGE = textwrap.dedent("""\
    __node_meta__ = {
        "node":        "Ping",
        "category":    "Networking",
        "version":     "0.1.0",
        "author":      "Test Author",
        "website":     "https://example.com",
        "repo":        "https://github.com/example/ping-node",
        "description": "Sends a ping.",
        "tags":        ["net", "ping"],
        "license":     "MIT",
        "actions":     ["success", "timeout"],
        "properties":  {
            "host_key": {"type": "string", "default": "host", "description": "Target host"},
        },
        "color":       "#0277bd",
    }

    class PingNode:
        def prep(self, shared):
            return shared.get("host", "localhost")

        def exec(self, prep_res):
            return {"host": prep_res, "alive": True}

        def post(self, shared, prep_res, exec_res):
            shared["ping_result"] = exec_res
            return "success"
""")

_NO_CLASS_PACKAGE = textwrap.dedent("""\
    __node_meta__ = {"node": "Broken", "category": "Custom"}

    def some_function():
        pass
""")

_SYNTAX_ERROR_PACKAGE = "def broken(:\n    pass\n"


def test_load_good_package(tmp_path):
    f = tmp_path / "ping_node.py"
    f.write_text(_GOOD_PACKAGE, encoding="utf-8")
    defn = load_node_package(f)

    assert defn.display_name == "Ping"
    assert defn.category == "Networking"
    assert defn.node_type_id == "ping_node"
    assert defn.actions == ["success", "timeout"]
    assert "host_key" in defn.properties
    assert defn.description == "Sends a ping."

    meta = _PACKAGE_META["ping_node"]
    assert meta["version"] == "0.1.0"
    assert meta["author"] == "Test Author"
    assert meta["website"] == "https://example.com"
    assert meta["repo"] == "https://github.com/example/ping-node"
    assert meta["tags"] == ["net", "ping"]
    assert meta["license"] == "MIT"
    assert meta["source_file"] == str(f)


def test_load_no_meta_raises(tmp_path):
    f = tmp_path / "no_meta.py"
    f.write_text("class MyNode:\n    def prep(self,s): pass\n    def exec(self,p): pass\n    def post(self,s,p,e): pass\n", encoding="utf-8")
    with pytest.raises(PackageLoadError, match="__node_meta__"):
        load_node_package(f)


def test_load_no_class_raises(tmp_path):
    f = tmp_path / "no_class.py"
    f.write_text(_NO_CLASS_PACKAGE, encoding="utf-8")
    with pytest.raises(PackageLoadError, match="No Node subclass"):
        load_node_package(f)


def test_load_syntax_error_raises(tmp_path):
    f = tmp_path / "syntax_error.py"
    f.write_text(_SYNTAX_ERROR_PACKAGE, encoding="utf-8")
    with pytest.raises(PackageLoadError, match="Import error"):
        load_node_package(f)


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(PackageLoadError, match="File not found"):
        load_node_package(tmp_path / "nonexistent.py")


def test_load_wrong_extension_raises(tmp_path):
    f = tmp_path / "node.yaml"
    f.write_text("Node: X\n", encoding="utf-8")
    with pytest.raises(PackageLoadError, match=".py"):
        load_node_package(f)


# ── discover_user_nodes ───────────────────────────────────────────────────────

def test_discover_empty_dir(tmp_path):
    defns, errors = discover_user_nodes(tmp_path)
    assert defns == []
    assert errors == []


def test_discover_skips_private_files(tmp_path):
    (tmp_path / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "_helper.py").write_text("", encoding="utf-8")
    defns, errors = discover_user_nodes(tmp_path)
    assert defns == []
    assert errors == []


def test_discover_loads_good_and_reports_bad(tmp_path):
    (tmp_path / "ping_node.py").write_text(_GOOD_PACKAGE, encoding="utf-8")
    (tmp_path / "broken.py").write_text(_NO_CLASS_PACKAGE, encoding="utf-8")
    defns, errors = discover_user_nodes(tmp_path)
    assert len(defns) == 1
    assert defns[0].display_name == "Ping"
    assert len(errors) == 1
    assert errors[0][0] == "broken.py"


def test_discover_nonexistent_dir(tmp_path):
    defns, errors = discover_user_nodes(tmp_path / "does_not_exist")
    assert defns == []
    assert errors == []


# ── discover_addon_nodes ────────────────────────────────────────────────────

def test_discover_addon_nodes_finds_all():
    """Add-on node packages should all load without errors."""
    defns, errors = discover_addon_nodes()
    # Verify all 34 addon packages loaded
    assert len(defns) == 34, (
        f"Expected 34 addon nodes, got {len(defns)}. "
        f"Errors: {errors}"
    )
    assert errors == [], f"Unexpected load errors: {errors}"


def test_discover_addon_nodes_categories():
    """Add-on nodes should span the expected scientific / engineering categories."""
    expected_categories = {
        "Scientific Computing",
        "Aerospace",
        "Wind Energy",
        "Weather / Atmosphere",
        "Building Energy",
        "Hydrology / Water",
        "Geospatial",
        "Data Catalog",
    }
    defns, _ = discover_addon_nodes()
    actual_categories = {d.category for d in defns}
    assert expected_categories == actual_categories, (
        f"Category mismatch.\n"
        f"Expected: {sorted(expected_categories)}\n"
        f"Got:      {sorted(actual_categories)}"
    )


# ── multi-file package loading ────────────────────────────────────────────────

_MULTIFILE_MAIN = textwrap.dedent("""\
    from . import helpers

    __node_meta__ = {
        "node":        "Multi Ping",
        "category":    "Networking",
        "version":     "1.0.0",
        "author":      "Test",
        "description": "Ping with helper module.",
        "actions":     ["success", "timeout"],
        "properties":  {},
    }

    class MultiPingNode:
        def prep(self, shared):
            return helpers.default_host(shared)

        def exec(self, prep_res):
            return {"host": prep_res, "alive": True}

        def post(self, shared, prep_res, exec_res):
            shared["ping_result"] = exec_res
            return "success"
""")

_MULTIFILE_HELPER = textwrap.dedent("""\
    def default_host(shared):
        return shared.get("host", "localhost")
""")

_HELPER_COLLISION = textwrap.dedent("""\
    def default_host(shared):
        return "WRONG"
""")


def _make_multifile_pkg(base: Path, pkg_name: str, main_src: str, helper_src: str) -> Path:
    """Create a multi-file package folder under *base* and return the folder path."""
    pkg_dir = base / pkg_name
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / f"{pkg_name}.py").write_text(main_src, encoding="utf-8")
    (pkg_dir / "helpers.py").write_text(helper_src, encoding="utf-8")
    return pkg_dir


def test_load_multifile_package(tmp_path):
    """Multi-file package loads and relative import resolves correctly."""
    pkg_dir = _make_multifile_pkg(tmp_path, "multi_ping", _MULTIFILE_MAIN, _MULTIFILE_HELPER)
    defn = load_node_package(pkg_dir / "multi_ping.py", package_dir=pkg_dir)

    assert defn.display_name == "Multi Ping"
    assert defn.category == "Networking"
    assert defn.node_type_id == "multi_ping_node"

    meta = _PACKAGE_META["multi_ping_node"]
    assert meta["is_multifile"] is True
    assert meta["source_dir"] == str(pkg_dir)


def test_discover_multifile_in_user_dir(tmp_path):
    """_scan_directory picks up a multi-file package folder."""
    _make_multifile_pkg(tmp_path, "multi_ping2", _MULTIFILE_MAIN.replace("Multi Ping", "Multi Ping2"), _MULTIFILE_HELPER)
    defns, errors = discover_user_nodes(tmp_path)
    assert errors == []
    assert any(d.display_name == "Multi Ping2" for d in defns)


def test_discover_folder_missing_entrypoint(tmp_path):
    """A folder without {name}/{name}.py is reported as an error."""
    bad = tmp_path / "bad_plugin"
    bad.mkdir()
    (bad / "not_matching.py").write_text("", encoding="utf-8")
    _, errors = discover_user_nodes(tmp_path)
    assert len(errors) == 1
    assert errors[0][0] == "bad_plugin/"
    assert "bad_plugin.py" in errors[0][1]


def test_multifile_no_cross_contamination(tmp_path):
    """Two multi-file plugins with same-named helpers don't bleed into each other."""
    # plugin_a has helpers.default_host → "localhost"
    dir_a = _make_multifile_pkg(tmp_path, "plugin_a", _MULTIFILE_MAIN.replace("Multi Ping", "Plugin A").replace("MultiPingNode", "PluginANode"), _MULTIFILE_HELPER)
    # plugin_b has helpers.default_host → "WRONG" — must not leak into plugin_a
    dir_b = _make_multifile_pkg(tmp_path, "plugin_b", _MULTIFILE_MAIN.replace("Multi Ping", "Plugin B").replace("MultiPingNode", "PluginBNode"), _HELPER_COLLISION)

    defn_a = load_node_package(dir_a / "plugin_a.py", package_dir=dir_a)
    defn_b = load_node_package(dir_b / "plugin_b.py", package_dir=dir_b)

    assert defn_a.display_name == "Plugin A"
    assert defn_b.display_name == "Plugin B"
    # The modules used different specs so they cannot share cached helpers.
    # Verify by inspecting that both loaded without error — the real runtime
    # check is that plugin_a's helpers.default_host still returns "localhost".
    import sys
    mod_a = sys.modules.get("_pfc_addon_dir_plugin_a")
    mod_b = sys.modules.get("_pfc_addon_dir_plugin_b")
    assert mod_a is not None
    assert mod_b is not None
    # Each module's helpers are separate objects
    assert mod_a.helpers is not mod_b.helpers  # type: ignore[attr-defined]


# ── install_node_package (directory) ──────────────────────────────────────────

def test_install_node_package_directory(tmp_path, monkeypatch):
    """install_node_package copies a multi-file folder to the user nodes dir."""
    from pocketflow_creator import node_package_loader as npl

    user_dir = tmp_path / "user_nodes"
    user_dir.mkdir()
    monkeypatch.setattr(npl, "_USER_NODES_DIR", user_dir)

    src_pkg = _make_multifile_pkg(tmp_path / "src", "my_plugin", _MULTIFILE_MAIN.replace("Multi Ping", "My Plugin").replace("MultiPingNode", "MyPluginNode"), _MULTIFILE_HELPER)
    dest = install_node_package(src_pkg)
    assert dest == user_dir / "my_plugin"
    assert (dest / "my_plugin.py").exists()
    assert (dest / "helpers.py").exists()


def test_install_node_package_directory_overwrite(tmp_path, monkeypatch):
    """install_node_package with overwrite=True replaces an existing folder."""
    from pocketflow_creator import node_package_loader as npl

    user_dir = tmp_path / "user_nodes"
    user_dir.mkdir()
    monkeypatch.setattr(npl, "_USER_NODES_DIR", user_dir)

    src_pkg = _make_multifile_pkg(tmp_path / "src", "ow_plugin", _MULTIFILE_MAIN.replace("Multi Ping", "Overwrite Plugin").replace("MultiPingNode", "OverwritePluginNode"), _MULTIFILE_HELPER)
    install_node_package(src_pkg)
    # Second install without overwrite → FileExistsError
    with pytest.raises(FileExistsError):
        install_node_package(src_pkg)
    # With overwrite → succeeds
    dest = install_node_package(src_pkg, overwrite=True)
    assert (dest / "ow_plugin.py").exists()


def test_install_node_package_directory_invalid(tmp_path, monkeypatch):
    """install_node_package rejects a folder missing the required entry point."""
    from pocketflow_creator import node_package_loader as npl

    user_dir = tmp_path / "user_nodes"
    user_dir.mkdir()
    monkeypatch.setattr(npl, "_USER_NODES_DIR", user_dir)

    bad = tmp_path / "bad_plugin"
    bad.mkdir()
    (bad / "not_matching.py").write_text("", encoding="utf-8")

    with pytest.raises(PackageLoadError, match="bad_plugin.py"):
        install_node_package(bad)
