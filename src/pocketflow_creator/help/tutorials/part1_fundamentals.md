# Part 1 — Getting Started with PocketFlow Creator

Work through these tutorials in order. They cover every panel and every core
workflow you'll use in later tutorials.

[← Tutorials Index](index.md)

---

## Tutorial 0: Hello LLM

**What you'll learn:** Make your first real LLM call from a PocketFlow node — plain
text first, then structured JSON — and configure four different LLM providers.

**Prerequisites:** None. You do not need an open project; you can run this code directly
from a terminal once you have chosen a provider.

---

### Part A — Plain Text Response

The simplest possible flow asks the LLM for a specific string and prints it.

#### Graph

```
[Start] --default--> [HelloLlm] --default--> [Stop]
```

#### Node code

```python
class HelloLlm(Node):
    def prep(self, shared: dict) -> str:
        return 'Reply with exactly this text and nothing else: LLM says: Hello User'

    def exec(self, prep_res: str) -> str:
        return call_llm(prep_res)

    def post(self, shared: dict, prep_res: str, exec_res: str) -> str:
        shared["message"] = exec_res
        print(exec_res)          # → LLM says: Hello User
        return "default"
```

**Expected output:**
```
LLM says: Hello User
```

---

### Part B — Structured JSON Response

Now modify the node to instruct the LLM to respond with a JSON object.
The `exec()` method parses the response so the rest of the flow gets a dict,
not a raw string.

#### Node code

```python
import json

class HelloLlm(Node):
    def prep(self, shared: dict) -> str:
        return (
            'Respond with ONLY valid JSON — no markdown, no extra text.\n'
            'Use exactly this structure: {"message": "LLM says: Hello User"}'
        )

    def exec(self, prep_res: str) -> dict:
        raw = call_llm(prep_res)
        # Strip accidental markdown fences if the model adds them
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)

    def post(self, shared: dict, prep_res: str, exec_res: dict) -> str:
        shared["result"] = exec_res
        print(exec_res["message"])   # → LLM says: Hello User
        return "default"
```

**Expected output:**
```
LLM says: Hello User
```

The value at `shared["result"]` is now a Python dict:
```python
{"message": "LLM says: Hello User"}
```

---

### Part C — Configuring an LLM Provider

Replace the `call_llm` stub below with the provider you want to use.
Put this function at the top of your code file (outside the node class).

---

#### Option 1 — Ollama (local, free)

[Ollama](https://ollama.com) runs open-source models on your own machine.
No API key required.

**Install and pull a model:**
```bash
# Install Ollama from https://ollama.com, then:
ollama pull llama3.2          # ~2 GB, fast on CPU
# or
ollama pull mistral           # good alternative
```

**PocketFlow provider code:**
```python
import json
import urllib.request

def call_llm(prompt: str, model: str = "llama3.2") -> str:
    url = "http://localhost:11434/api/generate"
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["response"].strip()
```

**In PocketFlow Creator:**
- Tools > Provider Manager
- Set **Provider** to `Ollama`
- Set **Base URL** to `http://localhost:11434`
- Set **Model** to `llama3.2` (or whichever you pulled)

---

#### Option 2 — OpenAI API

```bash
pip install openai
```

```python
from openai import OpenAI

_client = OpenAI(api_key="sk-...")   # or set OPENAI_API_KEY env var

def call_llm(prompt: str, model: str = "gpt-4o-mini") -> str:
    response = _client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()
```

**Common models:** `gpt-4o-mini` (fast, cheap), `gpt-4o` (flagship).

**In PocketFlow Creator:**
- Tools > Provider Manager
- Set **Provider** to `OpenAI`
- Paste your API key (or set `OPENAI_API_KEY` in your shell before launching)
- Set **Model** to `gpt-4o-mini`

---

#### Option 3 — Anthropic Claude API

```bash
pip install anthropic
```

```python
import anthropic

_client = anthropic.Anthropic(api_key="sk-ant-...")  # or ANTHROPIC_API_KEY env var

def call_llm(prompt: str, model: str = "claude-haiku-4-5-20251001") -> str:
    message = _client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
```

**Common models:** `claude-haiku-4-5-20251001` (fast), `claude-sonnet-4-6` (balanced),
`claude-opus-4-7` (most capable).

**In PocketFlow Creator:**
- Tools > Provider Manager
- Set **Provider** to `Claude`
- Paste your Anthropic API key (or set `ANTHROPIC_API_KEY`)
- Set **Model** to `claude-haiku-4-5-20251001`

---

#### Option 4 — Google Gemini API

```bash
pip install google-generativeai
```

```python
import google.generativeai as genai

genai.configure(api_key="AIza...")   # or GOOGLE_API_KEY env var
_model = genai.GenerativeModel("gemini-1.5-flash")

def call_llm(prompt: str) -> str:
    response = _model.generate_content(prompt)
    return response.text.strip()
```

**Common models:** `gemini-1.5-flash` (fast, free tier available),
`gemini-1.5-pro` (more capable).

**In PocketFlow Creator:**
- Tools > Provider Manager
- Set **Provider** to `Gemini`
- Paste your Google AI Studio API key (or set `GOOGLE_API_KEY`)
- Set **Model** to `gemini-1.5-flash`

---

### Summary

| Step | What changed |
|---|---|
| Part A | Node calls LLM, stores plain string in `shared["message"]` |
| Part B | Node parses JSON response, stores dict in `shared["result"]` |
| Part C | `call_llm()` wired to a real provider of your choice |

The node code is identical regardless of which provider you choose — only the
`call_llm()` helper changes. This is the core PocketFlow promise: the graph
logic is decoupled from the infrastructure underneath it.

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
