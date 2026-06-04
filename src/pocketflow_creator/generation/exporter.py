from __future__ import annotations

import shutil
import zipfile
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

    def export_standalone_archive(self, project: ProjectModel, graphs: dict[str, GraphModel], output_dir: Path | None = None) -> Path:
        """Export standalone scripts as a complete archive with requirements, setup, and run scripts.

        Args:
            project: PocketFlow project
            graphs: Dict of graph files to export
            output_dir: Directory to save the archive (defaults to project root)

        Returns:
            Path to created archive file
        """
        if output_dir is None:
            output_dir = project.root

        output_dir.mkdir(parents=True, exist_ok=True)

        # Create temporary archive directory
        archive_name = f"{project.package_name}_standalone"
        temp_root = output_dir / archive_name
        temp_root.mkdir(parents=True, exist_ok=True)

        # Collect all dependencies across all graphs
        all_dependencies: dict[str, str] = {}
        standalone_scripts: dict[str, tuple[str, dict[str, str]]] = {}

        for rel, graph in graphs.items():
            stem = _flow_stem(rel)
            # Generate standalone script
            script = self._standalone_gen.generate(
                graph=graph,
                project_providers=project.providers,
                project_name=project.name,
                project_root=project.root,
            )
            # Collect dependencies
            deps = self._standalone_gen.collect_dependencies(graph)
            standalone_scripts[stem] = (script, deps)
            all_dependencies.update(deps)

        # Write scripts
        scripts_dir = temp_root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        for stem, (script, _) in standalone_scripts.items():
            script_path = scripts_dir / f"{stem}.py"
            script_path.write_text(script, encoding="utf-8")

        # Write requirements.txt
        requirements_path = temp_root / "requirements.txt"
        requirements_content = "\n".join(sorted(all_dependencies.values()))
        if requirements_content:
            requirements_path.write_text(requirements_content + "\n", encoding="utf-8")
        else:
            requirements_path.write_text("# No external dependencies\n", encoding="utf-8")

        # Write setup script
        setup_script = self._render_setup_script(archive_name)
        setup_path = temp_root / "setup.sh"
        setup_path.write_text(setup_script, encoding="utf-8")
        setup_path.chmod(0o755)

        # Write run script
        if len(standalone_scripts) == 1:
            stem = list(standalone_scripts.keys())[0]
            run_script = self._render_run_script(stem)
        else:
            run_script = self._render_run_script_multi(list(standalone_scripts.keys()))
        run_path = temp_root / "run.sh"
        run_path.write_text(run_script, encoding="utf-8")
        run_path.chmod(0o755)

        # Write setup.bat and run.bat for Windows
        setup_bat = self._render_setup_script_windows(archive_name)
        setup_bat_path = temp_root / "setup.bat"
        setup_bat_path.write_text(setup_bat, encoding="utf-8")

        run_bat = self._render_run_script_windows(list(standalone_scripts.keys())[0] if len(standalone_scripts) == 1 else None)
        run_bat_path = temp_root / "run.bat"
        run_bat_path.write_text(run_bat, encoding="utf-8")

        # Write README
        readme = self._render_standalone_readme(project, list(standalone_scripts.keys()), all_dependencies)
        readme_path = temp_root / "README.md"
        readme_path.write_text(readme, encoding="utf-8")

        # Create ZIP archive
        archive_path = output_dir / f"{archive_name}.zip"
        shutil.rmtree(archive_path, ignore_errors=True)

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in temp_root.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_dir)
                    zf.write(file_path, arcname)

        # Clean up temp directory
        shutil.rmtree(temp_root)

        return archive_path

    def _render_setup_script(self, archive_name: str) -> str:
        """Render bash setup.sh script."""
        return f"""\
#!/bin/bash
set -e

echo "Setting up {archive_name}..."

# Detect Python
PYTHON=$(command -v python3 || command -v python || echo "python3")

if ! command -v "$PYTHON" &> /dev/null; then
    echo "Error: Python not found. Please install Python 3.10+"
    exit 1
fi

echo "Using Python: $($PYTHON --version)"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate 2>/dev/null || true

# Upgrade pip
echo "Upgrading pip..."
$PYTHON -m pip install --quiet --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
else
    echo "No dependencies required"
fi

echo "✓ Setup complete!"
echo ""
echo "To run the scripts:"
echo "  ./run.sh           (on Linux/Mac)"
echo "  run.bat            (on Windows)"
"""

    def _render_setup_script_windows(self, archive_name: str) -> str:
        """Render batch setup.bat script for Windows."""
        return f"""\
@echo off
echo Setting up {archive_name}...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.10+
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Using Python: %PYTHON_VERSION%

REM Create virtual environment
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\\Scripts\\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --quiet --upgrade pip

REM Install dependencies
if exist "requirements.txt" (
    echo Installing dependencies...
    pip install -q -r requirements.txt
) else (
    echo No dependencies required
)

echo.
echo [OK] Setup complete!
echo.
echo To run the scripts:
echo   run.bat
"""

    def _render_run_script(self, stem: str) -> str:
        """Render bash run.sh script for single graph."""
        return f"""\
#!/bin/bash
set -e

# Activate virtual environment
source .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate 2>/dev/null || true

echo "Running {stem}..."
python scripts/{stem}.py "$@"
"""

    def _render_run_script_multi(self, stems: list[str]) -> str:
        """Render bash run.sh script for multiple graphs."""
        scripts_list = "\n  ".join(stems)
        return f"""\
#!/bin/bash
set -e

# Activate virtual environment
source .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate 2>/dev/null || true

if [ $# -eq 0 ]; then
    echo "Usage: ./run.sh <script>"
    echo ""
    echo "Available scripts:"
    echo "  {scripts_list}"
    exit 1
fi

SCRIPT=$1
shift

if [ ! -f "scripts/${{SCRIPT}}.py" ]; then
    echo "Error: Script ${{SCRIPT}} not found"
    exit 1
fi

echo "Running ${{SCRIPT}}..."
python "scripts/${{SCRIPT}}.py" "$@"
"""

    def _render_run_script_windows(self, stem: str | None = None) -> str:
        """Render batch run.bat script for Windows."""
        if stem:
            return f"""\
@echo off
setlocal enabledelayedexpansion

REM Activate virtual environment
call .venv\\Scripts\\activate.bat

echo Running {stem}...
python scripts\\{stem}.py %*
"""
        else:
            return """\
@echo off
setlocal enabledelayedexpansion

REM Activate virtual environment
call .venv\\Scripts\\activate.bat

if "%1"=="" (
    echo Usage: run.bat ^<script^>
    echo.
    echo Available scripts:
    for %%f in (scripts\\*.py) do (
        for %%B in (%%f) do echo   %%~nB
    )
    exit /b 1
)

set SCRIPT=%1
shift

if not exist "scripts\\%SCRIPT%.py" (
    echo Error: Script %SCRIPT% not found
    exit /b 1
)

echo Running %SCRIPT%...
python "scripts\\%SCRIPT%.py" %*
"""

    def _render_standalone_readme(self, project: ProjectModel, stems: list[str], dependencies: dict[str, str]) -> str:
        """Render README.md for standalone archive."""
        scripts_section = ""
        if len(stems) == 1:
            scripts_section = """
## Running

```bash
./run.sh           # Linux/Mac
run.bat            # Windows
```
"""
        else:
            scripts_list = "\n".join(f"- `{stem}`" for stem in sorted(stems))
            scripts_section = f"""
## Running

Available scripts:
{scripts_list}

```bash
./run.sh <script>           # Linux/Mac
run.bat <script>            # Windows

# Example:
./run.sh {stems[0]}
```
"""

        deps_section = ""
        if dependencies:
            deps_section = f"""
## Dependencies

This project requires the following Python packages:

```
{chr(10).join(sorted(dependencies.values()))}
```

They will be installed automatically during setup.
"""

        return f"""# {project.name} — Standalone Scripts

Auto-generated standalone Python scripts for PocketFlow flows.

## Setup

**First time only:**

```bash
./setup.sh         # Linux/Mac
setup.bat          # Windows
```

This will:
1. Create a Python virtual environment (`.venv`)
2. Upgrade pip
3. Install all required dependencies
{deps_section}

## Scripts

Generated flows:
{chr(10).join(f"- `{stem}`" for stem in sorted(stems))}
{scripts_section}

## Input/Output

These scripts use standard I/O:
- **stdin** for interactive node input (Human Input, Human Review)
- **stdout** for output and prompts
- **stderr** for errors

You can pipe input/output:

```bash
# Pipe input
echo "input" | ./run.sh {stems[0]}

# Redirect to file
./run.sh {stems[0]} > output.json 2> errors.log

# Use in shell scripts
cat input.txt | ./run.sh {stems[0]}
```

## Environment Variables

Configure these environment variables before running:

```bash
# For LLM providers
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
export DEEPSEEK_API_KEY="sk-..."

# For API integrations
export SEARCH_API_KEY="..."
export SLACK_WEBHOOK="https://hooks.slack.com/..."
export EMAIL_ADDRESS="user@example.com"
export EMAIL_PASSWORD="..."

# For other services
export MCP_SERVER_URL="http://localhost:3000"
```

## Troubleshooting

**Issue: Command not found: ./run.sh**
- Make sure you're in the correct directory
- On Windows, use `run.bat` instead

**Issue: Python not found**
- Install Python 3.10+ from python.org
- Make sure python is in your PATH

**Issue: Module not found**
- Make sure setup completed successfully
- Try running setup again: `./setup.sh` or `setup.bat`

## Generated

This package was generated by PocketFlow Creator v0.3.0

For more information, visit: https://github.com/Monotoba/PocketFlowCreator
"""

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
