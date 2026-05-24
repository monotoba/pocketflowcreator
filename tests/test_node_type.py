import pytest

from pocketflow_creator.model.node_type import NodeTypeDefinition


def test_node_type_definition_loads_from_mapping():
    node_type = NodeTypeDefinition.from_mapping(
        {
            "node_type_id": "llm_prompt_node",
            "display_name": "LLM Prompt Node",
            "category": "LLM",
            "base_class": "Node",
            "actions": ["success", "error"],
        }
    )

    assert node_type.node_type_id == "llm_prompt_node"
    assert node_type.actions == ["success", "error"]


def test_node_type_definition_requires_core_fields():
    with pytest.raises(ValueError):
        NodeTypeDefinition.from_mapping({"display_name": "Broken"})
