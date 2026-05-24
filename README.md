# PocketFlow Creator

PocketFlow Creator is an exploratory design and starter implementation for a Delphi/VB-style RAD visual designer for building PocketFlow-based LLM workflows and agentic applications.

The intended workflow is:

```text
Select node type -> Place node -> Edit properties -> Wire action ports -> Validate -> Run/debug -> Export
```

This archive contains:

- A PySide6 application scaffold.
- A property-first graph and node model.
- A starter graph validator.
- A starter Python code generator.
- Example project files.
- Markdown, YAML, and Python editor design notes.
- Setup, run, test, lint, and format scripts for Linux/macOS and Windows.
- Documentation covering requirements, architecture, GUI wireframes, custom node types, generated project format, testing strategy, and implementation phases.

## Status

This package is an **exploratory project scaffold**, not yet a locked implementation specification. It is structured so it can be converted into a design-locked specification later.

## Quick start on Linux/macOS

```bash
cd PocketFlowCreator
./scripts/setup-prj.sh
./scripts/test.sh
./scripts/run_app.sh
```

## Quick start on Windows PowerShell

```powershell
cd PocketFlowCreator
.\scripts\setup-prj.ps1
.\scripts\test.ps1
.\scripts\run_app.ps1
```

## Development notes

The starter GUI runs without needing Ollama or PocketFlow installed for tests. Runtime LLM and PocketFlow integration are intentionally represented by adapters and stubs so the design can evolve safely.

Recommended first Git commit after unpacking:

```bash
git init
git add .
git commit -m "Initial PocketFlow Creator exploratory scaffold"
```

## Project layout

```text
PocketFlowCreator/
├─ docs/
├─ examples/
├─ scripts/
├─ src/pocketflow_creator/
├─ tests/
├─ pyproject.toml
└─ README.md
```
