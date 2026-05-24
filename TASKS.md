# PocketFlow Creator — Task List

Tasks are ordered by implementation phase. Each phase depends on the previous phase being
substantially complete. Within a phase, tasks can be taken in any order.

Status: `[ ]` = open, `[x]` = done, `[-]` = in progress, `[~]` = deferred

---

## Housekeeping

- [x] T-001: Create project scaffold (models, validator, generator, GUI shell, docs, scripts)
- [x] T-002: Add setup, test, lint, format, and run scripts for Linux and Windows
- [x] T-003: Write starter test suite (7 tests, all passing)
- [x] T-004: Create STATUS.md and TASKS.md
- [ ] T-005: Fix pre-existing lint errors in scaffold (ruff: UP035, F401, UP037, E501 ×6)
- [ ] T-006: Add mypy type check pass to CI/scripts

---

## Phase 2 — RAD GUI Shell

- [ ] T-101: Wire File > New Project → create blank project in memory and update Project Explorer
- [ ] T-102: Wire File > Open Project → file dialog → YAML loader → populate Project Explorer
- [ ] T-103: Wire File > Save / Save All → YAML saver
- [ ] T-104: Wire File > Export PocketFlow Project → PythonGenerator → write output directory
- [ ] T-105: Wire File > Project Settings → settings dialog
- [ ] T-106: Wire Edit > Undo/Redo to a command stack
- [ ] T-107: Wire Project > Validate Project → GraphValidator → show results in Problems tab
- [ ] T-108: Wire Project > Generate Code → PythonGenerator → show in Generated Code tab
- [ ] T-109: Wire Project > Open Project Folder → open system file manager
- [ ] T-110: Wire Run > Run Project → MockProvider run → populate Run Log tab
- [ ] T-111: Wire Run > Run Tests → pytest subprocess → populate Test Results tab
- [ ] T-112: Wire Help > About → show version dialog
- [ ] T-113: Make Project Explorer populate from loaded project (graphs, prompts, node types, etc.)
- [ ] T-114: Add recent-projects list to File menu

---

## Phase 3 — Real Graph Designer

- [ ] T-201: Implement `QGraphicsScene`-backed graph canvas in central widget
- [ ] T-202: Implement `NodeItem` (QGraphicsItem) with title, type badge, and action port handles
- [ ] T-203: Implement `EdgeItem` — routed line from source action port to destination node
- [ ] T-204: Implement drag/drop from Component Palette to canvas (creates NodeModel + NodeItem)
- [ ] T-205: Implement selection — click node/edge to select, Object Inspector reflects selection
- [ ] T-206: Implement Object Inspector as a real property grid (QTreeWidget or QFormLayout)
- [ ] T-207: Sync Object Inspector edits back to NodeModel / EdgeModel
- [ ] T-208: Show continuous validation markers (error badges on invalid nodes/edges)
- [ ] T-209: Implement canvas zoom and pan
- [ ] T-210: Implement View > Zoom to Fit

---

## Phase 4 — Editors

- [ ] T-301: Integrate Python syntax-highlighting editor (QSyntaxHighlighter or third-party widget)
- [ ] T-302: Integrate Markdown editor/preview for prompt files
- [ ] T-303: Integrate YAML editor with validation feedback
- [ ] T-304: Add shared-store designer panel (key-value table with type annotations)
- [ ] T-305: Wire Tools > Provider Manager → dialog for creating/editing Ollama/mock profiles
- [ ] T-306: Wire Tools > Tool Registry → dialog listing registered Python tool functions
- [ ] T-307: Wire Tools > Shared Store Inspector → live view of shared-store state during run

---

## Phase 5 — Code Generation and Export

- [ ] T-401: Replace ad-hoc PythonGenerator with Jinja2 (or similar) template-based generator
- [ ] T-402: Implement generated test scaffolding for each exported flow
- [ ] T-403: Implement File > Export PocketFlow Project → full package with `generated/` and `custom/`
- [ ] T-404: Guard `custom/` directory from overwrite on re-export
- [ ] T-405: Implement graph image export (SVG/PNG from QGraphicsScene)
- [ ] T-406: Implement project report export (Markdown summary of nodes, edges, requirements)

---

## Phase 6 — Run and Debug

- [ ] T-501: Implement `OllamaProvider.complete()` via HTTP to Ollama REST API
- [ ] T-502: Implement Run > Run Active Flow with MockProvider — capture trace
- [ ] T-503: Implement step debugger — pause after each node execution, show shared-store diff
- [ ] T-504: Populate Shared Store tab live during a run
- [ ] T-505: Populate Prompt Preview tab for selected LLM node
- [ ] T-506: Implement Run > Debug Active Flow with breakpoints
- [ ] T-507: Implement run trace export

---

## Phase 7 — Custom Node Type System

- [ ] T-601: Implement node type wizard dialog (name, category, base class, properties, actions)
- [ ] T-602: Validate custom node type metadata against schema on creation
- [ ] T-603: Implement node type inheritance — show inherited properties and actions in inspector
- [ ] T-604: Add custom node library manager — list, import, and version custom node packages
- [ ] T-605: Wire Node > New Custom Node Type → wizard → write YAML + Python skeleton
- [ ] T-606: Wire Node > Generate Node Skeleton → write Python class file for selected node type

---

## Project File I/O (cross-cutting)

- [ ] T-701: Implement `ProjectLoader` — load `.pfcproj.yaml` into `ProjectModel` + `GraphModel`s
- [ ] T-702: Implement `ProjectSaver` — serialize `ProjectModel` + `GraphModel`s to YAML
- [ ] T-703: Round-trip test: load example → save → load again → compare models
- [ ] T-704: Implement graph file loader — load individual graph YAML into `GraphModel`
- [ ] T-705: Implement graph file saver — serialize `GraphModel` to graph YAML

---

## Testing (ongoing)

- [ ] T-801: Add GUI smoke test infrastructure (offscreen Qt platform, or headless XVfb)
- [ ] T-802: Add test for `ProjectLoader` round-trip
- [ ] T-803: Add test for code generation completeness against example project
- [ ] T-804: Add test for `OllamaProvider` using a mock HTTP server
- [ ] T-805: Reach 50+ tests covering all implemented behavior
