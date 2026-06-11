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

## Completed Former Backlog

All formerly identified backlog items have been completed:

- [x] T-B01: Add keyboard shortcuts for all primary actions (designer canvas operations)
- [x] T-B02: Add project template system (File > New From Template)
- [x] T-B03: Add node template / snippet library (reusable pre-configured nodes)
- [x] T-B04: Implement shared-store schema editor with JSON Schema validation
- [x] T-B05: Add subflow support — `SubflowNode` that embeds another graph
- [x] T-B06: Internationalization / localization scaffolding (QTranslator setup, tr() wrapping, .ts files for en/es, update/compile scripts)
- [x] T-B07: Dark mode support (system palette + user override in settings)
- [x] T-B08: Windows installer / macOS .app bundle packaging

---

## Open Backlog

No scheduled backlog items at this time. Next work is user-directed.

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

## M13 — Graph Editor Repair  ✓ Complete

**Deliverable:** Graph canvas works reliably — nodes are deletable, connectors are
correctly routed and visually accurate, and all edge interactions are stable.

- [x] T-G01: Repair graph editor — audit NodeItem, EdgeItem, and GraphScene for
             regressions introduced since M4; restore all broken interactions
- [x] T-G02: Fix graph connectors — edge routing, port positions, and label placement
             should be correct after node moves, zoom changes, and scene reloads

---

## M14 — Graph Auto Arrange  ✓ Complete

**Deliverable:** Users can arrange the graph canvas automatically using three layout algorithms
(Layered BFS, Grid, Force-directed) and three connector styles (Straight, Curved, Orthogonal).
Settings are persisted in the project file and the operation is undoable.

**Depends on:** M13

- [x] T-A01: Add `auto_arrange` dict field to `ProjectModel`; update `ProjectLoader`/`ProjectSaver`
             to load/save it under `auto_arrange:` in `.pfcproj.yaml`
- [x] T-A02: Change `EdgeItem` base class from `QGraphicsLineItem` to `QGraphicsPathItem`;
             implement `update_position(connector_style)` with straight, curved (Bezier),
             and orthogonal path building
- [x] T-A03: Add `connector_style` attribute and `set_connector_style()` to `GraphScene`;
             update `update_edges()` and `add_edge()` to thread the style through
- [x] T-A04: Add `layout_grid()` (row/column placement) and `layout_force()` (spring-embedder)
             to `GraphScene`; parameterise `auto_layout()` with `h_gap`/`v_gap`
- [x] T-A05: Implement `AutoArrangeDialog` — algorithm, connector style, h_gap, v_gap, max_cols
- [x] T-A06: Replace `_on_auto_layout` with `_on_auto_arrange` in `MainWindow` — shows dialog,
             runs chosen algorithm, pushes `GraphSnapshotCommand` to undo stack, saves settings
             to `project.auto_arrange`, zooms to fit
- [x] T-A07: Apply saved `connector_style` from project when loading a project/graph

---

## M15 — Boy Scout Refactoring  ✓ Complete

**Deliverable:** Codebase readability and maintainability improvements identified in
[`BOY_SCOUT_NOTES.md`](BOY_SCOUT_NOTES.md). No functional changes — existing tests must
stay green throughout. Tasks are grouped by theme and ordered high → medium → low priority.

**Depends on:** M14

### Group 1 — Fix the Qt try/import pattern (Cross-cutting)

- [x] T-R01 🔴 Replace `except Exception` with `except ImportError` in the PySide6
  try/import blocks in `app/canvas.py`, `app/commands.py`, and `app/editors.py`.
- [x] T-R02 🔴 Resolve Pyright "possibly unbound" false-positives in `app/canvas.py`
  and `app/editors.py` by moving type-only Qt imports under `if TYPE_CHECKING:` guards
  and using a runtime availability check for non-type usage.

### Group 2 — Split oversized files

- [x] T-R03 🔴 Split `app/canvas.py` (1404 lines) into a `canvas/` sub-package:
  `canvas/icons.py`, `canvas/items.py`, `canvas/scene.py`, `canvas/view.py`,
  `canvas/palette.py`, and a `canvas/__init__.py` that re-exports all existing public
  names so no external imports need to change.
