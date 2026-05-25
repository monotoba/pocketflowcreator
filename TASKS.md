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

## M1 — Clean Baseline  ✓ Complete

**Deliverable:** Zero lint errors, mypy runs without configuration errors. This locks the
quality floor before real feature work begins.

**Depends on:** M0

- [x] T-005: Fix pre-existing lint errors in scaffold
- [x] T-006: Add `mypy src` to `scripts/lint.sh` and confirm clean pass

---

## M2 — Project File I/O  ✓ Complete

**Deliverable:** Full YAML round-trip for projects and graphs. Required before any GUI
File > Open or File > Save can work.

**Depends on:** M1

- [x] T-701: Implement `ProjectLoader` — parse `.pfcproj.yaml` into `ProjectModel` + graph file list
- [x] T-702: Implement `ProjectSaver` — serialize `ProjectModel` back to `.pfcproj.yaml`
- [x] T-704: Implement `GraphLoader` — parse `.pfcgraph.yaml` into `GraphModel`
- [x] T-705: Implement `GraphSaver` — serialize `GraphModel` to `.pfcgraph.yaml`
- [x] T-703: Round-trip test: load example → save → reload → assert models equal

---

## M3 — GUI Shell Wired  ✓ Complete

**Deliverable:** All primary menu actions route to real behavior (open/save/validate/generate).
Project Explorer reflects the loaded project tree.

**Depends on:** M2 (T-102 and T-103 require the loader/saver from M2)

- [x] T-101: Wire File > New Project → blank `ProjectModel` in memory, update Project Explorer
- [x] T-102: Wire File > Open Project → file dialog → `ProjectLoader` → populate explorer
- [x] T-103: Wire File > Save / Save All → `ProjectSaver` + `GraphSaver`
- [x] T-113: Make Project Explorer populate from loaded project (graphs, prompts, node types, tools)
- [x] T-107: Wire Project > Validate Project → `GraphValidator` → Problems tab
- [x] T-108: Wire Project > Generate Code → `PythonGenerator` → Generated Code tab
- [x] T-109: Wire Project > Open Project Folder → `QDesktopServices.openUrl`
- [x] T-114: Add recent-projects list under File menu (persist in user config)
- [x] T-112: Wire Help > About → version dialog
- [x] T-105: Wire File > Project Settings → project-level settings dialog
- [x] T-106: Wire Edit > Undo/Redo to a `QUndoStack`

---

## M4 — Real Graph Canvas  ✓ Complete

**Deliverable:** Users can place nodes by dragging from the palette; edges from loaded
graphs are visualized as straight lines between nodes. Users can select objects and edit
properties in a live inspector. Validation errors appear as badges on the canvas.

**Depends on:** M3

- [x] T-201: Replace central placeholder with a `QGraphicsView` + `QGraphicsScene` canvas
- [x] T-202: Implement `NodeItem` (`QGraphicsItem`) — title bar, type badge, action port handles
- [x] T-203: Implement `EdgeItem` — orthogonal routed line from action port to destination
- [x] T-204: Implement drag/drop from Component Palette → canvas creates `NodeModel` + `NodeItem`
- [x] T-205: Implement selection — single click selects node or edge; inspector reflects it
- [x] T-206: Implement Object Inspector as a real property grid (`QTreeWidget` or `QFormLayout`)
- [x] T-207: Sync inspector edits back to `NodeModel` / `EdgeModel` and re-validate live
- [x] T-208: Show validation error badges on node/edge items after each change
- [x] T-209: Implement canvas zoom (Ctrl+Scroll) and pan (middle-drag or spacebar-drag)
- [x] T-210: Wire View > Zoom to Fit → fit all items in view

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

- [x] T-501: Implement `OllamaProvider.complete()` — HTTP POST to Ollama `/api/generate`
- [x] T-502: Wire Run > Run Active Flow with `MockProvider` — capture trace, populate Run Log
- [x] T-504: Populate Shared Store tab live after each node step
- [x] T-505: Populate Prompt Preview tab for selected LLM node (show resolved prompt)
- [x] T-503: Implement step debugger — FlowRunner.steps() generator + run_debug() with StepController
- [x] T-506: Wire Run > Debug Active Flow — breakpoint markers on node items, Stop/Resume menu actions
- [x] T-507: Implement run trace export — save trace to `run_reports/<timestamp>.json`
- [x] T-110: Wire Run > Run Active Flow menu action to M7 runner
- [x] T-111: Wire Run > Run Tests → `pytest` subprocess, populate Test Results tab

---

## M8 — Custom Node Type System  ✓ Complete

**Deliverable:** Users can define new node types through a wizard, validate them against
the schema, and manage a local library of custom types.

**Depends on:** M4 (Component Palette must accept custom types), M5 (YAML editor)

- [x] T-601: Implement node type wizard dialog — name, category, base class, properties, actions
- [x] T-602: Validate custom node type YAML against `NodeTypeDefinition` schema on save
- [x] T-603: Support node type inheritance — show inherited properties and actions in inspector
- [x] T-604: Add custom node library manager — list, import, and version custom node packages
- [x] T-605: Wire Node > New Custom Node Type → wizard → write YAML + Python skeleton
- [x] T-606: Wire Node > Generate Node Skeleton → write Python class file for selected type

