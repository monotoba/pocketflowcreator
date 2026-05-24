from pocketflow_creator.model.graph_model import EdgeModel, GraphModel, NodeModel
from pocketflow_creator.validation.graph_validator import GraphValidator


def test_valid_minimal_graph_has_no_errors():
    graph = GraphModel(
        id="main",
        title="MainFlow",
        start_node="start",
        nodes=[
            NodeModel(id="start", type_id="start_node", title="Start", actions=["default"]),
            NodeModel(id="stop", type_id="stop_node", title="Stop"),
        ],
        edges=[EdgeModel(id="edge1", from_node="start", action="default", to_node="stop")],
    )

    issues = GraphValidator().validate(graph)

    assert [issue for issue in issues if issue.severity == "error"] == []


def test_missing_start_node_is_error():
    graph = GraphModel(id="main", title="MainFlow")

    issues = GraphValidator().validate(graph)

    assert any(issue.code == "PFCE1001" for issue in issues)


def test_undeclared_edge_action_is_error():
    graph = GraphModel(
        id="main",
        title="MainFlow",
        start_node="a",
        nodes=[
            NodeModel(id="a", type_id="router_node", title="A", actions=["yes"]),
            NodeModel(id="b", type_id="stop_node", title="B"),
        ],
        edges=[EdgeModel(id="edge1", from_node="a", action="no", to_node="b")],
    )

    issues = GraphValidator().validate(graph)

    assert any(issue.code == "PFCE2101" for issue in issues)
