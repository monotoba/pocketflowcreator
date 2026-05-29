# Component Palette

The Component Palette lists every node type available for dragging onto the canvas.
It is divided into three sections, each separated by a labelled divider.

---

## Section 1 — Built-in Nodes

The built-in nodes ship with PocketFlow Creator and are always available.
They are grouped by category inside the palette.

| Category | Node types |
|---|---|
| **Flow Control** | Start, Stop, Router, Subflow |
| **Core / General** | Basic Node, Python Tool |
| **AI / LLM** | LLM Prompt, JSON LLM, Classifier, Agent, RAG, Judge |
| **AI / Reasoning** | Chain of Thought, Majority Vote, Supervisor, Debate Advocate, Debate Judge |
| **AI / LLM Utilities** | Context Compact, Conversation History |
| **Human-in-the-Loop** | Human Review, Human Input |
| **Data / IO** | File Reader, File Writer |
| **Data Processing** | JSON Parse, List Operations, String Operations, Regex, Template Render |
| **Data / Vector** | Vector Store, Embedding |
| **Data Structures / Memory** | Key-Value Store, Sliding Window Memory |
| **Code / Execution** | Code Executor, Python REPL |
| **Processing / Async** | Batch, Async, Async Batch, Async Parallel Batch |
| **Web / Search** | HTTP Request, Web Scrape, Web Search |
| **Database / SQL** | SQL Query |
| **Voice / Audio** | Speech-to-Text, Text-to-Speech |
| **Document / Vision** | PDF Reader, Image Analyser |
| **Calendar** | Calendar Event |
| **MCP / Agent Protocol** | MCP Tool Call |
| **Observability / Utility** | Logger, Timer, Counter |
| **System / Shell** | Shell Command, TTY Serial, Spreadsheet |
| **Networking** | Socket, WebSocket, Webhook Trigger |
| **Resilience** | Retry, Rate Limiter |
| **Messaging** | Email Send, Email Read, Notification |
| **Security** | Secret |

---

## Section 2 — Scientific & Engineering Add-on Nodes

These 34 domain-specific nodes ship with Creator in `addon_nodes/` and appear under the
**─── Scientific & Engineering ───** divider.  They are grouped by domain.

| Domain | Node types |
|---|---|
| **Geospatial** | USGS Elevation Point, USGS 3DEP Elevation, National Map Download, Earthquake Catalog, Landsat Search & Download, ShakeMap Fetch, ShakeMap Scenario |
| **Hydrology / Water** | USGS Water Data, NWIS Query, StreamStats Basin, SWMM Run, EPANET Run, MODFLOW 6 Run, FloPy Model, pyWatershed |
| **Weather / Atmosphere** | NOAA Weather, WRF Model |
| **Building Energy** | EnergyPlus Run |
| **Aerospace — CFD & Geometry** | Open VSP Geometry, VSPAERO Analysis, SU2 CFD, Cart3D Analysis, FUN3D Run |
| **Aerospace — Propulsion & MDO** | NASA CEA, RocketPy Flight, GMAT Script, OpenMDAO Model, Optimization, NASA Trick Simulation |
| **Wind Energy** | OpenFAST, KiteFAST |
| **Scientific Computing** | MATLAB Engine, Octave Script |
| **Data Catalog** | USGS Data Catalog Search |

For full property documentation see the [Node Reference](../quick_ref.md#addon-nodes--geospatial).
For hands-on tutorials see [GTKN Parts 20–25](../tutorials/gtkn_index.md).

---

## Section 3 — Custom Nodes

User-installed node packages appear under the **─── Custom Nodes ───** divider,
grouped by category.  Install packages via **Tools → Node Type Library → Install node package…**.

See [Creating Custom Nodes](../tutorials/custom_nodes.md) for how to write and install your own packages.

---

## Using the Palette

1. Find the node type by scrolling or scanning the category groups.
2. Click and hold on a node type.
3. Drag it onto the **Graph Canvas**.
4. Release — the node appears at the drop position.
5. Click the new node to select it and edit its properties in the **Object Inspector**.

> **Tip:** Node types also appear as icon buttons in the **Node toolbar** across the top of the window.  Click any icon to drop that node at the centre of the current canvas view.

---

## Node Lifecycle

Every node follows the `prep → exec → post` lifecycle:

```
shared store → prep(shared) → exec(prep_res) → post(shared, prep_res, exec_res) → action string
```

The action string returned by `post()` determines which edge to follow next.

[← Help Index](../index.md) | [Canvas Help](canvas.md)
