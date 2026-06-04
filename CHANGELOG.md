# Changelog

All notable changes to PocketFlow Creator are documented here.
Entries are ordered newest-first within each version.

---

## [Unreleased]

### Added — comprehensive standalone script generation (2026-06-03)

**Standalone Python script generation for all graphs**
- Export graphs as fully self-contained, zero-dependency Python scripts
- Embedded provider implementations (Ollama, OpenAI, Anthropic, Gemini, DeepSeek)
- Complete node dispatch logic with type-based execution for 76 implemented nodes
- Environmental variable support for API keys, webhooks, and credentials
- Single `.py` file can execute entire flow independently without framework
- Automatic dependency detection and helpful error messages at runtime

**7 new Hardware I/O node types added to palette**
- USB Serial Input/Output: Serial port communication
- Audio Input/Output: Microphone recording and speaker playback
- Video Input/Output: Webcam/camera recording and video playback
- Webcam: Direct webcam capture and streaming
- All nodes have custom icons and full property definitions
- New "Hardware I/O" category in palette ordering

**Implementation of 76 node types in standalone generator**
- Completed node type coverage across 10 categories
- Phase 1: 14 core data processing nodes
- Phase 2: 9 LLM/Reasoning nodes (subflow, RAG, chain-of-thought, debate, etc.)
- Phase 3: 6 External API nodes (web search/scrape, webhooks, PDF, spreadsheet)
- Phase 4: 7 Memory/State nodes (secrets, registries, stacks, queues, local memory)
- Phase 5: 3 Database nodes (schema, NL-to-SQL, SQL execute)
- Phase 6: 8 Data/File I/O nodes (text chunking, regex, templates, code gen, serial)
- Phase 7: 10 Vector/ML/Audio/Vision nodes (embeddings, vectors, email, retry, rate limiting)
- Phase 8: 19 Hardware/Communication/System nodes (USB, audio, video, webcam, socket, shell)

---

### Added — multi-file node packages and add-on node system (2026-05-28)

**Multi-file node packages**
- Node packages can now be a folder instead of a single file.
  Convention: `{name}/{name}.py` is the entry point; all other files in the folder
  are helpers importable via relative imports (`from . import helpers`).
- Isolation guaranteed via `importlib.util.spec_from_file_location` with
  `submodule_search_locations` — no `sys.path` mutation; two plugins with
  identically named helpers cannot interfere with each other.
- `install_node_package()` accepts both a `.py` file and a directory; validates
  the `{name}/{name}.py` convention before copying.
- 7 new tests covering: load, discovery, missing entry-point error, cross-plugin
  isolation, install, overwrite, and invalid-folder rejection.

**Add-on node system (`addon_nodes/`)**
- 34 scientific & engineering node packages ship with Creator in
  `src/pocketflow_creator/addon_nodes/`:
  Scientific Computing (2), Aerospace (11), Wind Energy (2),
  Weather/Atmosphere (2), Building Energy (1), Hydrology/Water (8),
  Geospatial (7), Data Catalog (1).
- New `_ADDON_NODE_REGISTRY` separate from `_USER_NODE_REGISTRY`; loaded at
  startup before user packages.
- `discover_addon_nodes()`, `get_all_addon_nodes()`, `get_addon_node_groups()`
  added to `node_package_loader`.
- Palette gains a **─── Scientific & Engineering ───** section between the
  built-in and custom-node sections.
- Node toolbar gains a **48 px** gap before the add-on and custom sections;
  built-in super-groups are separated by **32 px** transparent spacers.
- Node Type Library dialog now has four tabs: Built-in, Scientific & Engineering,
  Installed Custom, ⚠ Errors.

**Documentation**
- `tutorials/custom_nodes.md`: multi-file packages, installation of folders,
  4-tab Node Type Library, updated load-order section, sharing multi-file packages.
- `context/palette.md`: full three-section palette reference with node tables.
- `docs/11_developer_guide.md`: node package system architecture, add-on node
  conventions, toolbar super-group implementation note.

### Fixed
- `QWidget` missing from `QWidgets` import block in `app/main.py` caused
  `NameError` at startup when building the node toolbar spacers.
- Toolbar gap spacers now use `setFixedSize(width, height)` instead of
  `setFixedWidth` alone — Qt's toolbar layout engine collapses widgets that have
  no explicit height to zero, making the gaps invisible.

---

## [0.2.0] — 2026-05-28 (node expansion II)

### Added — 19 new node types with custom icons (2026-05-28)
- 19 `NodeTypeDefinition` entries added, growing the palette from 64 to **83 node types**
- Custom QPainter icon for every new type; zero fallback-initials in the palette
- `quick_ref.md` extended with full property tables and usage guidance for all 19 new types
- README node-type list updated to reflect all 83 types across all 19 categories

#### New node types by category

**System / Shell / Hardware** — Shell Command (bash/sh/zsh/powershell/cmd + `auto`
platform detection), TTY Serial (Arduino/MCU serial port), Spreadsheet
(CSV/TSV/Excel with delimiter, quoting, sheet name, header row, and encoding controls)

