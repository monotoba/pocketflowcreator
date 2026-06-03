from __future__ import annotations

import dataclasses
from pathlib import Path

from pocketflow_creator.generation.exporter import Exporter, _flow_stem
from pocketflow_creator.generation.python_generator import PythonGenerator
from pocketflow_creator.graph_io import GraphLoader
from pocketflow_creator.model.graph_model import GraphModel
from pocketflow_creator.model.project import ProjectModel
from pocketflow_creator.project_io import ProjectLoader

_EXAMPLE = Path(__file__).parent.parent / "examples" / "document_summarizer"
_PROJ_FILE = _EXAMPLE / "DocumentSummarizer.pfcproj.yaml"


def _load_example() -> tuple[ProjectModel, dict[str, GraphModel]]:
    project = ProjectLoader().load(_PROJ_FILE)
    loader = GraphLoader()
    graphs: dict[str, GraphModel] = {}
    for rel in project.graphs:
        gpath = _EXAMPLE / rel
        if gpath.exists():
            graphs[rel] = loader.load(gpath)
    return project, graphs


def test_generator_produces_nodes_py_for_example() -> None:
    _, graphs = _load_example()
    assert graphs, "no graphs loaded from document_summarizer example"
    gen = PythonGenerator()
    for rel, graph in graphs.items():
        code = gen.generate_nodes_py(graph)
        for node in graph.nodes:
            class_name = "".join(p.capitalize() for p in node.id.replace("-", "_").split("_"))
            assert f"class {class_name}" in code, f"missing class {class_name} in {rel}"


def test_generator_produces_flow_py_for_example() -> None:
    _, graphs = _load_example()
    gen = PythonGenerator()
    for rel, graph in graphs.items():
        code = gen.generate_flow_py(graph)
        assert "def build_flow" in code, f"build_flow missing in {rel}"
        assert "Flow(" in code, f"Flow( missing in {rel}"


def test_generator_flow_py_wires_edges_for_example() -> None:
    _, graphs = _load_example()
    gen = PythonGenerator()
    for rel, graph in graphs.items():
        code = gen.generate_flow_py(graph)
        for edge in graph.edges:
            if edge.action in ("default", ""):
                assert ">>" in code
            else:
                assert f'"{edge.action}"' in code or f"'{edge.action}'" in code, f"action {edge.action!r} not in generated flow.py for {rel}"


def test_exporter_writes_all_expected_files_for_example(tmp_path: Path) -> None:
    project, graphs = _load_example()
    project = dataclasses.replace(project, root=tmp_path)
    result = Exporter().export(project, graphs)
    stems = {_flow_stem(rel) for rel in graphs}
    pkg = project.package_name
    base = tmp_path / "exports" / pkg
    for stem in stems:
        assert (base / "generated" / f"{stem}_nodes.py").exists(), f"missing {stem}_nodes.py"
        assert (base / "generated" / f"{stem}_flow.py").exists(), f"missing {stem}_flow.py"
    assert (base / "main.py").exists()
    assert len(result.written) >= len(stems) * 2 + 1
