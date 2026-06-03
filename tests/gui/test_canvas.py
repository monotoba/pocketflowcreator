from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

from pocketflow_creator.app.canvas import EdgeItem, GraphScene, GraphView, NodeItem
from pocketflow_creator.graph_io import GraphLoader

pytestmark = pytest.mark.gui

_EXAMPLE = Path(__file__).parent.parent / "examples" / "document_summarizer"

_app = QApplication.instance() or QApplication([])


def _make_scene() -> GraphScene:
    graph = GraphLoader().load(_EXAMPLE / "graphs" / "main.pfcgraph.yaml")
    scene = GraphScene()
    scene.load_graph(graph)
    return scene


def test_load_graph_node_count() -> None:
    scene = _make_scene()
    node_items = [item for item in scene.items() if isinstance(item, NodeItem)]
    assert len(node_items) == 6


def test_load_graph_edge_count() -> None:
    scene = _make_scene()
    edge_items = [item for item in scene.items() if isinstance(item, EdgeItem)]
    assert len(edge_items) == 8


def test_create_node_at_increases_count() -> None:
    scene = _make_scene()
    scene.create_node_at("basic_node", QPointF(400, 200))
    node_items = [item for item in scene.items() if isinstance(item, NodeItem)]
    assert len(node_items) == 7


def test_create_node_at_model_registered() -> None:
    scene = _make_scene()
    new_item = scene.create_node_at("router_node", QPointF(100, 100))
    assert new_item.node.type_id == "router_node"
    assert new_item.node.id in {item._node.id for item in scene.items() if isinstance(item, NodeItem)}


def test_apply_validation_marks_error() -> None:
    scene = _make_scene()
    scene.apply_validation({"node_start"})
    node_map = {item._node.id: item for item in scene.items() if isinstance(item, NodeItem)}
    assert node_map["node_start"]._has_error is True
    for node_id, item in node_map.items():
        if node_id != "node_start":
            assert item._has_error is False


def test_apply_validation_clears_errors() -> None:
    scene = _make_scene()
    scene.apply_validation({"node_start"})
    scene.apply_validation(set())
    node_items = [item for item in scene.items() if isinstance(item, NodeItem)]
    assert all(not item._has_error for item in node_items)


def test_zoom_to_fit_empty() -> None:
    scene = GraphScene()
    view = GraphView(scene)
    view.zoom_to_fit()


def test_zoom_to_fit_populated() -> None:
    scene = _make_scene()
    view = GraphView(scene)
    view.zoom_to_fit()
