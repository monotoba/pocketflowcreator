import tempfile
from pathlib import Path

from pocketflow_creator.app import code_manager
from pocketflow_creator.model.graph_model import NodeModel


def _node(node_id: str = "node_abc", title: str = "My Step", type_id: str = "basic_node"):
    return NodeModel(id=node_id, type_id=type_id, title=title)


def test_ensure_code_file_creates_file():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = code_manager.ensure_code_file("graphs/main.pfcgraph.yaml", root)
        assert path.exists()
        assert path.name == "main.py"
        assert "class " not in path.read_text()


def test_add_node_creates_stub():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = code_manager.ensure_code_file("graphs/main.pfcgraph.yaml", root)
        node = _node()
        line = code_manager.add_node(path, node)
        text = path.read_text()
        assert "class MyStep" in text
        assert "# --- NODE_START: node_abc ---" in text
        assert "# --- NODE_END: node_abc ---" in text
        assert line >= 1


def test_add_node_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = code_manager.ensure_code_file("graphs/main.pfcgraph.yaml", root)
        node = _node()
        line1 = code_manager.add_node(path, node)
        line2 = code_manager.add_node(path, node)
        assert line1 == line2
        assert path.read_text().count("class MyStep") == 1


def test_remove_node():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = code_manager.ensure_code_file("graphs/main.pfcgraph.yaml", root)
        node = _node()
        code_manager.add_node(path, node)
        code_manager.remove_node(path, node.id)
        text = path.read_text()
        assert "class MyStep" not in text
        assert "NODE_START: node_abc" not in text


def test_remove_node_missing_is_noop():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = code_manager.ensure_code_file("graphs/main.pfcgraph.yaml", root)
        code_manager.remove_node(path, "nonexistent_id")
        assert path.exists()


def test_find_node_line():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = code_manager.ensure_code_file("graphs/main.pfcgraph.yaml", root)
        node = _node()
        expected = code_manager.add_node(path, node)
        found = code_manager.find_node_line(path, node.id)
        assert found == expected


def test_class_name_from_title():
    assert code_manager._to_class_name("My LLM Step") == "MyLlmStep"
    assert code_manager._to_class_name("start node!") == "StartNode"
    assert code_manager._to_class_name("") == "Node"
