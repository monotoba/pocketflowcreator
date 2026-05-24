# PocketFlow Creator — Tasks and Milestones

Status markers: `[ ]` = open, `[x]` = done, `[-]` = in progress, `[~]` = deferred

Milestones group related tasks into deliverable increments. Each milestone should leave
the project in a working, committable state. Phases depend on earlier phases; tasks
within a milestone can be taken in any order unless noted.

---

## M0 — Initial Scaffold  ✓ Complete

**Deliverable:** Project structure, models, validator, generator, GUI shell, docs, scripts,
and initial test suite. Repository initialized and committed.

- [x] T-001: Create project scaffold (models, validator, generator, GUI shell, docs, scripts)
- [x] T-002: Add setup, test, lint, format, and run scripts for Linux and Windows
- [x] T-003: Write starter test suite (7 tests, all passing)
- [x] T-004: Create STATUS.md, TASKS.md, MEMORY.md, and .gitignore

---

## M1 — Clean Baseline

**Deliverable:** Zero lint errors, mypy runs without configuration errors. This locks the
quality floor before real feature work begins.

**Depends on:** M0

- [ ] T-005: Fix pre-existing lint errors in scaffold
  - `app/main.py`: UP035 (Sequence import), F401 (unused QWidget), E501 ×4
  - `generation/python_generator.py`: E501 ×1
  - `model/node_type.py`: UP037 (quoted return annotation)
  - `tests/test_python_generator.py`: E501 ×1
- [ ] T-006: Add `mypy src` to `scripts/lint.sh` and confirm clean pass

---

## M2 — Project File I/O

**Deliverable:** Full YAML round-trip for projects and graphs. Required before any GUI
File > Open or File > Save can work.

**Depends on:** M1

- [ ] T-701: Implement `ProjectLoader` — parse `.pfcproj.yaml` into `ProjectModel` + graph file list
- [ ] T-702: Implement `ProjectSaver` — serialize `ProjectModel` back to `.pfcproj.yaml`
- [ ] T-704: Implement `GraphLoader` — parse `.pfcgraph.yaml` into `GraphModel`
- [ ] T-705: Implement `GraphSaver` — serialize `GraphModel` to `.pfcgraph.yaml`
- [ ] T-703: Round-trip test: load example → save → reload → assert models equal

---

## M3 — GUI Shell Wired

**Deliverable:** All primary menu actions route to real behavior (open/save/validate/generate).
Project Explorer reflects the loaded project tree.

**Depends on:** M2 (T-102 and T-103 require the loader/saver from M2)

- [ ] T-101: Wire File > New Project → blank `ProjectModel` in memory, update Project Explorer
- [ ] T-102: Wire File > Open Project → file dialog → `ProjectLoader` → populate explorer
- [ ] T-103: Wire File > Save / Save All → `ProjectSaver` + `GraphSaver`
- [ ] T-113: Make Project Explorer populate from loaded project (graphs, prompts, node types, tools)
- [ ] T-107: Wire Project > Validate Project → `GraphValidator` → Problems tab
- [ ] T-108: Wire Project > Generate Code → `PythonGenerator` → Generated Code tab
- [ ] T-109: Wire Project > Open Project Folder → `QDesktopServices.openUrl`
- [ ] T-114: Add recent-projects list under File menu (persist in user config)
- [ ] T-112: Wire Help > About → version dialog
- [ ] T-105: Wire File > Project Settings → project-level settings dialog
- [ ] T-106: Wire Edit > Undo/Redo to a `QUndoStack`

---

## M4 — Real Graph Canvas

**Deliverable:** Users can place nodes by dragging from the palette; edges from loaded
graphs are visualized as straight lines between nodes. Users can select objects and edit
properties in a live inspector. Validation errors appear as badges on the canvas.

**Depends on:** M3

- [ ] T-201: Replace central placeholder with a `QGraphicsView` + `QGraphicsScene` canvas
- [ ] T-202: Implement `NodeItem` (`QGraphicsItem`) — title bar, type badge, action port handles
- [ ] T-203: Implement `EdgeItem` — orthogonal routed line from action port to destination
- [ ] T-204: Implement drag/drop from Component Palette → canvas creates `NodeModel` + `NodeItem`
- [ ] T-205: Implement selection — single click selects node or edge; inspector reflects it
- [ ] T-206: Implement Object Inspector as a real property grid (`QTreeWidget` or `QFormLayout`)
- [ ] T-207: Sync inspector edits back to `NodeModel` / `EdgeModel` and re-validate live
- [ ] T-208: Show validation error badges on node/edge items after each change
- [ ] T-209: Implement canvas zoom (Ctrl+Scroll) and pan (middle-drag or spacebar-drag)
- [ ] T-210: Wire View > Zoom to Fit → fit all items in view

---

## M5 — Editors

**Deliverable:** Users can edit Python custom code, Markdown prompts, and YAML metadata
inside the app. Provider profiles and tool registry are manageable via dialogs.