- [x] T-R04 🔴 Reduce `app/main.py` (2556 lines) by extracting self-contained dialogs
  and the run controller:
  `app/dialogs/provider_manager.py` (`ProviderManagerDialog`),
  `app/dialogs/shared_store_designer.py` (`SharedStoreDesignerDialog`),
  `app/dialogs/auto_arrange_dialog.py` (`AutoArrangeDialog`),
  `app/run_controller.py` (`RunController` — all threading/signal/input-callback wiring).
  main.py: 2556 → 2141 lines. All 106 tests pass.

### Group 3 — Eliminate duplicated code in `app/main.py`

- [x] T-R05 🔴 Extract `_build_provider()` to replace the identical 12-line
  provider-construction block duplicated at lines 1090–1101 and 1240–1251.
- [x] T-R06 🔴 Extract the human-input callback wiring (inner signal class, `_input_event`,
  `_input_result`, GUI slot, `input_cb` closure) into a reusable helper shared by
  `_on_run_active_flow` and `_on_debug_active_flow`.
- [x] T-R07 🟡 Extract `_clear_selection_state()` and call it from both `_on_undo` and
  `_on_redo` (currently identical except for the `undo()`/`redo()` call).
- [x] T-R08 🟡 Move all inline `import` statements inside handler methods (`threading`,
  `uuid`, `re`, `shutil`, `subprocess`, `sys`, `ast`, etc.) to file-level imports.
- [x] T-R09 🟡 Define module-level constants for all repeated `QSettings` key strings
  (`_ORG`, `_APP`, `_SKEY_PROVIDER`, `_SKEY_OLLAMA_URL`, `_SKEY_OLLAMA_MODEL`, etc.)
  and replace the ~9 scattered string literals.
- [x] T-R10 🟡 Fix f-strings passed into `self.tr()` at lines 603, 861, 1861, and 2020 —
  format the string *after* translation using `% name` or `.format(name)`.
- [x] T-R11 🟡 Change `_stop_action` and `_resume_action` type annotations from `object`
  to `QAction` and remove all `# type: ignore[attr-defined]` comments on their usage.
- [x] T-R12 🟡 Change `_ensure_active_graph` return type from `bool` to `None`, remove
  the `return True` statements, and clean up the now-dead
  `if not self._ensure_active_graph(): return` guards in callers.
- [x] T-R13 🟡 Replace `assert self._active_graph_rel is not None` (lines 1769, 1834)
  with explicit `if … is None: return` guards that are safe under `python -O`.
- [x] T-R14 🟢 Add named constant `_PNG_BACKGROUND_DARK = 0xFF1A1A1A` for the PNG export
  background fill colour (line 1028).
- [x] T-R15 🟢 Remove the redundant `_PALETTE_ITEMS` list from `canvas.py`; have
  `PaletteWidget` iterate `_PALETTE_ITEMS_EX` directly.

### Group 4 — Decompose `FlowRunner.steps` in `runtime/runner.py`

- [x] T-R16 🔴 Decompose the 160-line `FlowRunner.steps` while-loop body by extracting
  each node-type branch into its own private method:
  `_handle_subflow_node`, `_handle_llm_node`, `_handle_classifier_node`,
  `_handle_judge_node`, `_handle_agent_node`, `_handle_human_input_node`.
- [x] T-R17 🟡 Replace `on_step: object` and `input_callback: object` with proper
  `Callable` types from `collections.abc`; remove the resulting `# type: ignore[operator]`.
- [x] T-R18 🟡 Replace `bp = breakpoints or set()` with
  `bp = breakpoints if breakpoints is not None else set()` to avoid the falsy-empty-set trap.
- [x] T-R19 🟢 Replace the `# noqa: UP028` suppression on the subflow inner-step loop with
  a comment explaining why `list()` materialisation is needed (to access `inner_steps[-1]`
  after iteration).

### Group 5 — Fix `validation/graph_validator.py`

- [x] T-R20 🔴 Assign a unique error code to the second `PFCE2102` usage (line 123,
  "subflow references missing graph") — change it to `PFCE2103`.
