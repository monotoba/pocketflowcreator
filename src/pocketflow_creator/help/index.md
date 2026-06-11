# PocketFlow Creator Help

Welcome to PocketFlow Creator — the RAD visual designer for building LLM workflows with
the [PocketFlow](https://github.com/The-Pocket/PocketFlow) framework.

![PocketFlow Creator main window](img/main_window.png)

---

## Getting Started

| Topic | Description |
|---|---|
| [Getting Started](getting_started.md) | Installation, first launch, and IDE overview |
| [Your First Flow](your_first_flow.md) | Build and run a Hello World flow step-by-step |
| [About PocketFlow](about_pocketflow.md) | What PocketFlow is and how it works |
| [About PocketFlow Creator](about_pocketflow_creator.md) | Architecture and design principles |

---

## Tutorials

| Tutorial Set | Topics |
|---|---|
| [Part 1 — Fundamentals](tutorials/part1_fundamentals.md) | IDE Tour, First Flow, Inspector, Code Editor, Custom Nodes, Templates |
| [Part 2 — PocketFlow Patterns](tutorials/part2_patterns.md) | Hello World, Chat, Structured Output, Routing, Agent, RAG, Batch, HITL, Judge, Multi-Agent, Streaming, Memory |
| [Part 3 — Advanced Features](tutorials/part3_advanced.md) | Validation, Debug, Subflows, Export, Shared Store, Packaging |
| [**Creating Custom Nodes**](tutorials/custom_nodes.md) | GUI wizard + external `.py` node packages; installing, sharing, testing |
| [**Resilience Patterns**](tutorials/resilience_failover.md) | Provider Failover: multi-provider fallback, error-specific retries, session recovery |
| [Part 4 — Exercises](tutorials/part4_exercises.md) | News Summariser, Coding Agent, Multi-Provider Router, Full IDE Workout |

See the [Tutorials Index](tutorials/index.md) for a full list.

---

## Getting to Know Nodes — Node-by-Node Tutorial Series

A 25-part series with one hands-on mini-flow per node type — all 83 built-in nodes
plus all 34 addon nodes. Start at Part 1 and work forwards.

| Parts | Coverage |
|---|---|
| [Parts 1–19](tutorials/gtkn_index.md) | All 83 built-in nodes (Flow Control → Security) |
| [Part 20 — Geospatial](tutorials/gtkn_part20.md) | USGS Elevation, 3DEP, National Map, Earthquake Catalog, Landsat, ShakeMap |
| [Part 21 — Hydrology](tutorials/gtkn_part21.md) | USGS Water Data, NWIS, StreamStats, SWMM, EPANET, MODFLOW, FloPy, pyWatershed |
| [Part 22 — Weather & Building Energy](tutorials/gtkn_part22.md) | NOAA Weather, WRF Model, EnergyPlus |
| [Part 23 — Aerospace CFD](tutorials/gtkn_part23.md) | Open VSP, VSPAERO, SU2, Cart3D, FUN3D |
| [Part 24 — Aerospace Propulsion & MDO](tutorials/gtkn_part24.md) | NASA CEA, RocketPy, GMAT, OpenMDAO, Optimization, NASA Trick |
| [Part 25 — Wind Energy, Sci. Computing & Data](tutorials/gtkn_part25.md) | OpenFAST, KiteFAST, MATLAB Engine, Octave Script, USGS Data Catalog |

[→ Open Series Index](tutorials/gtkn_index.md)

---

## Context Help

Context help is available in every dialog via the **?** button.
You can also browse topics directly:

| Panel / Dialog | Help |
|---|---|
| Graph Canvas | [canvas.md](context/canvas.md) |
| Object Inspector | [inspector.md](context/inspector.md) |
| Component Palette | [palette.md](context/palette.md) |
| Project Explorer | [explorer.md](context/explorer.md) |
| Options | [options.md](context/options.md) |
| Provider Manager | [provider_manager.md](context/provider_manager.md) |
| Shared Store Designer | [shared_store.md](context/shared_store.md) |
| Node Type Wizard | [node_type_wizard.md](context/node_type_wizard.md) |
| Code Editor | [code_editor.md](context/code_editor.md) |
| Run Log | [run_log.md](context/run_log.md) |
| Validation | [validation.md](context/validation.md) |

---

## Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| New project | Ctrl+N |
| Open project | Ctrl+O |
| Save | Ctrl+S |
| Save all | Ctrl+Shift+S |
| Undo | Ctrl+Z |
| Redo | Ctrl+Y |
| Generate code | Ctrl+G |
| Validate | Ctrl+Shift+V |
| Auto Arrange… | Ctrl+Shift+L |
| Run active flow | F5 |
| Debug active flow | Shift+F5 |
| Toggle breakpoint | F9 |
| Zoom in | Ctrl++ |
| Zoom out | Ctrl+- |
| Zoom to fit | Ctrl+0 |
| Zoom to selected node | Ctrl+Shift+Z |
| Delete selected node/edge | Delete |
| Help | F1 |