---

## M9 — Test Coverage and Polish  ✓ Complete

**Deliverable:** GUI smoke-test infrastructure in place, key integration paths covered,
test count at 50+, app ready for broader review.

**Depends on:** M7 (all major features implemented)

- [x] T-801: Add GUI smoke test infrastructure (offscreen Qt platform `QT_QPA_PLATFORM=offscreen`)
- [x] T-802: Add round-trip test for `ProjectLoader` → `ProjectSaver` → `ProjectLoader`
- [x] T-803: Add code generation completeness test against the document-summarizer example
- [x] T-804: Add `OllamaProvider` test using a mock HTTP server (`http.server` or `pytest-httpserver`)
- [x] T-805: Reach 50+ tests covering all implemented behavior across M1–M8

---

## M10 — Tutorials and Documentation  ✓ Complete

**Deliverable:** Comprehensive tutorial document covering all PocketFlow cookbook patterns
and all Creator-specific features. Users can self-onboard without external help.

**Depends on:** M9 (all features implemented)

- [x] T-D01: Research PocketFlow repo — catalog all tutorials and examples (40+ patterns)
- [x] T-D02: Part 1 — Creator Fundamentals (6 tutorials: IDE tour, first flow, inspector,
             code editor, custom node wizard, templates)
- [x] T-D03: Part 2 — PocketFlow Patterns (11 tutorials: hello world, chat, structured output,
             workflow, routing, agent, RAG, batch, HITL, judge, multi-agent, streaming, memory)
- [x] T-D04: Part 3 — Advanced Creator Features (8 tutorials: validation, debug, subflow,
             export, shared store designer, streaming, memory, packaging)
- [x] T-D05: Part 4 — Creator System Exercises (4 exercises: news summariser, coding agent,
             multi-provider router, full IDE workout)
- [x] T-D06: Update TASKS.md, STATUS.md, MEMORY.md with tutorial milestone

---

## Backlog / Deferred

Tasks identified but not yet scheduled into a milestone:

- [x] T-B01: Add keyboard shortcuts for all primary actions (designer canvas operations)
- [x] T-B02: Add project template system (File > New From Template)
- [x] T-B03: Add node template / snippet library (reusable pre-configured nodes)
- [x] T-B04: Implement shared-store schema editor with JSON Schema validation
- [x] T-B05: Add subflow support — `SubflowNode` that embeds another graph
- [x] T-B06: Internationalization / localization scaffolding (QTranslator setup, tr() wrapping, .ts files for en/es, update/compile scripts)
- [x] T-B07: Dark mode support (system palette + user override in settings)
- [x] T-B08: Windows installer / macOS .app bundle packaging

---

## M11 — Help System  ✓ Complete

**Deliverable:** Full integrated help system with navigable Markdown browser, context help
in every dialog, and tutorials moved from docs/ to the help/ tree.

- [x] T-H01: Create help folder structure (help/, help/tutorials/, help/context/, help/img/)
- [x] T-H02: Write main help pages (index, getting_started, your_first_flow, about_pocketflow, about_pocketflow_creator)
- [x] T-H03: Split TUTORIALS.md into part files in help/tutorials/ (index + 4 part files)
- [x] T-H04: Write 11 context help files in help/context/
- [x] T-H05: Implement HelpBrowser (QDialog with QTextBrowser, back/forward/home, Markdown→HTML)
- [x] T-H06: Wire Help menu (PocketFlow Creator Help → index.md, Quick Reference → tutorials/index.md)
- [x] T-H07: Add ? button helper (_add_help_button) and wire to Options, Provider Manager, Shared Store Designer
- [x] T-H08: Add ? button to Node Type Wizard
- [x] T-H09: Wire F1 shortcut to Help > PocketFlow Creator Help
- [x] T-H10: Update pyproject.toml package-data for all help/*.md files
- [x] T-H11: Write 8 tests for HelpBrowser (file existence, rendering, navigation)

---

## M12 — Polish and Completion  ✓ Complete

**Deliverable:** Close all known stub/gap items identified after M11.

- [x] T-P01: Fix code_manager base class — resolve actual PocketFlow base from node type, not `# TODO` comment
- [x] T-P02: Wire known_graphs into GUI run handler so subflow recursive execution works end-to-end
- [x] T-P03: Implement Tool Registry — discover and display @tool-decorated functions from project tools/ directory
- [x] T-P04: Add Chinese (zh) and Japanese (ja) .ts + .qm translation files
- [x] T-P05: Populate help/img/ with UI screenshots and link them from help pages

---

## M13 — Graph Editor Repair

**Deliverable:** Graph canvas works reliably — nodes are deletable, connectors are
correctly routed and visually accurate, and all edge interactions are stable.

- [ ] T-G01: Repair graph editor — audit NodeItem, EdgeItem, and GraphScene for
             regressions introduced since M4; restore all broken interactions
- [ ] T-G02: Fix graph connectors — edge routing, port positions, and label placement
             should be correct after node moves, zoom changes, and scene reloads
