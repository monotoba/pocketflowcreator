# Object Inspector

The Object Inspector (right panel) displays and edits properties of the selected node or edge.

## Node Properties

| Field | Editable | Description |
|---|---|---|
| **ID** | No | Unique internal identifier — auto-generated, never changes |
| **Type** | No | Node type from the palette (e.g., `llm_prompt_node`) |
| **Title** | **Yes** | Display name shown on the canvas |
| **Position X / Y** | No | Canvas coordinates — drag the node to reposition |
| **Actions** | **Yes** | Comma-separated output action names (e.g., `default` or `yes, no, maybe`) |
| **Reads** | **Yes** | Shared-store keys this node reads — documentation only, not enforced |
| **Writes** | **Yes** | Shared-store keys this node writes — documentation only, not enforced |

**Custom type properties** (e.g., `prompt_file`, `subflow_ref`) appear below the standard fields
when a custom node type is loaded.

## How to Edit a Field

1. Click the **blue value cell** in the Value column
2. The cell enters edit mode
3. Type the new value and press **Enter** — or click elsewhere to commit
4. Changes sync to the graph model immediately; validation re-runs automatically

## Edge Properties

Click an edge (the line between two nodes) to see:
- **Action** — the label on this transition; must match a declared action on the source node

## Validation Feedback

When you change a field that affects validation (e.g., Actions), the canvas re-validates
immediately. Nodes with errors gain a red border; the Problems tab shows details.

[← Help Index](../index.md) | [Canvas Help](canvas.md)
