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
| **Reads** | **Yes** | Shared-store keys this node reads in `prep()` — documents the node's data contract |
| **Writes** | **Yes** | Shared-store keys this node writes in `post()` — documents the node's data contract |

**Custom type properties** appear below the standard fields when a node type is selected.
Properties with a fixed set of allowed values (e.g., `prompt_type`) are shown as a
**drop-down selector**; all other properties use a text field.

---

## Understanding Actions, Reads, and Writes

These three fields define the **data contract** of a node — what it needs, what it
produces, and which path it takes next. Together they are the most important metadata
you can give a node.

### Actions — "Which way do I go next?"

When a node finishes, its `post()` method returns a **string**. That string is the
**action**. PocketFlow looks up the outgoing edge whose label matches that string and
follows it to the next node.

```
post() returns "approved"
    ↓
graph follows the "approved" edge
    ↓
next node runs
```

**Actions** in the Inspector is the comma-separated list of strings this node's
`post()` might return. The validator checks that every outgoing edge label matches
one of these declared actions — if you wire an edge labelled `"success"` but the
node only declares `"default"`, you get error PFCE2101.

**Examples:**
- Simple linear node: `default`
- Binary gate: `approved, rejected`
- Classifier: `positive, negative, neutral`
- Agent loop: `done, continue`

> **Tip:** Declare every action before drawing edges. The canvas creates edge labels
> automatically from the output port you drag from, so your declared actions become
> clickable ports on the right side of the node tile.

### Reads — "What do I take from the shared store?"

The **shared store** is a plain Python `dict` that every node in the flow can see.
It is the only way data moves between nodes. When a node needs data produced by an
earlier node, its `prep()` method reads it from the shared store:

```python
def prep(self, shared: dict) -> str:
    return shared["user_input"]   # <-- reads "user_input" from the store
```

**Reads** in the Inspector documents which keys this node's `prep()` pulls from the
store. This is **documentation only — not enforced at runtime** — but it is invaluable:

- The **Data Flow Report** (Project > Data Flow Report) uses Reads declarations to show
  the full key lifecycle: who writes a key, who reads it, and whether any node reads a
  key that nobody writes.
- When you look at a graph cold, clicking a node and seeing `reads: user_input` tells
  you instantly what that node depends on — without opening the code editor.

### Writes — "What do I put back into the shared store?"

After doing its work, a node's `post()` method writes results back into the shared store
so downstream nodes can use them:

```python
def post(self, shared: dict, prep_res, exec_res: str) -> str:
    shared["llm_response"] = exec_res   # <-- writes "llm_response" into the store
    return "default"
```

**Writes** in the Inspector documents which keys this node's `post()` puts into the
store. Like Reads, this is **documentation only**, but it feeds the Data Flow Report and
makes the graph self-describing.

### The Full Picture

```
INSPECTOR FIELD    MAPS TO         WHAT IT DOES
─────────────────  ──────────────  ───────────────────────────────────────────
Reads              prep(shared)    Pull inputs from the shared store
                                   (documents what this node depends on)

Writes             post(shared)    Push outputs into the shared store
                                   (documents what this node produces)

Actions            return value    Choose the next node to execute
                   of post()       (validated against outgoing edge labels)
```

All three together make a node's contract explicit and visible on the canvas — no code
reading required to understand what a node does, needs, or produces.

---

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