**Depends on:** M3 (editors open from Project Explorer)

- [x] T-301: Integrate Python syntax-highlighting editor for custom node code
  (`QSyntaxHighlighter` subclass or third-party widget such as QScintilla)
- [x] T-302: Integrate Markdown editor with live preview for prompt files
- [x] T-303: Integrate YAML editor with schema-driven validation feedback
- [x] T-304: Add shared-store designer panel — key/type/default table, editable
- [x] T-305: Wire Tools > Provider Manager → dialog for Ollama / mock provider profiles
- [x] T-306: Wire Tools > Tool Registry → dialog listing registered Python tool functions
- [x] T-307: Wire Tools > Shared Store Inspector → live key/value view (populated during run)

---

## M6 — Code Generation and Export

**Deliverable:** File > Export PocketFlow Project produces a full, runnable Python package.
Generated code uses templates. Re-export never overwrites `custom/`.

**Depends on:** M2, M3

- [x] T-401: Replace ad-hoc `PythonGenerator` with Jinja2 template-based generator
  (templates in `src/pocketflow_creator/templates/`)
- [x] T-402: Generate test scaffolding alongside each exported flow (`tests/test_<flow>.py`)
- [x] T-403: Implement File > Export PocketFlow Project → write full package under `exports/`
  with `generated/`, `custom/` (if new), `tests/`, and `main.py`
- [x] T-404: Guard `custom/` — skip files that already exist; warn user, do not overwrite
- [x] T-405: Implement graph image export — render `QGraphicsScene` to SVG and PNG
- [x] T-406: Implement project report export — Markdown summary of nodes, edges, validation status
- [x] T-104: Wire File > Export PocketFlow Project menu action to M6 export logic

---

## M7 — Run and Debug

**Deliverable:** Users can run the active flow with a real or mock provider, inspect
shared-store state step by step, and preview prompts for LLM nodes.

**Depends on:** M6 (needs exported/generated code), M5 (Prompt Preview and Shared Store tabs)

- [ ] T-501: Implement `OllamaProvider.complete()` — HTTP POST to Ollama `/api/generate`
- [ ] T-502: Wire Run > Run Active Flow with `MockProvider` — capture trace, populate Run Log
- [ ] T-504: Populate Shared Store tab live after each node step
- [ ] T-505: Populate Prompt Preview tab for selected LLM node (show resolved prompt)
- [ ] T-503: Implement step debugger — pause after each node, show shared-store diff
- [ ] T-506: Wire Run > Debug Active Flow — breakpoint markers on node items
- [ ] T-507: Implement run trace export — save trace to `run_reports/<timestamp>.json`
- [ ] T-110: Wire Run > Run Project menu action to M7 runner
- [ ] T-111: Wire Run > Run Tests → `pytest` subprocess, populate Test Results tab

---

## M8 — Custom Node Type System

**Deliverable:** Users can define new node types through a wizard, validate them against
the schema, and manage a local library of custom types.

**Depends on:** M4 (Component Palette must accept custom types), M5 (YAML editor)

- [ ] T-601: Implement node type wizard dialog — name, category, base class, properties, actions
- [ ] T-602: Validate custom node type YAML against `NodeTypeDefinition` schema on save
- [ ] T-603: Support node type inheritance — show inherited properties and actions in inspector
- [ ] T-604: Add custom node library manager — list, import, and version custom node packages
- [ ] T-605: Wire Node > New Custom Node Type → wizard → write YAML + Python skeleton
- [ ] T-606: Wire Node > Generate Node Skeleton → write Python class file for selected type

---

## M9 — Test Coverage and Polish

**Deliverable:** GUI smoke-test infrastructure in place, key integration paths covered,
test count at 50+, app ready for broader review.

**Depends on:** M7 (all major features implemented)

- [ ] T-801: Add GUI smoke test infrastructure (offscreen Qt platform `QT_QPA_PLATFORM=offscreen`)
- [ ] T-802: Add round-trip test for `ProjectLoader` → `ProjectSaver` → `ProjectLoader`
- [ ] T-803: Add code generation completeness test against the document-summarizer example
- [ ] T-804: Add `OllamaProvider` test using a mock HTTP server (`http.server` or `pytest-httpserver`)
- [ ] T-805: Reach 50+ tests covering all implemented behavior across M1–M8

---

## Backlog / Deferred

Tasks identified but not yet scheduled into a milestone:

- [ ] T-B01: Add keyboard shortcuts for all primary actions (designer canvas operations)
- [ ] T-B02: Add project template system (File > New From Template)
- [ ] T-B03: Add node template / snippet library (reusable pre-configured nodes)
- [ ] T-B04: Implement shared-store schema editor with JSON Schema validation
- [ ] T-B05: Add subflow support — `SubflowNode` that embeds another graph
- [ ] T-B06: Internationalization / localization scaffolding
- [ ] T-B07: Dark mode support (system palette + user override in settings)
- [ ] T-B08: Windows installer / macOS .app bundle packaging
