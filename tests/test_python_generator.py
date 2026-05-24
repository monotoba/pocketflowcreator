from pocketflow_creator.generation.python_generator import PythonGenerator
from pocketflow_creator.model.graph_model import EdgeModel, GraphModel, NodeModel


def test_generator_emits_node_and_flow_code():
    graph = GraphModel(
        id="main",
        title="MainFlow",
        start_node="node_start",
        nodes=[
            NodeModel(id="node_start", type_id="start_node", title="Start", actions=["default"]),
            NodeModel(id="node_stop", type_id="stop_node", title="Stop"),
        ],
        edges=[EdgeModel(id="edge1", from_node="node_start", action="default", to_node="node_stop")],
    )

    generator = PythonGenerator()
    nodes_py = generator.generate_nodes_py(graph)
    flow_py = generator.generate_flow_py(graph)

    assert "class NodeStartNode" in nodes_py
    assert "def build_flow" in flow_py
    assert "node_start >> node_stop" in flow_py