- [x] T-R21 🟡 Mark all `_validate_*` helper methods as `@staticmethod` (none use `self`).
- [x] T-R22 🟡 Compute `graph.node_ids()` once in `validate()` and pass it as a parameter
  to sub-methods, eliminating the redundant recomputation.

### Group 6 — Refactor `app/canvas.py` internals

- [x] T-R23 🟡 Add named constant `_DRAG_LINE_Z = 1000` and replace the bare literal in
  `GraphView.mousePressEvent`.
- [x] T-R24 🟡 Add `is_dark` property to `GraphScene`; update `NodeItem.paint` to call
  `scene.is_dark` instead of accessing `scene._dark` directly via `hasattr`.
- [x] T-R25 🟡 Unify the 20 `_ico_*` icon functions to a consistent `(p, sz, bg)` signature
  so `_ICON_DRAW` can dispatch uniformly and the `if/elif` special-case block in
  `_paint_node_pixmap` can be removed.
- [x] T-R26 🟡 Extract a shared `_hit_test_port(scene_pos, port_fn, hit_r)` helper used
  by both `_node_at_action_port` and `_node_at_input_port`.
- [x] T-R27 🟢 Add explicit type annotation `_edge_rubber: QGraphicsLineItem | None` in
  `GraphView.__init__`.

### Group 7 — Refactor `app/editors.py`

- [x] T-R28 🟡 Introduce `_RulesHighlighter(QSyntaxHighlighter)` base class with the
  shared `highlightBlock` implementation; have `PythonHighlighter` and `YamlHighlighter`
  inherit from it.
- [x] T-R29 🟢 Move highlight rule objects to class-level `ClassVar` attributes so they
  are built once, not on every instantiation.

### Group 8 — Model layer improvements

- [x] T-R30 🟡 Replace `position: dict[str, float]` in `NodeModel` with a typed `Position`
  structure (`TypedDict` with keys `x`/`y`, or a small `@dataclass(slots=True)`).
- [x] T-R31 🟡 Add a `_node_index` cached property (or cached dict) to `GraphModel` for
  O(1) node lookups; add an O(n) complexity comment to `find_node`.
- [x] T-R32 🟡 Refactor `NodeTypeDefinition.from_mapping` to build `kwargs` dynamically
  from the dataclass field list so adding a new field requires only one change, not two.
- [x] T-R33 🟢 Add class-level docstrings to `NodeModel`, `EdgeModel`, `GraphModel`,
  and `ProjectModel`.
- [x] T-R34 🟢 Type `ProjectModel.auto_arrange` as `dict[str, Any]` (minimum) or introduce
  an `AutoArrangeSettings` `TypedDict`.
- [x] T-R35 🟢 Fix the YAML boolean coercion edge case in `NodeTypeDefinition.from_mapping`
  so that a YAML-quoted `"false"` string is not treated as `True`.

### Group 9 — I/O layer (`graph_io.py`, `project_io.py`)

- [x] T-R36 🟡 Mark `GraphLoader._parse_node`, `GraphLoader._parse_edge`,
  `GraphSaver._node_to_dict`, and `GraphSaver._edge_to_dict` as `@staticmethod`.
- [x] T-R37 🟡 Decompose `ProjectLoader.load` into `@staticmethod` helper methods
  symmetric to the `GraphLoader` pattern.
- [x] T-R38 🟢 Add an explanatory comment next to the schema version mismatch checks in
  both `GraphLoader` and `ProjectLoader` noting no migration path is intentional.

### Group 10 — Runtime providers (`runtime/providers.py`)

- [x] T-R39 🟡 Broaden exception handling in `OllamaProvider.complete` to also catch
  `json.JSONDecodeError` and re-raise uniformly as `RuntimeError`.
- [x] T-R40 🟢 Add a one-line docstring to the `LLMProvider` Protocol `complete` method.

### Group 11 — Code generation (`generation/python_generator.py`)

- [x] T-R41 🟡 Mark `PythonGenerator._class_name` and `_var_name` as `@staticmethod`.
- [x] T-R42 🟡 Replace the untyped `dict` return type of `_node_ctx` with a `_NodeCtx`
  `TypedDict`.

### Group 12 — Code manager (`app/code_manager.py`)

