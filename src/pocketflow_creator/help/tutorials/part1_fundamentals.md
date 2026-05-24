# Part 1 — Getting Started with PocketFlow Creator

Work through these six tutorials in order. They cover every panel and every core
workflow you'll use in later tutorials.

[← Tutorials Index](index.md)

---

## Tutorial 1: IDE Tour

**What you'll learn:** The six panels of the PocketFlow Creator IDE and what each one does.

**Prerequisites:** App launched (`python -m pocketflow_creator` or `pocketflow-creator`).

### The Six Panels

```
┌──────────────────────────────────────────────────────────────────┐
│  Menu Bar: File  Edit  View  Project  Flow  Node  Run  Tools     │
├──────────────┬───────────────────────────────┬───────────────────┤
│              │                               │                   │
│  Project     │       Graph Canvas            │  Object           │
│  Explorer    │  (drag nodes here, wire       │  Inspector        │
│  (left dock) │   edges between ports)        │  (right dock)     │
│              │                               │                   │
├──────────────┤                               │  Component        │
│  Component   │                               │  Palette          │
│  Palette     │                               │  (drag sources)   │
│  (left dock) │                               │                   │
│              ├───────────────────────────────┴───────────────────┤
│              │  Python | Markdown | YAML | Run Log | Shared Store│
│              │  Test Results | Prompt Preview | Generated Code    │
└──────────────┴───────────────────────────────────────────────────┘
```

| Panel | Purpose |
|---|---|
| **Project Explorer** | Tree view of the loaded project — graphs, prompts, node types, tools |
| **Component Palette** | Drag-and-drop source for all built-in node types and snippets |
| **Graph Canvas** | Visual editor — nodes, edges, ports; your flow lives here |
| **Object Inspector** | Property editor for the selected node or edge |
| **Bottom tabs** | Code editor, run output, shared store view, test results |
| **Status bar** | Current operation and validation feedback |

### Quick Reference: Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| New project | Ctrl+N |
| Open project | Ctrl+O |
| Save | Ctrl+S |
| Save all | Ctrl+Shift+S |
| Export project | Ctrl+E |
| Validate | Ctrl+Shift+V |
| Run active flow | F5 |
| Debug active flow | Shift+F5 |
| Toggle breakpoint | F9 |
| Zoom to fit | Ctrl+0 |
| Auto layout | Ctrl+Shift+L |

---

## Tutorial 2: Your First Flow — Hello World

**What you'll learn:** Create a project, add nodes, wire them, edit properties, and run.

**Prerequisites:** Tutorial 1.

### Steps

1. **Create a project**
   - File > New Project…
   - Name: `hello_world`, location: any folder
   - Click **Create**

2. **Open the graph**
   - In Project Explorer, double-click `graphs/main.pfcgraph.yaml`
   - The canvas appears (empty)

3. **Add a Start node**
   - In Component Palette, drag **Start Node** onto the canvas
   - A blue-bordered node labelled "Start Node" appears
   - Single-click it to select it
   - In Object Inspector, change **Title** to `Start`

4. **Add an LLM Prompt node**
   - Drag **LLM Prompt Node** from the palette onto the canvas, to the right of Start
   - Single-click it; set **Title** to `Ask LLM`
   - Set **prompt_file** to `prompts/hello.md`

5. **Add a Stop node**
   - Drag **Stop Node** to the right of Ask LLM
   - Set **Title** to `End`

6. **Auto-layout** (optional, to tidy positions)
   - View > Auto Layout (Ctrl+Shift+L)
   - View > Zoom to Fit (Ctrl+0)

7. **Create the prompt file**
   - Open the **Markdown** tab at bottom, type: `Say hello to the world in one sentence.`
   - Save (Ctrl+S) to `prompts/hello.md`

8. **Validate the graph**
   - Project > Validate Project (Ctrl+Shift+V)
   - Problems tab shows any errors

9. **Run with mock provider**
   - Run > Run Active Flow (F5)
   - Check **Run Log** tab — you'll see one step per node

**Expected result:** Three nodes on canvas, no error badges, run log shows Start → Ask LLM → End.

---

## Tutorial 3: Using the Properties Inspector

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
3. Change **Reads** to `user_input`
4. Change **Writes** to `llm_response`

Notice how the canvas updates live — action changes may trigger validation badges if wired edges don't match the new action names.

### Edge Properties

