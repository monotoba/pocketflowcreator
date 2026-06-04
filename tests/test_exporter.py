from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from pocketflow_creator.generation.exporter import Exporter, _flow_stem
from pocketflow_creator.model.graph_model import EdgeModel, GraphModel, NodeModel
from pocketflow_creator.model.project import ProjectModel


def _simple_graph() -> GraphModel:
    nodes = [
        NodeModel(id="node_start", type_id="basic", title="Start"),
        NodeModel(id="node_stop", type_id="basic", title="Stop"),
    ]
    edges = [EdgeModel(id="e1", from_node="node_start", to_node="node_stop", action="default")]
    return GraphModel(id="g1", title="Test Graph", nodes=nodes, edges=edges, start_node="node_start")


def _project(root: Path) -> ProjectModel:
    return ProjectModel(name="TestProject", package_name="test_project", root=root)


def test_flow_stem_strips_double_extension() -> None:
    assert _flow_stem("graphs/main.pfcgraph.yaml") == "main"


def test_flow_stem_replaces_hyphens() -> None:
    assert _flow_stem("graphs/my-flow.pfcgraph.yaml") == "my_flow"


def test_export_creates_expected_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "proj"
        root.mkdir()
        project = _project(root)
        graph = _simple_graph()
        result = Exporter().export(project, {"graphs/main.pfcgraph.yaml": graph})

        export_root = root / "exports" / "test_project"
        assert (export_root / "generated" / "main_nodes.py").exists()
        assert (export_root / "generated" / "main_flow.py").exists()
        assert (export_root / "custom" / "main_custom.py").exists()
        assert (export_root / "tests" / "test_main.py").exists()
        assert (export_root / "main.py").exists()
        assert len(result.written) > 0
        assert len(result.skipped) == 0


def test_export_generated_content() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "proj"
        root.mkdir()
        project = _project(root)
        graph = _simple_graph()
        Exporter().export(project, {"graphs/main.pfcgraph.yaml": graph})

        export_root = root / "exports" / "test_project"
        nodes_py = (export_root / "generated" / "main_nodes.py").read_text()
        flow_py = (export_root / "generated" / "main_flow.py").read_text()
        assert "class NodeStartNode" in nodes_py
        assert "def build_flow" in flow_py
        assert "node_start >> node_stop" in flow_py


def test_export_custom_guard_skips_on_reexport() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "proj"
        root.mkdir()
        project = _project(root)
        graph = _simple_graph()
        exporter = Exporter()
        exporter.export(project, {"graphs/main.pfcgraph.yaml": graph})

        # Modify custom file and re-export
        custom_path = root / "exports" / "test_project" / "custom" / "main_custom.py"
        custom_path.write_text("# user wrote this\n", encoding="utf-8")
        result2 = exporter.export(project, {"graphs/main.pfcgraph.yaml": graph})

        assert custom_path.read_text() == "# user wrote this\n"
        assert custom_path in result2.skipped


def test_export_generated_always_overwritten() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "proj"
        root.mkdir()
        project = _project(root)
        graph = _simple_graph()
        exporter = Exporter()
        exporter.export(project, {"graphs/main.pfcgraph.yaml": graph})

        nodes_path = root / "exports" / "test_project" / "generated" / "main_nodes.py"
        nodes_path.write_text("# old content\n", encoding="utf-8")
        result2 = exporter.export(project, {"graphs/main.pfcgraph.yaml": graph})

        assert "# old content" not in nodes_path.read_text()
        assert nodes_path in result2.written


def test_export_result_skipped_reported() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "proj"
        root.mkdir()
        project = _project(root)
        graph = _simple_graph()
        exporter = Exporter()
        exporter.export(project, {"graphs/main.pfcgraph.yaml": graph})
        result2 = exporter.export(project, {"graphs/main.pfcgraph.yaml": graph})

        skipped_names = {p.name for p in result2.skipped}
        assert "main_custom.py" in skipped_names
        assert "test_main.py" in skipped_names
        assert "main.py" in skipped_names


def test_export_standalone_archive_creates_zip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "proj"
        root.mkdir()
        project = _project(root)
        graph = _simple_graph()
        archive_path = Exporter().export_standalone_archive(project, {"graphs/main.pfcgraph.yaml": graph})

        assert archive_path.exists()
        assert archive_path.suffix == ".zip"
        assert archive_path.name == "test_project_standalone.zip"

        with zipfile.ZipFile(archive_path) as zf:
            names = zf.namelist()
            assert any("main.py" in n for n in names)
            assert any("requirements.txt" in n for n in names)
            assert any("setup.sh" in n for n in names)
            assert any("run.sh" in n for n in names)
            assert any("README.md" in n for n in names)


def test_export_standalone_archive_contains_scripts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "proj"
        root.mkdir()
        project = _project(root)
        graph = _simple_graph()
        archive_path = Exporter().export_standalone_archive(project, {"graphs/main.pfcgraph.yaml": graph})

        with zipfile.ZipFile(archive_path) as zf:
            setup_sh = next((c for c in zf.namelist() if c.endswith("setup.sh")), None)
            run_sh = next((c for c in zf.namelist() if c.endswith("run.sh")), None)
            assert setup_sh is not None
            assert run_sh is not None

            setup_content = zf.read(setup_sh).decode("utf-8")
            run_content = zf.read(run_sh).decode("utf-8")
            assert "python -m venv" in setup_content or ".venv" in setup_content
            assert "python" in run_content


def test_export_standalone_archive_multiple_graphs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "proj"
        root.mkdir()
        project = _project(root)
        graph1 = _simple_graph()
        graph2 = _simple_graph()
        graphs = {
            "graphs/flow1.pfcgraph.yaml": graph1,
            "graphs/flow2.pfcgraph.yaml": graph2,
        }
        archive_path = Exporter().export_standalone_archive(project, graphs)

        with zipfile.ZipFile(archive_path) as zf:
            names = zf.namelist()
            script_names = [n for n in names if n.endswith(".py")]
            assert len([n for n in script_names if "flow1" in n]) > 0
            assert len([n for n in script_names if "flow2" in n]) > 0
