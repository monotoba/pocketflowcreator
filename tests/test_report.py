from __future__ import annotations

from pocketflow_creator.generation.report import generate_project_report
from pocketflow_creator.model.graph_model import EdgeModel, GraphModel, NodeModel
from pocketflow_creator.model.project import ProjectModel


def _graph() -> GraphModel:
    nodes = [
        NodeModel(id="node_start", type_id="basic", title="Start"),
        NodeModel(id="node_stop", type_id="basic", title="Stop"),
    ]
    edges = [EdgeModel(id="e1", from_node="node_start", to_node="node_stop", action="default")]
    return GraphModel(id="g1", title="Main Flow", nodes=nodes, edges=edges, start_node="node_start")


def _project() -> ProjectModel:
    from pathlib import Path

    return ProjectModel(name="Demo", package_name="demo", root=Path("/tmp/demo"))


def test_report_contains_project_name() -> None:
    report = generate_project_report(_project(), {"graphs/main.pfcgraph.yaml": _graph()})
    assert "# Demo" in report


def test_report_lists_node_count() -> None:
    report = generate_project_report(_project(), {"graphs/main.pfcgraph.yaml": _graph()})
    assert "**Nodes:** 2" in report


def test_report_lists_edge_count() -> None:
    report = generate_project_report(_project(), {"graphs/main.pfcgraph.yaml": _graph()})
    assert "**Edges:** 1" in report


def test_report_shows_validation_ok() -> None:
    report = generate_project_report(_project(), {"graphs/main.pfcgraph.yaml": _graph()})
    assert "**Validation:** OK" in report


def test_report_empty_graphs() -> None:
    report = generate_project_report(_project(), {})
    assert "# Demo" in report
    assert "## Graph:" not in report
