# PocketFlow Creator — Status

## Current State: Exploratory Scaffold (v0.1.0)

This is an initial exploratory scaffold. It is not yet a design-locked implementation. The
scaffold establishes the package structure, data models, validation engine, starter code
generator, GUI shell, and documentation for all seven planned phases.

---

## What Is Implemented

### Core Data Model (`src/pocketflow_creator/model/`)
- `GraphModel` — graph with nodes, edges, and start-node reference
- `NodeModel` — node instance with id, type, title, position, properties, actions, reads, writes
- `EdgeModel` — directed edge with action label
- `NodeTypeDefinition` — reusable node type metadata with inheritance-ready fields
- `ProjectModel` — project root, name, package name, default provider/model, graph list

### Validation (`src/pocketflow_creator/validation/`)
- `GraphValidator` — validates unique node IDs, start node exists, edge endpoints exist,
  and edge actions are declared by source nodes
- Error codes: PFCE1001–PFCE1003, PFCE2001–PFCE2003, PFCE2101
- `ValidationIssue` — structured result with severity, code, object ID, and message

### Code Generation (`src/pocketflow_creator/generation/`)
- `PythonGenerator` — generates `nodes.py` (one class per node) and `flow.py` (wired flow)
- Maps graph edges to PocketFlow `>>` and `- "action" >>` syntax
- Fallback imports allow generated files to be inspected without PocketFlow installed

### Runtime (`src/pocketflow_creator/runtime/`)
- `LLMProvider` — protocol interface for LLM providers
- `MockProvider` — deterministic test provider
- `OllamaProvider` — design stub; HTTP integration not yet implemented

### GUI Shell (`src/pocketflow_creator/app/`)
- `MainWindow` (PySide6) — full menu bar, central graph placeholder, four dock regions
- Docks: Project Explorer, Component Palette, Object Inspector, Output (tabbed)
- Menu structure: File, Edit, View, Project, Flow, Node, Run, Tools, Window, Help
- Component palette lists 12 built-in node types
- All menu actions and dock content are stubs (no real dispatch yet)

### Example Project (`examples/document_summarizer/`)
- Sample project YAML file with graphs, node types, prompts, and schemas directories

### Documentation (`docs/`)
- 00 Project overview, 01 Requirements, 02 GUI wireframes, 03 Architecture
- 04 Node type model, 05 Project format, 06 Code generation design
- 07 Testing strategy, 08 Security model, 09 Implementation plan
- 10 User guide, 11 Developer guide, 12 AI agent instructions
- `diagrams/application_architecture.svg`

### Scripts
- `setup-prj.sh/.ps1/.bat` — create venv and install dev dependencies
- `test.sh/.ps1/.bat` — run pytest
- `lint.sh` — run ruff check
- `format.sh` — run ruff format
- `run_app.sh/.ps1/.bat` — launch GUI

---

## Test Status

| Suite | Tests | Status |
|---|---|---|
| `test_graph_validator.py` | 3 | Passing |
| `test_node_type.py` | 2 | Passing |
| `test_project_archive_files.py` | 1 | Passing |
| `test_python_generator.py` | 1 | Passing |
| **Total** | **7** | **All green** |

---

## Lint Status

Pre-existing issues in the scaffold (not yet fixed):

| File | Issues |
|---|---|
| `src/pocketflow_creator/app/main.py` | UP035 (Sequence import), F401 (unused QWidget), E501 ×4 (long menu-spec lines) |
| `src/pocketflow_creator/generation/python_generator.py` | E501 ×1 |
| `src/pocketflow_creator/model/node_type.py` | UP037 (quoted return annotation) |
| `tests/test_python_generator.py` | E501 ×1 |

3 of 9 are auto-fixable with `ruff check --fix`.

---

## What Is Not Yet Implemented

These are intentional deferred phases (see `docs/09_implementation_plan.md`):

### Phase 2 — RAD GUI Shell (Partially Done)
- Menu actions dispatch to real handlers (all stubs currently)
- Project open/save dialogs
- Real project loading into Project Explorer

### Phase 3 — Real Graph Designer
- `QGraphicsView`/`QGraphicsScene` graph canvas
- Node items with action port handles
- Edge routing and drawing
- Drag/drop from Component Palette to canvas
- Object Inspector synchronization with selected node/edge

### Phase 4 — Editors
- Python editor with syntax highlighting
- Markdown/prompt editor
- YAML editor
- Shared-store designer
- Provider profile manager
- Tool registry

### Phase 5 — Code Generation and Export
- Full template-based code generation
- Generated test scaffolding
- Exported project YAML/Python package
- Graph image and project report export

### Phase 6 — Run and Debug
- Real Ollama HTTP integration
- Step debugger
- Shared-store diff view
- Prompt preview and response inspection
- Run trace export

### Phase 7 — Custom Node Type System
- Node type wizard
- Metadata validation for custom types
- Inheritance support
- Custom node library manager

### Project File I/O
- Full YAML project loader and saver (model → YAML → model round-trip)

---

## Dependencies

| Package | Version constraint | Purpose |
|---|---|---|
| PySide6 | >=6.6 | GUI framework |
| PyYAML | >=6.0 | Project YAML files |
| jsonschema | >=4.20 | Metadata and schema validation |
| pytest | >=8.0 (dev) | Test runner |
| ruff | >=0.5 (dev) | Linter and formatter |
| mypy | >=1.8 (dev) | Type checker |
