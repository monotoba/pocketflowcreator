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


def _inner_graph() -> GraphModel:
    """A simple two-node graph used as a subflow."""
    return GraphModel(
        id="inner",
        title="Inner",
        start_node="i1",
        nodes=[
            NodeModel(id="i1", type_id="start_node", title="Inner Start", actions=["default"]),
            NodeModel(id="i2", type_id="stop_node", title="Inner Stop"),
        ],
        edges=[
            EdgeModel(id="ie1", from_node="i1", action="default", to_node="i2"),
        ],
    )


def test_runner_executes_subflow_inline():
    """When known_graphs is provided, inner steps are yielded in place of the subflow node."""
    ref = "graphs/sub.pfcgraph.yaml"
    graph = _subflow_graph(ref=ref)
    inner = _inner_graph()
    runner = FlowRunner()
    steps = list(runner.steps(graph, MockProvider(), known_graphs={ref: inner}))
    node_ids = [s.node_id for s in steps]
    # Inner graph nodes must appear
    assert "i1" in node_ids
    # Parent graph nodes around the subflow must still appear
    assert "s1" in node_ids
    assert "e1" in node_ids


def test_runner_subflow_shared_store_propagates():
    """Subgraph can write to shared store and parent graph sees the result."""
    ref = "graphs/sub.pfcgraph.yaml"
    graph = _subflow_graph(ref=ref)
    inner = _inner_graph()
    runner = FlowRunner()
    steps = list(runner.steps(graph, MockProvider(), shared={"seed": 1}, known_graphs={ref: inner}))
    # Every step should have seen 'seed' in shared_before
    assert all(s.shared_before.get("seed") == 1 for s in steps)
    # The subflow boundary marker is written after the inner steps
    last_parent_step = next(s for s in steps if s.node_id == "e1")
    assert last_parent_step.shared_before.get("sub1_subflow_ref") == ref
