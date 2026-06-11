# Tutorial 3: Using the Properties Inspector

**What you'll learn:** Every field in the Object Inspector and how edits sync live to the graph.

**Prerequisites:** Tutorial 2 — a project with at least one node.

### Node Properties

Click any node to see its properties in the inspector:

| Field | Editable | Purpose |
|---|---|---|
| **ID** | No | Unique internal identifier (auto-generated) |
| **Type** | No | Node type from the palette |
| **Title** | **Yes** | Display name shown on the canvas |
| **Position X/Y** | No | Canvas coordinates (drag to reposition) |
| **Actions** | **Yes** | Comma-separated list of output action names |
| **Reads** | **Yes** | Shared-store keys this node reads (documentation) |
| **Writes** | **Yes** | Shared-store keys this node writes (documentation) |

**Blue value fields** are editable — click once to enter edit mode, type the new value, press Enter or click away.

### Editing in Practice

1. Select the **Ask LLM** node
2. Change **Actions** to `success, failure`
   - The validator now expects edges with labels `success` or `failure` leaving this node
3. Change **Reads** to `user_input`
4. Change **Writes** to `llm_response`

Notice how the canvas updates live (title changes show immediately; action changes may trigger validation badges if wired edges don't match).

### Edge Properties

Click an edge (the line between two nodes) to see:
- **Action** — the label on this transition (must match a declared action on the source node)

---
