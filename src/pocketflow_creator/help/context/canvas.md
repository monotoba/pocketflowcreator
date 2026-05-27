# Graph Canvas

The canvas is the central panel where you visually design your PocketFlow workflow.

![PocketFlow Creator canvas and panels](../img/main_window.png)

## Basic Operations

| Operation | How |
|---|---|
| **Add a node** | Drag a node type from the Component Palette and drop it on the canvas |
| **Select a node** | Click once — properties appear in the Object Inspector |
| **Move a node** | Click and hold, then drag to a new position |
| **Delete a node** | Select it; press the **Delete** key |
| **Open code** | **Double-click** a node to open its class in the Python editor |
| **Connect nodes** | Hover over the source node until action ports appear; drag from a port to a target node |
| **Select an edge** | Click the line between two nodes |
| **Delete an edge** | Select the edge; press the **Delete** key |

## Navigation

| Action | How |
|---|---|
| **Zoom in/out** | Ctrl+Scroll wheel, or Ctrl++ / Ctrl+- |
| **Pan** | Middle-drag or Space-drag |
| **Zoom to Fit** | View > Zoom to Fit (Ctrl+0) |
| **Zoom to selected node** | Ctrl+Shift+Z |
| **Auto Arrange…** | View > Auto Arrange… (Ctrl+Shift+L) — opens settings dialog before running |

## Auto Arrange

**View > Auto Arrange…** (Ctrl+Shift+L) opens a settings dialog before rearranging the canvas.

| Setting | Options |
|---|---|
| **Algorithm** | Layered BFS, Grid, Force-directed (spring-embedder) |
| **Connector style** | Straight, Curved (quadratic Bezier), Orthogonal (right-angle) |
| **H Gap / V Gap** | Horizontal and vertical spacing between nodes |
| **Max Cols** | Maximum columns (used by the Grid algorithm) |

Settings are persisted per-project in the `.pfcproj.yaml` file under `auto_arrange:`. The operation is fully undoable with Ctrl+Z.

## Undo / Redo

| Action | Shortcut |
|---|---|
| **Undo** | Ctrl+Z |
| **Redo** | Ctrl+Y |

Undo covers: add node, delete node/edge, add edge, edit property, change edge action, move node, and Auto Arrange. The undo stack clears when a project is opened or created.

## Node Anatomy

Each node shows:
- **Title** — the display name (editable in Inspector)
- **Type badge** — the node type (e.g., `llm_prompt_node`)
- **Action ports** — right-side ellipses, one per declared action
- **Input port** — left-side ellipse; receives incoming edges
- **Red border** — validation error; check Problems tab

## Breakpoints

- Select a node, then Node > Toggle Breakpoint (F9)
- A red dot appears in the node's corner
- Debug mode (Shift+F5) pauses when this node is about to execute

## Code Sync

Every node has a corresponding class in `code/<graph_stem>.py`.
When you delete a node from the canvas, its class block is removed from the code file.

[← Help Index](../index.md) | [Inspector Help](inspector.md) | [Palette Help](palette.md)
