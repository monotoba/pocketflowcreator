from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, PackageLoader, StrictUndefined

from pocketflow_creator.generation.python_generator import PythonGenerator
from pocketflow_creator.generation.standalone_generator import StandaloneGenerator
from pocketflow_creator.model.graph_model import GraphModel
from pocketflow_creator.model.project import ProjectModel


@dataclass
class ExportResult:
    written: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)


def _flow_stem(rel: str) -> str:
    """Derive a safe Python identifier from a graph relative path."""
    name = Path(Path(rel).stem).stem  # strip two extensions, e.g. .pfcgraph.yaml
    return name.replace("-", "_")


class Exporter:
    """Writes a full runnable PocketFlow package under exports/<package_name>/."""

    def __init__(self) -> None:
        loader = PackageLoader("pocketflow_creator", "templates")
        self._env = Environment(
            loader=loader,
            undefined=StrictUndefined,
            keep_trailing_newline=True,
        )
        self._env.filters["repr"] = repr
        self._gen = PythonGenerator()
        self._standalone_gen = StandaloneGenerator()

    def export(self, project: ProjectModel, graphs: dict[str, GraphModel]) -> ExportResult:
        result = ExportResult()
        export_root = project.root / "exports" / project.package_name
        gen_dir = export_root / "generated"
        custom_dir = export_root / "custom"
        tests_dir = export_root / "tests"
        standalone_dir = export_root / "standalone"

        for d in (export_root, gen_dir, custom_dir, tests_dir, standalone_dir):
            d.mkdir(parents=True, exist_ok=True)

        stems: list[str] = []
        for rel, graph in graphs.items():
            stem = _flow_stem(rel)
            stems.append(stem)

            # generated/ — always overwrite
            self._write(gen_dir / f"{stem}_nodes.py", self._gen.generate_nodes_py(graph), result)
            self._write(gen_dir / f"{stem}_flow.py", self._gen.generate_flow_py(graph), result)

            # custom/ and tests/ — skip if already exist (user code)
            self._write_if_new(
                custom_dir / f"{stem}_custom.py",
                self._render("custom_stub.py.j2", stem=stem),
                result,
            )
            self._write_if_new(
                tests_dir / f"test_{stem}.py",
                self._render("test_flow.py.j2", stem=stem),
                result,
            )

            # standalone/ — always overwrite (self-contained script)
            standalone_script = self._standalone_gen.generate(
                graph=graph,
                project_providers=project.providers,
                project_name=project.name,
                project_root=project.root,
            )
            self._write(
                standalone_dir / f"{stem}_standalone.py",
                standalone_script,
                result,
            )

        for d in (gen_dir, custom_dir, tests_dir, standalone_dir):
            self._write_if_new(d / "__init__.py", "", result)

        self._write_if_new(
            export_root / "main.py",
            self._render("main.py.j2", project=project, stems=stems),
            result,
        )

        return result

    def _render(self, template_name: str, **ctx: object) -> str:
        return self._env.get_template(template_name).render(**ctx)

    def _write(self, path: Path, content: str, result: ExportResult) -> None:
        path.write_text(content, encoding="utf-8")
        result.written.append(path)

    def _write_if_new(self, path: Path, content: str, result: ExportResult) -> None:
        if path.exists():
            result.skipped.append(path)
        else:
            path.write_text(content, encoding="utf-8")
            result.written.append(path)