Click an edge (the line between two nodes) to see:
- **Action** — the label on this transition (must match a declared action on the source node)

---

## Tutorial 4: The Code Editor — RAD Node Coding

**What you'll learn:** How double-clicking a node opens its implementation in the code editor, and how to write real node logic.

**Prerequisites:** Tutorial 2 — an open project with nodes on the canvas.

### How the Code File Works

Every graph has a companion code file at `code/<graph_stem>.py`.
When you **double-click a node** on the canvas:
1. The file is created if it doesn't exist
2. A class stub is added for that node (if not already there)
3. The **Python** tab opens and scrolls to that node's class

### Steps

1. Open the project from Tutorial 2
2. Double-click the **Ask LLM** node on the canvas
3. The Python tab opens, showing:

```python
# --- NODE_START: node_abc12345 ---
class AskLlm(Node):
    """llm_prompt_node: Ask LLM"""

    def prep(self, shared: dict) -> object:
        return None

    def exec(self, prep_res: object) -> object:
        return None

    def post(self, shared: dict, prep_res: object, exec_res: object) -> str:
        return "default"

# --- NODE_END: node_abc12345 ---
```

4. Edit the stub to implement real logic:

```python
# --- NODE_START: node_abc12345 ---
class AskLlm(Node):
    """llm_prompt_node: Ask LLM"""

    def prep(self, shared: dict) -> str:
        prompt_path = shared.get("prompt_file", "prompts/hello.md")
        with open(prompt_path) as f:
            return f.read()

    def exec(self, prep_res: str) -> str:
        llm = shared.get("llm")
        return llm.complete(prep_res) if llm else f"[mock] {prep_res}"

    def post(self, shared: dict, prep_res: str, exec_res: str) -> str:
        shared["llm_response"] = exec_res
        print(exec_res)
        return "default"

# --- NODE_END: node_abc12345 ---
```

5. Save (Ctrl+S)

### Deleting a Node

- Select a node on the canvas
- Press **Delete** key
- The node is removed from the canvas AND its class is removed from `code/main.py`

---

## Tutorial 5: Creating a Custom Node Type

**What you'll learn:** Use the Node Wizard to define a reusable node type with custom properties.

**Prerequisites:** Tutorial 2.

### Steps

1. Node > New Custom Node Type…
2. Fill in the wizard:
   - **Node Type ID:** `sentiment_node`
   - **Display Name:** Sentiment Analyser
   - **Category:** Analysis
   - **Base Class:** `Node`
   - **Actions:** `positive`, `negative`, `neutral`
3. Add a property:
   - Click **Add Property**
   - Name: `threshold`, Type: `number`, Default: `0.5`
4. Click **Create**

The wizard writes two files:
- `node_types/sentiment_node.yaml` — the type definition
- `custom/sentiment_node.py` — a Python skeleton

5. Open `custom/sentiment_node.py` from Project Explorer and implement the logic:

```python
class SentimentNode(Node):
    def prep(self, shared):
        return shared.get("text", "")

    def exec(self, prep_res):
        text = prep_res.lower()
        if any(w in text for w in ["great", "love", "excellent"]):
            return "positive"
        elif any(w in text for w in ["bad", "hate", "terrible"]):
            return "negative"
        return "neutral"

    def post(self, shared, prep_res, exec_res):
        shared["sentiment"] = exec_res
        return exec_res  # routes to "positive", "negative", or "neutral" edge
```

6. The **Sentiment Analyser** now appears in the Component Palette under "Analysis"
7. Drag it onto a canvas and wire three outgoing edges labelled `positive`, `negative`, `neutral`

---

## Tutorial 6: Project Templates

**What you'll learn:** Start a new project from a built-in template instead of from scratch.

**Prerequisites:** None.

### Steps

1. File > New From Template…
2. Select **Simple LLM Flow**
3. Choose a folder, enter a project name, click **Create**

The template creates:
- `graphs/main.pfcgraph.yaml` — Start → LLM Prompt → Stop
- `prompts/main.md` — placeholder prompt
- `project.pfcproj.yaml` — configured project file

4. Open the graph, run Auto Layout, and explore the pre-wired nodes
5. Edit `prompts/main.md` to write your own instruction
6. Run > Run Active Flow to test with the mock provider

---

[→ Continue to Part 2 — PocketFlow Patterns](part2_patterns.md)
