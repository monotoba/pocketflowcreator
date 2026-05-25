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

**Custom type properties** appear below the standard fields when a node type is selected.
Properties with a fixed set of allowed values (e.g., `prompt_type`) are shown as a
**drop-down selector**; all other properties use a text field.

## LLM Node Prompt Properties

| Property | Values | Description |
|---|---|---|
| `prompt_type` | `string` / `path` | How `prompt_file` is interpreted |
| `prompt_file` | any text | Literal prompt text (when `prompt_type = string`) or relative file path (when `prompt_type = path`) |

Setting `prompt_type = string` lets you type the prompt directly into the Inspector without
creating a separate file. Setting `prompt_type = path` reads the prompt from a Markdown
file at runtime — useful for long, reusable, or version-controlled prompts.

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
