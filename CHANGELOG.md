# Changelog

All notable changes to PocketFlow Creator are documented here.
Entries are ordered newest-first within each version.

---

## [Unreleased]

### Added — Getting to Know Nodes tutorial series
- 7-file tutorial series (`gtkn_index.md` + 6 part files) covering all 20 built-in node types
  through hands-on mini-flows, progressing simplest → most complex
- Part 1: Start, Stop, Basic — foundation lifecycle and shared store
- Part 2: File Reader, File Writer, Python Tool — I/O and @tool functions
- Part 3: Router, Human Review, Human Input — flow control and human-in-the-loop
- Part 4: LLM Prompt, JSON LLM, Classifier, Judge — LLM integration patterns
- Part 5: Batch, Async, Async Batch, Async Parallel Batch — batch and async execution
- Part 6: RAG, Agent, Subflow — advanced patterns
- `Help > Getting to Know Nodes` menu item added; opens `tutorials/gtkn_index.md`
- Tutorials index updated with series table and links

---

## [0.2.0] — 2026-05-27

### Added — Graph Auto Arrange (M14)
- Auto Arrange dialog (`View > Auto Arrange…`, Ctrl+Shift+L) with three layout algorithms: Layered BFS, Grid, and Force-directed (spring-embedder)
- Three connector styles: Straight, Curved (quadratic Bezier), and Orthogonal (right-angle routing)
- `EdgeItem` upgraded from `QGraphicsLineItem` to `QGraphicsPathItem` — `update_position(connector_style)` builds the path for whichever style is active
- `GraphScene.set_connector_style()`, `layout_grid()`, `layout_force()` — new scene methods; `auto_layout()` now accepts `h_gap`/`v_gap` parameters
- `AutoArrangeDialog` in `main.py` — algorithm, connector style, h_gap, v_gap, and max-columns (for grid) are configurable before each run
- Auto Arrange is undoable — pushes a `GraphSnapshotCommand` to the undo stack
- `auto_arrange` dict field on `ProjectModel`; `ProjectLoader`/`ProjectSaver` persist settings under `auto_arrange:` in `.pfcproj.yaml`
- Saved connector style is restored when a project is opened

### Added — Undo / Redo
- Snapshot-based undo/redo (Ctrl+Z / Ctrl+Y) for all graph mutations: add node, delete node/edge, add edge, edit node properties, change edge action, and move node
- `GraphSnapshotCommand` in `commands.py` — single command class stores `deepcopy(graph)` before/after each mutation and rebuilds the scene via `GraphScene.load_graph()` on undo/redo
- `node_drag_started` and `node_move_finished` signals on `GraphScene` to detect drag completion for move commands
- Undo stack is cleared automatically when opening, creating, or switching projects

### Changed — Node Type Wizard layout
- `NodeTypeWizard` restructured into a three-tab layout: **Definition** (identity fields + flags), **Actions** (list + add/remove), **Properties** (table + add/remove)
- Dialog resized from 560×560 to 560×360 so it fits smaller displays

---

## [0.1.0] — 2026-05-23 through 2026-05-26

### Added — Data flow and canvas polish (2026-05-26)
- Data Flow Report (`Project > Data Flow Report`) — generates a per-node report of reads/writes, shared-store key lifecycle, and data-flow warnings
- Multi-action output ports — nodes with multiple actions get one output port per action; node height grows dynamically based on action count
- Input port label — shows the node's `input_key` property (fallback: `"in"`) beside the input port dot
- Output port action labels — rendered inside the node body, right-aligned, one row per action
- Separator line between node header and action rows when more than one action is present
- Zoom In / Zoom Out (Ctrl++ / Ctrl+-) via View menu
- Zoom to selected node (Ctrl+Shift+Z) via View menu
- Zoom percentage indicator in the status bar (permanent widget, updates on all zoom operations)
- Tutorial updates: node port labels, Data Flow Report usage, and new keyboard shortcuts documented in parts 1 and 3

### Added — LLM prompt and provider features (2026-05-25)
- Shared store value interpolation into LLM prompts before sending (e.g. `{{key}}` replaced at runtime)
- `prompt_type` / `prompt_file` properties added to Classifier, Agent, and Judge node types
- Ollama provider: live model list fetched from `/api/tags`; combo is populated on dialog open and refreshed on demand
- `prompt_type` supports `"string"` (inline) and `"path"` (file reference) modes for all LLM nodes

### Fixed — Graph editor and Ollama wiring (2026-05-24, late)
- Delete key now correctly removes selected nodes and edges
- Double-click on a node opens its code stub in the Python editor tab
- Bidirectional graph/code sync: deleting a node's `# NODE_START` marker from the Python editor removes that node from the canvas on save
- Temp-project workflow: a temporary project is created on startup so all features (run, export, code gen) work immediately without requiring a named project
- Ollama provider fully wired end-to-end through the run loop

