# PocketFlow Creator — Status

## Current State: M12 Complete — Polish and Completion (v0.1.3, 2026-05-24)

Milestones M0–M12 are done. M12 closes all known stub/gap items: code_manager base class
resolved from node type definition, GUI run handler passes known_graphs for subflow execution,
Tool Registry discovers @tool functions via AST scan, zh/ja translations compiled to .qm, and
help/img/ populated with UI screenshots linked from help pages.
M11 added the full integrated help system. M10 added comprehensive tutorials. M0–M9 delivered
the working app: graph canvas, file I/O, wired menus, editors, live preview, shared-store
tooling, code generation, full export pipeline, run/debug engine, and Custom Node Type System.

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

### M10 — Tutorials and Documentation ✓
- `docs/TUTORIALS.md` — 25 tutorials + 4 exercises (source; canonical copy now in `help/tutorials/`)
- PocketFlow repo researched: 40+ examples catalogued across beginner/intermediate/advanced

### M11 — Help System ✓
- `src/pocketflow_creator/help/` — 21 Markdown help files in 3 directories:
  - Main: `index.md`, `getting_started.md`, `your_first_flow.md`, `about_pocketflow.md`,
    `about_pocketflow_creator.md`
  - `tutorials/`: `index.md` + 4 part files (Fundamentals, Patterns, Advanced, Exercises)
  - `context/`: 11 files (canvas, inspector, palette, explorer, options, provider_manager,
    shared_store, node_type_wizard, code_editor, run_log, validation)
- `HelpBrowser` dialog — navigable QTextBrowser with Markdown→HTML, back/forward/home,
  image search paths, external URL handling
- `open_help()` convenience function for use from dialogs
- Help menu wired: `PocketFlow Creator Help` (F1) → index.md; `Quick Reference` → tutorials/index.md
- `_add_help_button()` helper method adds `?` to QDialogButtonBox with HelpRole
- `?` buttons in: Options, Provider Manager, Shared Store Designer, Node Type Wizard
- `pyproject.toml` updated: `help/**/*.md` in package-data
- 8 new tests in `tests/test_help_browser.py`

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

### M7 — Run and Debug ✓
- `OllamaProvider.complete()` — HTTP POST to `{base_url}/api/generate` using stdlib `urllib.request`
- `FlowRunner.steps()` generator — yields `RunStep` per node; non-blocking, consumer controls pacing
- `FlowRunner.run()` — convenience wrapper that collects all steps into a `RunTrace`
- `FlowRunner.run_debug()` — threaded debug runner with `StepController` pause/resume gate + breakpoints
- `StepController` — thread-safe `pause()` / `resume()` / `stop()` / `wait_for_resume()` for debug thread
- `RunTrace.to_json()` / `FlowRunner.save_trace()` — writes `run_reports/<timestamp>.json`
- Run > Run Active Flow — populates Run Log tab and Shared Store tab; saves trace file
- Run > Debug Active Flow — runs in background thread with StepController; Stop/Resume menu actions
- Run > Run Tests — `pytest` subprocess; populates Test Results tab
- T-505 Prompt Preview — auto-populates when LLM node selected; reads `prompt_file` from node properties
- T-506 Debug breakpoints — Toggle Breakpoint on canvas node; red dot marker on `NodeItem`

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
- `LLMProvider` protocol, `MockProvider`, `OllamaProvider` (HTTP POST via `urllib.request`)
- `FlowRunner` — interprets `GraphModel` directly; `RunTrace` + `RunStep` dataclasses
- `save_trace()` — writes `run_reports/<timestamp>.json`

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
| `test_ollama_provider.py` | 5 | Passing |
| `test_runner.py` | 10 | Passing |
| `test_generation_completeness.py` | 4 | Passing |
| `test_node_type_wizard.py` | 10 | Passing |
| `test_runner.py` (expanded) | 22 | Passing |
| `test_subflow.py` | 6 | Passing |
| `test_help_browser.py` | 8 | Passing |
| **Total** | **106** | **All green** |

---

## Lint / Type Check Status

- **ruff**: 0 errors across all source and test files
- **mypy**: 0 errors (`ignore_missing_imports = true`; Pyright "possibly unbound" warnings
  are false positives from the try/except Qt fallback pattern — not real errors)

---

## What Is Not Yet Implemented

### M8 — Custom Node Type System ✓
- `NodeTypeWizard` dialog — ID, display name, category, base class, actions list, properties table, flags
- `NodeTypeDefinition.from_mapping()` validates on wizard Accept — shows error, keeps dialog open
- Inspector shows inherited type definition properties (T-603) — loaded from project `node_types/` YAML
- Tools > Node Type Library — table view of loaded types; Import from file copies YAML into project
- Node > New Custom Node Type → wizard → writes YAML + Python skeleton stub
- Node > Generate Node Skeleton → writes `custom/<type_id>.py` for selected canvas node
- Node > Toggle Breakpoint — red dot marker on `NodeItem`, adds to `_breakpoints` set for debug runs

### M12 — Polish and Completion ✓
- T-P01: code_manager base class resolved from node type definition (not TODO comment)
- T-P02: GUI run handler passes known_graphs so subflow execution works end-to-end
- T-P03: Tool Registry discovers @tool-decorated functions from project tools/ directory
- T-P04: Chinese (zh) and Japanese (ja) .ts + .qm translation files
- T-P05: help/img/ populated with UI screenshots; context help pages link them

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
