from pathlib import Path


def test_required_docs_exist():
    root = Path(__file__).resolve().parents[1]
    required = [
        "README.md",
        "docs/00_project_overview.md",
        "docs/01_requirements.md",
        "docs/02_gui_wireframes.md",
        "docs/03_architecture.md",
        "docs/04_node_type_model.md",
        "scripts/setup-prj.sh",
        "scripts/run_app.sh",
        "scripts/test.sh",
    ]
    for rel in required:
        assert (root / rel).exists(), rel