- [x] T-R43 🟡 Fix `add_node` to reuse the in-memory text string when the start marker
  already exists, eliminating the redundant second `read_text()` call.
- [x] T-R44 🟢 Fix `_stem_from_rel` to use an explicit `endswith(".pfcgraph.yaml")` check
  rather than the broad second `.replace(".yaml", "")`.

### Group 13 — Public API exports

- [x] T-R45 🟡 Add `__all__` to `model/__init__.py`, `generation/__init__.py`,
  `validation/__init__.py`, and `runtime/__init__.py`.

### Group 14 — Single source of truth for node display names

- [x] T-R46 🟡 Update `PaletteWidget` and the toolbar builder in `app/main.py` to source
  display names from `BUILTIN_NODE_TYPES` rather than the parallel `_PALETTE_ITEMS_EX`
  list, keeping `_PALETTE_ITEMS_EX` only for colour values.

### Group 15 — `app/commands.py` clarity

- [x] T-R47 🟢 Add an explanatory comment to `GraphSnapshotCommand.redo` describing why
  the first call is skipped (Qt pushes → calls redo immediately; mutation was already
  applied live).

---

### M15 Task Summary

| Priority | Count |
|----------|-------|
| 🔴 High  | 8     |
| 🟡 Medium | 27   |
| 🟢 Low   | 12    |
| **Total** | **47** |

---

## M16 — Add-on Nodes & Multi-file Packages  ✓ Complete

**Deliverable:** Node packages can now be organized as folders with multiple files using the
`{name}/{name}.py` convention. 34 scientific & engineering add-on nodes ship with Creator. The
palette gains a dedicated add-on section separate from built-in and custom nodes. Node Type
Library expanded to four tabs: Built-in, Scientific & Engineering, Installed Custom, ⚠ Errors.

**Depends on:** M15

- [x] T-M16-01: Implement multi-file node packages with `{name}/{name}.py` entry-point convention
- [x] T-M16-02: Add isolation via `importlib.util.spec_from_file_location` to prevent plugin conflicts
- [x] T-M16-03: Create `addon_nodes/` directory with 34 scientific & engineering node packages
- [x] T-M16-04: Add `_ADDON_NODE_REGISTRY` separate from `_USER_NODE_REGISTRY`
- [x] T-M16-05: Wire Node Type Library with four-tab interface (Built-in, Add-on, Custom, Errors)
- [x] T-M16-06: Add palette section separator and toolbar gaps for visual organization

---

## M17 — Standalone Script Generation  ✓ Complete

**Deliverable:** Export graphs as fully self-contained, zero-dependency Python scripts. 76 node
types implemented with complete node dispatch logic. Scripts include embedded provider
implementations (Ollama, OpenAI, Anthropic, Gemini, DeepSeek), environment variable support,
automatic dependency detection, and graceful error handling. Export as single `.py` file or
complete `.zip` archive with setup/run scripts and requirements.

**Depends on:** M16

- [x] T-M17-01: Implement standalone script generator for 14 core data processing nodes
- [x] T-M17-02: Implement 9 LLM/Reasoning node types in standalone generator
- [x] T-M17-03: Implement 6 External API nodes (web search/scrape, webhooks, PDF, spreadsheet)
- [x] T-M17-04: Implement 7 Memory/State nodes (secrets, registries, stacks, queues, local memory)
- [x] T-M17-05: Implement 3 Database nodes (schema, NL-to-SQL, SQL execute)
- [x] T-M17-06: Implement 8 Data/File I/O nodes (text chunking, regex, templates, code gen, serial)
- [x] T-M17-07: Implement 10 Vector/ML/Audio/Vision nodes (embeddings, email, retry, rate limiting)
- [x] T-M17-08: Implement 8 Hardware/Communication/System nodes (USB, audio, video, webcam, socket, shell)
- [x] T-M17-09: Add embedded provider implementations (Ollama, OpenAI, Anthropic, Gemini, DeepSeek)
- [x] T-M17-10: Implement stdin/stdout/stderr I/O for interactive nodes (Human Input/Review)
- [x] T-M17-11: Add export-standalone-archive feature with setup/run scripts and requirements.txt
- [x] T-M17-12: Test standalone scripts in CI/CD pipelines with environment variable substitution
