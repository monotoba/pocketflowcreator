# PocketFlow Creator — Status

## Current State: M6 Complete (v0.1.0, 2026-05-24)

Milestones M0–M6 are done. The app has a working graph canvas, full file I/O, wired menus,
syntax-highlighting editors, live Markdown preview, shared-store tooling, Jinja2 template-based
code generation, full export pipeline with `custom/` guard, graph image export (SVG/PNG), and
project report export (Markdown). M7 (Run and Debug) is next.

---

## Completed Milestones

### M0 — Initial Scaffold ✓
Project structure, models, validator, generator, GUI shell, docs, scripts, and initial test
suite committed.

### M1 — Clean Baseline ✓
Zero ruff errors, zero mypy errors. Quality floor locked.

### M2 — Project File I/O ✓
- `ProjectLoader` / `ProjectSaver` — YAML round-trip for `.pfcproj.yaml`
- `GraphLoader` / `GraphSaver` — YAML round-trip for `.pfcgraph.yaml`
- Round-trip test for load → save → reload equality

### M3 — GUI Shell Wired ✓
- File > New/Open/Save/Save All/Project Settings all dispatch to real handlers
- Recent-projects list persisted in `QSettings`
- Project Explorer populates from loaded project tree
- Project > Validate / Generate Code / Open Folder wired
- Help > About dialog
- `QUndoStack` wired to Edit > Undo/Redo

### M4 — Real Graph Canvas ✓
- `QGraphicsScene` canvas with `NodeItem` (rounded rect, title/badge, port ellipses)
- `EdgeItem` (straight line from action port to input port)
- Drag-drop from Component Palette creates nodes on canvas
- Selection → Object Inspector property grid (ID, Type, Title editable, Position, etc.)
- Inspector edits sync back to `NodeModel` live
- Validation error badges (`_has_error` flag, red border) via `apply_validation()`
- Ctrl+Scroll zoom, middle-drag pan, View > Zoom to Fit

### M5 — Editors ✓
- `PythonHighlighter` / `YamlHighlighter` (`QSyntaxHighlighter` subclasses) in `editors.py`
- Markdown tab: `QSplitter` with editor + live `QTextBrowser` preview (uses `markdown` package)
- YAML tab: validates on every keystroke, shows parse error in status bar
- Project Explorer double-click → opens `.py`/`.md`/`.yaml` into correct bottom tab
- `_bottom_tab_paths` tracks open files; Save/Save All writes back to disk
- Tools > Provider Manager → dialog persisting Ollama + Mock settings in `QSettings`
- Tools > Tool Registry → stub dialog
- Tools > Shared Store Inspector → switches to Shared Store tab
- Shared Store Designer: double-click "Shared Store" in explorer → `QTableWidget` dialog
  with Namespace/Key/Type/Default columns; edits serialize back to nested YAML

### M6 — Code Generation and Export ✓
- `PythonGenerator` replaced with Jinja2 template-based generator (`nodes.py.j2`, `flow.py.j2`)
- `Exporter` writes `exports/<pkg>/` with `generated/`, `custom/`, `tests/`, `main.py`
- `custom/` guard: skip existing files on re-export, report written vs skipped counts
- File > Export PocketFlow Project wired — completion dialog shows written/skipped summary
- Project > Export Graph Image → save-file dialog → renders scene to PNG or SVG
- Project > Export Project Report → Markdown with node/edge tables and validation status

---

## What Is Implemented

### Core Data Model (`src/pocketflow_creator/model/`)
- `GraphModel`, `NodeModel`, `EdgeModel`, `NodeTypeDefinition`, `ProjectModel`
- All use `@dataclass(slots=True)`; `ProjectModel` includes `prompts`, `node_types`,
  `shared_store_schema` fields

### File I/O (`src/pocketflow_creator/graph_io.py`, `project_io.py`)
- `GraphLoader`, `GraphSaver` — YAML ↔ `GraphModel`
- `ProjectLoader`, `ProjectSaver` — YAML ↔ `ProjectModel`

