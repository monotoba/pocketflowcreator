"""Tests for the single-file node package loader."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from pocketflow_creator.node_package_loader import (
    PackageLoadError,
    _PACKAGE_META,
    _parse_docstring,
    _to_type_id,
    discover_user_nodes,
    load_node_package,
)


# ── _parse_docstring ──────────────────────────────────────────────────────────

def test_parse_docstring_basic():
    doc = textwrap.dedent("""\
        Node: Weather Fetch
        Category: Web / Search
        Version: 1.2.3
        Author: Jane Dev
        Website: https://janedev.com
        Repo: https://github.com/janedev/weather-node
        Description: Fetches current conditions.
        Tags: weather, api, http
        Min-Creator-Version: 0.2.0
        License: MIT
    """)
    meta = _parse_docstring(doc)
    assert meta["node"] == "Weather Fetch"
    assert meta["category"] == "Web / Search"
    assert meta["version"] == "1.2.3"
    assert meta["author"] == "Jane Dev"
    assert meta["website"] == "https://janedev.com"
    assert meta["repo"] == "https://github.com/janedev/weather-node"
    assert meta["description"] == "Fetches current conditions."
    assert meta["tags"] == "weather, api, http"
    assert meta["min_creator_version"] == "0.2.0"
    assert meta["license"] == "MIT"


def test_parse_docstring_ignores_prose():
    doc = textwrap.dedent("""\
        This is some prose that should be ignored.

        Node: My Node
        This line has no colon-key structure.
        Category: Custom
    """)
    meta = _parse_docstring(doc)
    assert meta["node"] == "My Node"
    assert meta["category"] == "Custom"
    assert len(meta) == 2


def test_parse_docstring_empty():
    assert _parse_docstring("") == {}
    assert _parse_docstring("   \n   ") == {}


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
    from pocketflow_creator.node_package_loader import _to_type_id
    assert _to_type_id(name) == expected


# ── load_node_package ─────────────────────────────────────────────────────────

_GOOD_PACKAGE = textwrap.dedent("""\
    \"\"\"
    Node: Ping
    Category: Networking
    Version: 0.1.0
    Author: Test Author
    Website: https://example.com
    Repo: https://github.com/example/ping-node
    Description: Sends a ping.
    Tags: net, ping
    License: MIT
    \"\"\"

    __node_actions__ = ["success", "timeout"]
    __node_properties__ = {
        "host_key": {"type": "string", "default": "host", "description": "Target host"},
    }
    __node_color__ = "#0277bd"

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
    \"\"\"
    Node: Broken
    Category: Custom
    \"\"\"

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