### Added — Tutorials (2026-05-24)
- Tutorial 0: IDE Tour — overview of the PocketFlow Creator interface
- Tutorial 1: Hello LLM — first LLM call, JSON output, and comparison of four providers (OpenAI, Anthropic, Gemini, Ollama)
- Tutorials reorganised: IDE Tour is Tutorial 0, Hello LLM is Tutorial 1

### Added — Help system and documentation (2026-05-24)
- PocketFlow Node Reference page (`Help > PocketFlow Node Reference`) — inline quick-reference for all built-in node types
- Integrated help browser (`HelpBrowser`) with 21 help pages, context-sensitive `?` buttons in every dialog, and F1 shortcut
- `Help > About PocketFlow` entry with expanded description page

### Added — Internationalisation (2026-05-24)
- i18n scaffolding: `QTranslator`, `tr()` wrapping throughout, English and Spanish `.ts` source files
- French and German translations added; compiled `.qm` files checked in
- Language selector in `Tools > Options` with restart-to-apply notice

### Added — Tutorials content (2026-05-24)
- 25 tutorials covering all PocketFlow patterns (M10 milestone)
- 4 hands-on exercises
- Tutorials 26–31: additional walkthroughs for 6 new node types
- Palette snippets for 6 new node types added alongside tutorials

### Added — Node types and icons (2026-05-24)
- 6 new PocketFlow node types: Classifier, Agent, Judge, Batch, Parallel, and File Writer, each with purpose-built QPainter icons
- File Writer node type (stub) added to palette and toolbar
- All node type icons replaced with purpose-built QPainter shapes (no longer letter/symbol placeholders)
- Node type icons shown in Component Palette and Node Types toolbar
- Hover and pressed visual states on node type toolbar buttons

### Fixed — Help and Markdown rendering (2026-05-24)
- Help browser now uses `QTextBrowser.setMarkdown()` for native rendering (removes manual HTML conversion)
- Live Markdown preview in the Markdown editor tab also uses `QTextBrowser.setMarkdown()`
- Help HTML wrapped in a complete document so `QTextBrowser` renders it correctly

### Added — Polish milestone M12 (2026-05-24)
- T-P01 through T-P05: miscellaneous polish items (inspector styling, theme, shortcut fixes)
- F1 shortcut set directly on the action (fixes post-hoc menu traversal workaround)

### Added — Canvas, inspector, and RAD studio features (2026-05-24)
- Canvas-to-code sync, auto-layout (`Ctrl+Shift+L`), zoom-to-fit (`Ctrl+0`), Delete key support
- Inspector: editable value cells styled with distinct background and tooltip; full property editing with type coercion and live graph validation
- System theme mode added alongside Light and Dark in Options

### Added — Subflow, packaging, and node type system (2026-05-24)
- T-B05: Subflow node support — PFCE2102 validator rule, runner passthrough, inspector `subflow_ref` field
- T-B04: Shared Store schema editor (JSON Schema type validation)
- T-B02/T-B03: Project templates and node snippet library
- T-B01/T-B07: Keyboard shortcuts and dark/light mode toggle
- T-B06: i18n scaffolding (merged above)
- T-B08: PyInstaller packaging — Linux and Windows spec files and `package.sh` build script
- M8: Node type system (T-601–T-606) — `NodeTypeDefinition`, YAML-based custom node types, node type wizard; 85 tests passing

### Added — Debugger and run infrastructure (2026-05-24)
- Debugger (T-B05/T-503/T-506): step-through debug run, breakpoints (F9), Resume/Stop controls, per-step shared-store snapshot in the Shared Store tab
- M7: `OllamaProvider` HTTP client, `FlowRunner`, run trace, Run menu fully wired (T-501/502/504/507/110/111)

### Added — Export pipeline (2026-05-24)
- M6-A: Jinja2 template-based `PythonGenerator` replacing the ad-hoc generator (T-401)
- M6-B: Export pipeline with `custom/` guard preserving user-edited code (T-402/T-403/T-404/T-104)
- M6-C: Graph image export (PNG/SVG) and project report export to Markdown (T-405/T-406)

### Added — Foundation milestones M1–M5 (2026-05-23)
- M1: All lint errors resolved; mypy clean (T-005, T-006)
- M2: `GraphLoader`/`GraphSaver` and `ProjectLoader`/`ProjectSaver` with round-trip tests
- M3: All primary menu actions wired to real handlers
- M4: `QGraphicsView` canvas with `NodeItem`, `EdgeItem`, drag-drop palette, and live inspector
- M5-A: Editor infrastructure — syntax highlighters (Python, YAML), explorer wiring, Markdown preview (T-301/T-302/T-303/T-305/T-306/T-307)
- M5-B: Shared Store designer — `QTableWidget` with Namespace/Key/Type/Default columns (T-304)

### Added — Initial scaffold (2026-05-23)
- PySide6 GUI scaffold with main window, docks, menu bar, and toolbar
- Data models: `GraphModel`, `NodeModel`, `EdgeModel`, `ProjectModel`, `NodeTypeDefinition`
- Graph validation rules and starter Python code generator
- Example document summarizer project
- Documentation set, setup/run/test scripts, and project TASKS/STATUS tracking
