"""Tests for the single-file node package loader."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from pocketflow_creator.node_package_loader import (
    PackageLoadError,
    _PACKAGE_META,
    _to_type_id,
    discover_user_nodes,
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
    from pocketflow_creator.node_package_loader import _to_type_id
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
