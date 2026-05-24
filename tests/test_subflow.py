from pocketflow_creator.model.graph_model import EdgeModel, GraphModel, NodeModel
from pocketflow_creator.runtime.providers import MockProvider
from pocketflow_creator.runtime.runner import FlowRunner
from pocketflow_creator.validation.graph_validator import GraphValidator


def _subflow_graph(*, ref: str = "") -> GraphModel:
    props = {"subflow_ref": ref} if ref else {}
    return GraphModel(
        id="main",
        title="Main",
        start_node="s1",
        nodes=[
            NodeModel(id="s1", type_id="start_node", title="Start", actions=["default"]),
            NodeModel(
                id="sub1",
                type_id="subflow_node",
                title="Sub",
                actions=["default"],
                properties=props,
            ),
            NodeModel(id="e1", type_id="stop_node", title="Stop"),
        ],
        edges=[
            EdgeModel(id="ed1", from_node="s1", action="default", to_node="sub1"),
            EdgeModel(id="ed2", from_node="sub1", action="default", to_node="e1"),
        ],
    )


def test_subflow_node_missing_ref_raises_pfce2102():
    graph = _subflow_graph(ref="")
    issues = GraphValidator().validate(graph)
    assert any(i.code == "PFCE2102" for i in issues)


def test_subflow_node_with_known_ref_no_pfce2102():
    graph = _subflow_graph(ref="graphs/sub.pfcgraph.yaml")
    issues = GraphValidator().validate(
        graph, known_graph_paths={"graphs/sub.pfcgraph.yaml"}
    )
    assert not any(i.code == "PFCE2102" for i in issues)


def test_subflow_node_missing_from_known_paths_raises_pfce2102():
    graph = _subflow_graph(ref="graphs/missing.pfcgraph.yaml")
    issues = GraphValidator().validate(graph, known_graph_paths={"graphs/other.pfcgraph.yaml"})
    assert any(i.code == "PFCE2102" for i in issues)


def test_runner_passthrough_for_subflow_node():
    graph = _subflow_graph(ref="graphs/sub.pfcgraph.yaml")
    runner = FlowRunner()
    steps = list(runner.steps(graph, MockProvider()))
    node_ids = [s.node_id for s in steps]
    assert "sub1" in node_ids
    sub_step = next(s for s in steps if s.node_id == "sub1")
    assert sub_step.shared_after.get("sub1_subflow_ref") == "graphs/sub.pfcgraph.yaml"
