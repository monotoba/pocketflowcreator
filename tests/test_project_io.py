from __future__ import annotations

from pathlib import Path

import pytest

from pocketflow_creator.graph_io import GraphLoader, GraphSaver
from pocketflow_creator.project_io import ProjectLoader, ProjectSaver

EXAMPLE_DIR = Path(__file__).parent.parent / "examples" / "document_summarizer"


def test_project_load_fields() -> None:
    project = ProjectLoader().load(EXAMPLE_DIR / "DocumentSummarizer.pfcproj.yaml")
    assert project.name == "DocumentSummarizer"
    assert project.package_name == "document_summarizer"
    # Legacy fields still populated from schema 0.1 file for migration awareness
    assert project.default_provider == "ollama_local"
    assert project.default_model == "qwen2.5-coder:14b"
    assert project.graphs == ["graphs/main.pfcgraph.yaml"]
    assert project.prompts == ["prompts/summarize.md", "prompts/revise.md"]
    assert project.node_types == ["node_types/verified_json_llm.yaml"]
    assert project.shared_store_schema == "schemas/shared_store.schema.yaml"


def test_project_round_trip(tmp_path: Path) -> None:
    original = ProjectLoader().load(EXAMPLE_DIR / "DocumentSummarizer.pfcproj.yaml")
    save_path = tmp_path / "DocumentSummarizer.pfcproj.yaml"
    ProjectSaver().save(original, save_path)
    reloaded = ProjectLoader().load(save_path)

    assert reloaded.name == original.name
    assert reloaded.package_name == original.package_name
    # After round-trip through schema 0.2, legacy fields are gone from YAML;
    # providers block is present instead.
    assert reloaded.graphs == original.graphs
    assert reloaded.prompts == original.prompts
    assert reloaded.node_types == original.node_types
    assert reloaded.shared_store_schema == original.shared_store_schema
    assert isinstance(reloaded.providers.profiles, list)


def test_graph_load_fields() -> None:
    graph = GraphLoader().load(EXAMPLE_DIR / "graphs" / "main.pfcgraph.yaml")
    assert graph.id == "main"
    assert graph.title == "MainFlow"
    assert graph.flow_type == "sync"
    assert graph.start_node == "node_start"
    assert len(graph.nodes) == 6
    assert len(graph.edges) == 8

    summarize = graph.find_node("node_summarize")
    assert summarize is not None
    assert summarize.type_id == "llm_prompt_node"
    assert summarize.position == {"x": 520.0, "y": 80.0}
    assert summarize.properties["temperature"] == 0.2
    assert "document.text" in summarize.reads
    assert "document.summary" in summarize.writes


def test_graph_round_trip(tmp_path: Path) -> None:
    original = GraphLoader().load(EXAMPLE_DIR / "graphs" / "main.pfcgraph.yaml")
    out_path = tmp_path / "main.pfcgraph.yaml"
    GraphSaver().save(original, out_path)
    reloaded = GraphLoader().load(out_path)

    assert reloaded.id == original.id
    assert reloaded.title == original.title
    assert reloaded.flow_type == original.flow_type
    assert reloaded.start_node == original.start_node
    assert len(reloaded.nodes) == len(original.nodes)
    assert len(reloaded.edges) == len(original.edges)

    for orig_node, rl_node in zip(original.nodes, reloaded.nodes, strict=True):
        assert rl_node.id == orig_node.id
        assert rl_node.type_id == orig_node.type_id
        assert rl_node.position == orig_node.position
        assert rl_node.properties == orig_node.properties
        assert rl_node.actions == orig_node.actions
        assert rl_node.reads == orig_node.reads
        assert rl_node.writes == orig_node.writes

    for orig_edge, rl_edge in zip(original.edges, reloaded.edges, strict=True):
        assert rl_edge.id == orig_edge.id
        assert rl_edge.from_node == orig_edge.from_node
        assert rl_edge.action == orig_edge.action
        assert rl_edge.to_node == orig_edge.to_node


def test_graph_bad_version(tmp_path: Path) -> None:
    bad = tmp_path / "bad.pfcgraph.yaml"
    bad.write_text("schema_version: 99.0\nid: x\ntitle: x\n")
    with pytest.raises(ValueError, match="schema version"):
        GraphLoader().load(bad)


def test_project_bad_version(tmp_path: Path) -> None:
    bad = tmp_path / "bad.pfcproj.yaml"
    bad.write_text("schema_version: 99.0\nname: x\npackage_name: x\n")
    with pytest.raises(ValueError, match="schema version"):
        ProjectLoader().load(bad)
