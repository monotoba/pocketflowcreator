# PocketFlow Creator — Status

## Current State: v0.3.2 — M0–M17 Complete

PocketFlow Creator is active and unarchived.

Current automated test status:
- 181 CI-safe/headless tests passing
- GUI/manual tests that require an interactive desktop environment are not run in GitHub Actions
- `QT_QPA_PLATFORM=offscreen` is used for headless Qt-compatible automated tests

## Test Scope Note

The reported automated test count refers to the pytest suite that is intended to run in CI/headless environments. Some GUI tests, manual interaction tests, or display-dependent tests are intentionally excluded from GitHub Actions because they require a live desktop/session and cannot be reliably executed in the GitHub runner environment.

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
- `EdgeItem` — now `QGraphicsPathItem` supporting straight/curved/orthogonal paths
- Drag-drop from Component Palette creates nodes on canvas
- Selection → Object Inspector property grid (ID, Type, Title editable, Position, etc.)
- Inspector edits sync back to `NodeModel` live
- Validation error badges (`_has_error` flag, red border) via `apply_validation()`
- Ctrl+Scroll zoom, middle-drag pan, View > Zoom to Fit

### M5 — Editors ✓
- `PythonHighlighter` / `YamlHighlighter` (`QSyntaxHighlighter` subclasses) in `editors.py`
- Markdown tab: `QSplitter` with editor + live `QTextBrowser` preview
- YAML tab: validates on every keystroke, shows parse error in status bar
- Project Explorer double-click → opens `.py`/`.md`/`.yaml` into correct bottom tab
- Tools > Provider Manager → dialog persisting Ollama + Mock settings in `QSettings`
- Tools > Tool Registry — discovers `@tool`-decorated functions via AST scan
- Shared Store Designer: key/type/default table, YAML serialized

### M6 — Code Generation and Export ✓
- `PythonGenerator` — Jinja2 template-based; generates `nodes.py` and `flow.py` per graph
- `Exporter` — writes full package to `exports/<pkg>/`; `custom/` guard prevents overwrites
- File > Export PocketFlow Project wired
- Project > Export Graph Image → PNG or SVG
- Project > Export Project Report → Markdown

### M7 — Run and Debug ✓
- `OllamaProvider.complete()` — HTTP POST to Ollama `/api/generate`
- `FlowRunner` — interprets `GraphModel` directly; `RunTrace` + `RunStep` dataclasses
- Run > Run Active Flow — populates Run Log + Shared Store tabs; saves trace JSON
- Run > Debug Active Flow — background thread with `StepController` pause/resume + breakpoints
- Run > Run Tests — `pytest` subprocess; populates Test Results tab

### M8 — Custom Node Type System ✓
- `NodeTypeWizard` dialog — 3-tab layout (Definition / Actions / Properties), resized 560×360
- `NodeTypeDefinition.from_mapping()` validates on Accept
- Inspector shows inherited type properties from project `node_types/` YAML
- Node > New Custom Node Type → wizard → writes YAML + Python skeleton stub
- Node > Generate Node Skeleton → writes `custom/<type_id>.py`

### M9 — Test Coverage and Polish ✓
GUI smoke-test infra, round-trip tests, 106 tests all passing.

### M10 — Tutorials and Documentation ✓
25 tutorials + 4 exercises across 4 part files in `help/tutorials/`.

### M11 — Help System ✓
`HelpBrowser` dialog, 21 Markdown help files, `?` buttons in every dialog, F1 shortcut.

### M12 — Polish and Completion ✓
code_manager base class resolved, Tool Registry, zh/ja translations, help screenshots.

### M13 — Graph Editor Repair ✓
Delete key, double-click to code, bidirectional graph/code sync, Ollama end-to-end,
temp-project startup workflow.

### Undo/Redo ✓ (shipped between M13 and M14)
`GraphSnapshotCommand` in `commands.py` — snapshot before/after each mutation.
Covers: add node, delete node/edge, add edge, edit property, change edge action, move node.
`_on_undo` / `_on_redo` wrappers clear inspector and selection state after each stack operation.

### M14 — Graph Auto Arrange ✓
- `AutoArrangeDialog` — algorithm + connector style + h_gap + v_gap + max_cols (for grid)
- Layered BFS (`auto_layout(h_gap, v_gap)`), Grid (`layout_grid()`), Force-directed (`layout_force()`)
- `EdgeItem` upgraded to `QGraphicsPathItem`; `update_position(connector_style)` builds
  straight / curved (quadratic Bezier) / orthogonal (right-angle) paths
- `GraphScene.set_connector_style()` — updates all edges immediately
- Settings persisted in `ProjectModel.auto_arrange` dict → `.pfcproj.yaml` under `auto_arrange:`
- Saved connector style restored on project open
- Operation pushes `GraphSnapshotCommand` to undo stack

---

## What Is Implemented

### Core Data Model (`src/pocketflow_creator/model/`)
- `GraphModel`, `NodeModel`, `EdgeModel`, `NodeTypeDefinition`, `ProjectModel`
- `ProjectModel` fields: `name`, `package_name`, `root`, `default_provider`, `default_model`,
  `graphs`, `prompts`, `node_types`, `shared_store_schema`, `auto_arrange`

### File I/O (`src/pocketflow_creator/graph_io.py`, `project_io.py`)
- `GraphLoader`, `GraphSaver` — YAML ↔ `GraphModel`
- `ProjectLoader`, `ProjectSaver` — YAML ↔ `ProjectModel` (including `auto_arrange`)

### Validation (`src/pocketflow_creator/validation/`)
- `GraphValidator` — unique IDs, start node, edge endpoints, declared actions
- Error codes PFCE1001–PFCE1003, PFCE2001–PFCE2003, PFCE2101

### Code Generation (`src/pocketflow_creator/generation/`)
- `PythonGenerator` — Jinja2 template-based
- `Exporter` — full package export with `custom/` guard
- `generate_project_report()`, `generate_dataflow_report()`

### Runtime (`src/pocketflow_creator/runtime/`)
- `LLMProvider` protocol, `MockProvider`, `OllamaProvider`
- `FlowRunner`, `RunTrace`, `RunStep`, `StepController`

### GUI (`src/pocketflow_creator/app/`)
- `main.py`: `MainWindow`, `AutoArrangeDialog`, and all other inline dialogs
- `canvas.py`: `NodeItem`, `EdgeItem` (QGraphicsPathItem), `GraphScene`, `GraphView`, `PaletteWidget`
- `commands.py`: `GraphSnapshotCommand`
- `editors.py`: `PythonHighlighter`, `YamlHighlighter`
- `node_type_wizard.py`: `NodeTypeWizard` (3-tab layout)
- `help_browser.py`: `HelpBrowser`

---

## Test Status

181 tests, all passing. Run with:
```
python -m pytest
```

To verify the test count:
```
python -m pytest -q
```

---

## Lint / Type Check Status

- **ruff**: 0 errors across all source and test files
- **mypy**: 0 errors (`ignore_missing_imports = true`; Pyright "possibly unbound" warnings
  are false positives from the try/except Qt fallback pattern — not real errors)

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