**Networking / Sockets** — Socket (TCP/UDP, stateful object in shared store),
WebSocket (async ws:// / wss://), Webhook Trigger (wait for inbound HTTP POST)

**AI / LLM Utilities** — Context Compact (strategy pattern: truncate / sliding_window
/ summarize / extractive / semantic_dedup), Conversation History (append/trim/clear/format)

**Text / Data Processing** — Regex (match/search/findall/replace/split), Template Render
(Jinja2 inline or file), JSON Parse (parse ↔ serialize), List Operations
(filter/sort/slice/unique/flatten/reverse/count), String Operations
(split/join/strip/upper/lower/replace/format/truncate)

**Resilience / Flow Utilities** — Retry (exponential backoff + jitter, configurable
max attempts), Rate Limiter (per-minute throttle, labelled for multi-endpoint flows)

**Messaging / Notifications** — Email Send (SMTP/SendGrid/Mailgun), Email Read (IMAP/Gmail),
Notification (Slack/Discord/Teams/Telegram via webhook)

**Security / Configuration** — Secret (env variable, .env file, AWS Secrets Manager,
HashiCorp Vault)

---

## [0.2.0] — 2026-05-28 (node expansion)

### Added — 44 new node types with custom icons (2026-05-28)
- 44 `NodeTypeDefinition` entries added to `BUILTIN_NODE_TYPES`, growing the palette from 20 to 64
  node types across 12 new categories
- Custom QPainter icon function for every new node type — no fallback initials; all 64 palette
  entries have purpose-drawn icons with unique, semantically meaningful shapes
- `quick_ref.md` expanded with full property tables and usage guidance for all 44 new types
- README node-type list updated to reflect all 64 types across all categories

#### New node types by category

**AI / Reasoning** — Chain of Thought, Majority Vote, Supervisor, Debate Advocate, Debate Judge

**Web / Search** — Web Search, Web Scrape, API Call

**Data / Vector** — Text Chunk, Embed, Vector Index, Vector Retrieve

**Database / SQL** — DB Schema, NL to SQL, SQL Execute

**Voice / Audio** — Speech to Text, Text to Speech

**Document / Vision** — PDF Extract, Image Vision, Data Validate

**Code / Execution** — Code Gen, Code Exec, Test Gen

**Data Processing** — Map, Reduce, Condition, Loop Counter, Transform, Merge

**Calendar** — Calendar Read, Calendar Write

**MCP / Agent Protocol** — MCP Tool, A2A Send, A2A Receive

**Observability / Utility** — Log, Timer, Cache, Trace

**Data Structures / Memory** — Registry, Stack Push, Stack Pop, Queue Enqueue, Queue Dequeue, Local Memory

---

## [0.2.0] — 2026-05-27 / 2026-05-28

### Added — Toolbar overflow and Customize Toolbar dialog (2026-05-28)
- Node-palette toolbar now uses `QToolBar.addAction()` instead of `addWidget(QToolButton)` —
  Qt's built-in overflow extension button (`>>`) appears automatically when the toolbar is too
  narrow to show all icons
- Right-click the toolbar → **Customize Toolbar…** opens a modal dialog with icons, ↑/↓ reorder
  buttons, and a Reset Default option
- Custom toolbar order is persisted in `QSettings` under `ui/toolbar/node_palette_order` and
  restored on next launch; new node types added to `BUILTIN_NODE_TYPES` are automatically
  appended at the end of any saved order

### Added — Node right-click context menu (2026-05-28)
- Right-clicking a canvas node now shows a full context menu: **Open Code**, **Rename**,
  **Toggle Breakpoint** (F9), **Duplicate**, **Delete** (Del), and **Set as Start Node**
- Each action uses the existing signal/handler infrastructure; Rename uses `QInputDialog`;
  Duplicate offsets the new node by 30 px and pushes an undo command

### Changed — Flow menu cleanup (2026-05-28)
- Removed the dead **Flow > Set Start Node** menu item; right-click context menu handles it

### Added — Actions / Reads / Writes documentation (2026-05-28)
- Expanded the "Actions, Reads, and Writes" concept across all help files — context inspector
  help, quick reference, getting started, your first flow, and Tutorial 3 in part 1 — with
  code examples, lifecycle tables, and mapping diagrams so the concepts are reinforced
  across multiple reading paths

### Added — M15 Boy Scout refactoring (T-R01 – T-R47) (2026-05-28)
- 47 targeted code-quality improvements: `ImportError` guards on all Qt fallback blocks,
  `TYPE_CHECKING` pattern for Qt type hints, `@staticmethod` on pure helpers,
  `_NodeCtx` TypedDict, explicit `.endswith(".pfcgraph.yaml")` stem extraction,
  `__all__` exports in `generation/`, `validation/`, and `runtime/` packages,
  palette/toolbar sourced from `BUILTIN_NODE_TYPES`, clarifying comment in
  `GraphSnapshotCommand.redo`, and miscellaneous method and docstring improvements

### Added — Getting to Know Nodes tutorial series (2026-05-28)
- 7-file tutorial series (`gtkn_index.md` + 6 part files) covering all 20 built-in node types
  through hands-on mini-flows, progressing simplest → most complex
- Part 1: Start, Stop, Basic — foundation lifecycle and shared store
- Part 2: File Reader, File Writer, Python Tool — I/O and @tool functions
- Part 3: Router, Human Review, Human Input — flow control and human-in-the-loop
- Part 4: LLM Prompt, JSON LLM, Classifier, Judge — LLM integration patterns
- Part 5: Batch, Async, Async Batch, Async Parallel Batch — batch and async execution
- Part 6: RAG, Agent, Subflow — advanced patterns
- `Help > Getting to Know Nodes` menu item added; opens `tutorials/gtkn_index.md`

## [0.2.0] — 2026-05-27 (base)

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