### Validation (`src/pocketflow_creator/validation/`)
- `GraphValidator` — unique IDs, start node, edge endpoints, declared actions
- Error codes PFCE1001–PFCE1003, PFCE2001–PFCE2003, PFCE2101

### Code Generation (`src/pocketflow_creator/generation/`)
- `PythonGenerator` — Jinja2 template-based; generates `nodes.py` and `flow.py` per graph
- PocketFlow `>>` and `- "action" >>` syntax in `flow.py.j2`
- `Exporter` — writes full package to `exports/<pkg>/`; `custom/` guard prevents overwrites
- `generate_project_report()` — Markdown summary of nodes, edges, validation status

### Runtime (`src/pocketflow_creator/runtime/`)
- `LLMProvider` protocol, `MockProvider`, `OllamaProvider` stub (raises `NotImplementedError`)

### GUI (`src/pocketflow_creator/app/`)
- `main.py`: `MainWindow` — complete working GUI, all M3–M6 features wired
- `canvas.py`: `NodeItem`, `EdgeItem`, `GraphScene`, `GraphView`, `PaletteWidget`
- `editors.py`: `PythonHighlighter`, `YamlHighlighter`

### Example Project (`examples/document_summarizer/`)
- `.pfcproj.yaml`, graphs, node types, prompts, schemas directories

### Documentation (`docs/`)
- 13 design/spec docs (00–12) including architecture, requirements, GUI wireframes,
  node type model, project format, code generation, testing strategy, security model,
  implementation plan, user guide, developer guide, AI agent instructions
- `diagrams/application_architecture.svg`

---

## Test Status

| Suite | Tests | Status |
|---|---|---|
| `test_graph_validator.py` | 3 | Passing |
| `test_node_type.py` | 2 | Passing |
| `test_project_archive_files.py` | 1 | Passing |
| `test_project_io.py` | 5 | Passing |
| `test_python_generator.py` | 1 | Passing |
| `test_canvas.py` | 8 | Passing |
| `test_editors.py` | 5 | Passing |
| `test_shared_store_designer.py` | 6 | Passing |
| `test_exporter.py` | 7 | Passing |
| `test_report.py` | 5 | Passing |
| **Total** | **44** | **All green** |

---

## Lint / Type Check Status

- **ruff**: 0 errors across all source and test files
- **mypy**: 0 errors (`ignore_missing_imports = true`; Pyright "possibly unbound" warnings
  are false positives from the try/except Qt fallback pattern — not real errors)

---

## What Is Not Yet Implemented

### M7 — Run and Debug (next)
- `OllamaProvider.complete()` HTTP POST to Ollama `/api/generate`
- Run Active Flow with `MockProvider` → Run Log tab
- Shared Store tab live population per node step
- Prompt Preview tab for selected LLM node
- Step debugger with breakpoint markers
- Run trace export to JSON

### M8 — Custom Node Type System
- Node type wizard dialog
- Custom type YAML validation against schema
- Inheritance support in inspector
- Custom node library manager

### M9 — Test Coverage and Polish
- GUI smoke-test infrastructure (already partially done via offscreen tests)
- ProjectLoader round-trip test
- Code generation completeness test
- OllamaProvider mock HTTP test
- 50+ tests total

---

## Dependencies

| Package | Version constraint | Purpose |
|---|---|---|
| PySide6 | >=6.6 | GUI framework |
| PyYAML | >=6.0 | Project YAML files |
| jsonschema | >=4.20 | Metadata and schema validation |
| markdown | >=3.5 | Markdown → HTML for live preview |
| jinja2 | >=3.1 | Code generation templates |
| pytest | >=8.0 (dev) | Test runner |
| ruff | >=0.5 (dev) | Linter and formatter |
| mypy | >=1.8 (dev) | Type checker |
