from __future__ import annotations

from pathlib import Path

import pytest

from pocketflow_creator.model.node_type import NodeTypeDefinition


def _valid_defn() -> dict:
    return {
        "node_type_id": "my_llm",
        "display_name": "My LLM Node",
        "category": "LLM",
        "base_class": "Node",
        "description": "A test node",
        "actions": ["success", "error"],
        "properties": {"model": {"type": "string", "default": "qwen"}},
        "allow_python_hooks": True,
        "allow_prompt_files": False,
    }


class TestNodeTypeDefinitionValidation:
    def test_valid_mapping_loads(self) -> None:
        defn = NodeTypeDefinition.from_mapping(_valid_defn())
        assert defn.node_type_id == "my_llm"
        assert defn.category == "LLM"

    def test_missing_required_field_raises(self) -> None:
        bad = _valid_defn()
        del bad["base_class"]
        with pytest.raises(ValueError, match="base_class"):
            NodeTypeDefinition.from_mapping(bad)

    def test_actions_preserved(self) -> None:
        defn = NodeTypeDefinition.from_mapping(_valid_defn())
        assert defn.actions == ["success", "error"]

    def test_properties_preserved(self) -> None:
        defn = NodeTypeDefinition.from_mapping(_valid_defn())
        assert "model" in defn.properties

    def test_flags_preserved(self) -> None:
        defn = NodeTypeDefinition.from_mapping(_valid_defn())
        assert defn.allow_python_hooks is True
        assert defn.allow_prompt_files is False


class TestNodeSkeletonGeneration:
    """Tests for the _node_skeleton_text helper used by T-606."""

    def test_skeleton_contains_class_name(self) -> None:
        from pocketflow_creator.app.main import _node_skeleton_text

        text = _node_skeleton_text("my_node", "Node")
        assert "class MyNode" in text

    def test_skeleton_contains_prep_exec_post(self) -> None:
        from pocketflow_creator.app.main import _node_skeleton_text

        text = _node_skeleton_text("my_node", "Node")
        assert "def prep" in text
        assert "def exec" in text
        assert "def post" in text

    def test_skeleton_base_class_commented(self) -> None:
        from pocketflow_creator.app.main import _node_skeleton_text

        text = _node_skeleton_text("my_node", "llm_prompt_node")
        assert "llm_prompt_node" in text

    def test_skeleton_hyphen_id_converts(self) -> None:
        from pocketflow_creator.app.main import _node_skeleton_text

        text = _node_skeleton_text("my-special-node", "Node")
        assert "class MySpecialNode" in text


class TestNodeTypeLibraryLoad:
    def test_registry_loads_from_yaml(self, tmp_path: Path) -> None:
        import yaml

        from pocketflow_creator.model.node_type import NodeTypeDefinition
        from pocketflow_creator.model.project import ProjectModel

        nt_dir = tmp_path / "node_types"
        nt_dir.mkdir()
        (nt_dir / "test_type.yaml").write_text(
            yaml.dump(_valid_defn()), encoding="utf-8"
        )
        project = ProjectModel(
            name="P", package_name="p", root=tmp_path,
            node_types=["node_types/test_type.yaml"]
        )
        # Exercise the loading logic directly
        registry: dict[str, NodeTypeDefinition] = {}
        for rel in project.node_types:
            path = project.root / rel
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            defn = NodeTypeDefinition.from_mapping(data)
            registry[defn.node_type_id] = defn
        assert "my_llm" in registry
        assert registry["my_llm"].display_name == "My LLM Node"
