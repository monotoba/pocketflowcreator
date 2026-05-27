# Part 1 — Getting Started with PocketFlow Creator

Work through these tutorials in order. Each one builds on the previous, so the concepts
introduced early become the vocabulary for everything that follows.

[← Tutorials Index](index.md)

---

## Tutorial 0: IDE Tour

**What you'll learn:** The purpose of each panel in PocketFlow Creator and how they
work together as a unified design environment.

**Prerequisites:** App launched (`python -m pocketflow_creator` or `pocketflow-creator`).

### Why a Visual Designer for LLM Workflows?

Writing LLM applications as plain Python is possible, but it forces you to hold the
entire flow in your head: which nodes exist, how they connect, which actions each one
can return, and which shared-store keys flow between them. Small flows are manageable;
multi-node pipelines with loops, branches, and sub-graphs become hard to reason about
quickly.

PocketFlow Creator externalises that mental model onto a canvas. You see the graph,
you see the data contracts between nodes, and you can validate the whole structure
before writing a single line of code. The generated Python is plain, readable PocketFlow
code that runs without the designer installed — the canvas is a design tool, not a
runtime wrapper.

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

**Project Explorer (left dock, top)**
Shows every file in your project as a tree: graphs, prompt files, node type definitions,
and tool scripts. Double-clicking a graph opens it on the canvas. Double-clicking a
prompt file opens it in the Markdown editor. Think of this as the file browser for your
LLM application.

**Component Palette (left dock, bottom)**
The source of new nodes. Every built-in node type lives here, along with any snippets
you have configured. Drag a node type from the palette onto the canvas to create an
instance of it. The palette also shows custom node types once you have defined them —
they appear alongside the built-ins.

**Graph Canvas (centre)**
The main design surface. This is where you place nodes, draw edges between them, and
see the shape of your flow at a glance. Nodes are the work units; edges are the labelled
transitions between them. The canvas is interactive: you can drag nodes to reposition
them, click edges to inspect or relabel them, and zoom with Ctrl+Scroll.

Each node shows its data contract directly on its tile:

- **Left port** (input) — labelled with the shared-store key the node reads (its
  `input_key` property). Nodes without an explicit input key show `in`.
- **Right ports** (outputs) — one circle per action, each labelled with the action
  name (e.g. `default`, `pass`, `fail`). Multi-action nodes grow taller to accommodate
  all their ports; each port is wired to a separate outgoing edge.

Reading these labels lets you trace the data flow across the graph without opening the
Inspector or the code editor.

**Object Inspector (right dock, top)**
Shows and edits the properties of whatever is selected on the canvas. Selecting a node
shows its ID, type, title, actions, and any custom properties. Selecting an edge shows
its action label. Changes made here are reflected on the canvas immediately — the
inspector and the canvas are always in sync.

**Component Palette (right dock, bottom)**
A secondary palette for quick access when the left dock is collapsed.

**Bottom Tabs**
The tabbed panel at the bottom switches between several views:

| Tab | Purpose |
|---|---|
| **Python** | Live code editor for the current graph's node implementations |
| **Markdown** | Editor + live preview for prompt files |
| **YAML** | Editor for metadata and schema files, with parse-error feedback |
| **Run Log** | Step-by-step output from the last run |
| **Shared Store** | Live JSON view of the shared store during and after a run |
| **Prompt Preview** | Shows the rendered prompt for the selected LLM node |
| **Generated Code** | Read-only view of the exported `flow.py` |
| **Test Results** | Output from `pytest` when you run the test suite |
| **Problems** | Validation errors from the most recent validate operation |
| **Data Flow** | Plain-text report showing which shared-store keys each node reads and writes, execution order, and any routing warnings — generated via Project > Data Flow Report |

### How the Panels Work Together

The typical design loop in Creator is:

1. Drag nodes from the **Palette** onto the **Canvas**
2. Wire edges between nodes (output port → input port)
3. Click a node to inspect and edit its properties in the **Inspector**
4. Double-click a node to jump to its implementation in the **Python** tab
5. Press F5 to run, then read the **Run Log** and **Shared Store** tabs
6. Fix issues flagged in the **Problems** tab

Each panel has a focused job, and they all stay in sync. There is no save-then-refresh
cycle — what you see is always current.

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
| Undo | Ctrl+Z |
| Redo | Ctrl+Y |
| Zoom in | Ctrl++ |
| Zoom out | Ctrl+- |
| Zoom to fit | Ctrl+0 |
| Zoom to selected node | Ctrl+Shift+Z |
| Auto Arrange… | Ctrl+Shift+L |
| Delete selected node | Delete |

---

## Tutorial 1: Hello LLM

**What you'll learn:** Make your first real LLM call from a PocketFlow node, understand
the three-method node lifecycle (`prep` / `exec` / `post`), produce structured JSON
output, and configure four different LLM providers.

**Prerequisites:** None. You do not need an open project to understand this tutorial.

### Understanding the Node Lifecycle

Every PocketFlow node has exactly three methods, and they have distinct responsibilities.
Understanding why they are separate is more important than memorising the signatures.

**`prep(self, shared)`** — *Read from the world, prepare inputs.*
This method has access to `shared`, the dictionary that flows through the entire graph.
Its job is to extract whatever the node needs and return it as `prep_res`. Keeping reads
in `prep` keeps `exec` pure: `exec` receives only what it needs and nothing more.

**`exec(self, prep_res)`** — *Do the work.*
This is where the LLM call, tool call, file read, or calculation happens. `exec` receives
only what `prep` handed it — it never touches `shared` directly. This separation is
intentional: it makes `exec` easy to test in isolation and easy to swap out without
touching the data-flow logic.

**`post(self, shared, prep_res, exec_res)`** — *Write results back, choose the next step.*
This method receives both what `prep` prepared and what `exec` produced. It writes
results into `shared` and returns a string — the **action** — that tells the graph
which edge to follow next. Returning `"default"` follows the default edge.

This three-phase design means every node has a clear contract: read → work → write/route.

---

### Part A — Plain Text Response

The simplest possible flow sends a prompt to an LLM and prints the response.

#### Graph

```
[Start] --default--> [HelloLlm] --default--> [Stop]
```

#### Node code

```python
class HelloLlm(Node):
    def prep(self, shared: dict) -> str:
        # We read nothing from shared here — the prompt is hardcoded.
        # In a real flow, you might read shared["user_input"] instead.
        return 'Reply with exactly this text and nothing else: LLM says: Hello User'

    def exec(self, prep_res: str) -> str:
        # call_llm is the only thing that changes when you switch providers.
        # The rest of the node is provider-agnostic.
        return call_llm(prep_res)

    def post(self, shared: dict, prep_res: str, exec_res: str) -> str:
        # Store the result so downstream nodes can use it.
        shared["message"] = exec_res
        print(exec_res)       # → LLM says: Hello User
        return "default"      # follow the "default" edge to the next node
```

**Why this matters:** Even this trivial example demonstrates the full lifecycle.
`prep` prepares the prompt, `exec` calls the LLM, `post` stores the result and routes
the flow. In a larger application you would replace the hardcoded prompt with something
read from `shared`, and the print with a downstream node that formats and delivers the output.

**Expected output:**
```
LLM says: Hello User
```

---

### Part B — Structured JSON Response

Plain text output is fine for printing, but most real applications need typed, structured
data that downstream nodes can work with programmatically. The solution is to instruct
the LLM to respond with JSON and parse it in `exec`.

Why parse in `exec` rather than `post`? Because `exec` is the work step — if the parse
fails (malformed JSON from a non-deterministic model), you catch the error at the
work boundary, not after you have already tried to write to `shared`. You can also
add retry logic around `exec` without touching `prep` or `post`.

```python
import json

class HelloLlm(Node):
    def prep(self, shared: dict) -> str:
        # The prompt explicitly demands JSON and specifies the exact structure.
        # Being precise here greatly reduces malformed responses.
        return (
            'Respond with ONLY valid JSON — no markdown, no extra text.\n'
            'Use exactly this structure: {"message": "LLM says: Hello User"}'
        )

    def exec(self, prep_res: str) -> dict:
        raw = call_llm(prep_res)
        # Some models wrap responses in markdown code fences even when asked not to.
        # Strip them defensively rather than assuming the model will always comply.
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)   # raises ValueError on bad JSON — handle or retry here

    def post(self, shared: dict, prep_res: str, exec_res: dict) -> str:
        # exec_res is now a dict, not a string.
        shared["result"] = exec_res
        print(exec_res["message"])   # → LLM says: Hello User
        return "default"
```

**Expected output:**
```
LLM says: Hello User
```

The value at `shared["result"]` is a proper Python dict:
```python
{"message": "LLM says: Hello User"}
```

Downstream nodes can access `shared["result"]["message"]` directly, pass it to a
formatter, validate it against a schema, or route on its fields.

---

### Part C — Configuring an LLM Provider

The `call_llm` function is deliberately left as a placeholder in PocketFlow examples.
Swap in whichever implementation matches your provider. All four options below produce
the same interface — a function that takes a string and returns a string — so your node
code never changes when you switch providers.

---

#### Option 1 — Ollama (local, no API key)

[Ollama](https://ollama.com) runs open-source models on your own machine. It is the
best starting point: free, private, and works entirely offline once the model is downloaded.

**When to use:** Development and prototyping, privacy-sensitive applications, no-cost
experimentation with open-source models.

**Install and pull a model:**
```bash
# Install Ollama from https://ollama.com, then:
ollama pull llama3.2          # ~2 GB — fast, good for most tasks
ollama pull mistral           # alternative if you prefer Mistral
```

**Provider code:**
```python
import json
import urllib.request

def call_llm(prompt: str, model: str = "llama3.2") -> str:
    """Send a prompt to Ollama running on localhost and return the response."""
    url = "http://localhost:11434/api/generate"
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,        # get the full response at once, not a stream
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["response"].strip()
```

**In PocketFlow Creator:** Tools > Provider Manager → set Provider to `Ollama`,
Base URL to `http://localhost:11434`, Model to `llama3.2`.

---

#### Option 2 — OpenAI API

OpenAI's hosted models are widely used and have excellent instruction-following.
`gpt-4o-mini` is fast and inexpensive; `gpt-4o` is more capable for complex reasoning.

**When to use:** Production applications where response quality and reliability matter;
when you need function calling or vision capabilities.

```bash
pip install openai
```

```python
from openai import OpenAI

_client = OpenAI(api_key="sk-...")   # or export OPENAI_API_KEY in your shell

def call_llm(prompt: str, model: str = "gpt-4o-mini") -> str:
    response = _client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()
```

**In PocketFlow Creator:** Tools > Provider Manager → Provider: `OpenAI`,
API Key: your key, Model: `gpt-4o-mini`.

---

#### Option 3 — Anthropic Claude API

Claude models are particularly strong at following precise instructions and producing
well-structured output — both important properties when asking for JSON.

**When to use:** Tasks requiring nuanced reasoning, long context windows, or especially
reliable instruction-following.

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

**Model guide:** `claude-haiku-4-5-20251001` is fast and cheap; `claude-sonnet-4-6`
balances quality and speed; `claude-opus-4-7` is most capable.

**In PocketFlow Creator:** Tools > Provider Manager → Provider: `Claude`,
API Key: your Anthropic key, Model: `claude-haiku-4-5-20251001`.

---

#### Option 4 — Google Gemini API

Gemini has a generous free tier on `gemini-1.5-flash`, making it a good option for
experimentation without a credit card.

**When to use:** Free-tier prototyping, multimodal tasks (when combined with image input),
Google Cloud integration.

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

**In PocketFlow Creator:** Tools > Provider Manager → Provider: `Gemini`,
API Key: your Google AI Studio key, Model: `gemini-1.5-flash`.

---

### Summary

| Step | Key concept |
|---|---|
| Part A | `prep` / `exec` / `post` lifecycle; returning an action string |
| Part B | Parse structured output in `exec`; downstream nodes get typed data |
| Part C | `call_llm` is the only thing that changes between providers |

The most important insight from this tutorial: **your node logic is decoupled from the
provider.** A flow written today against Ollama runs tomorrow against Claude by changing
one function. PocketFlow's architecture enforces this separation by design.

---

## Tutorial 2: Your First Flow — Hello World

**What you'll learn:** Create a project, place nodes on the canvas, wire them with
action edges, set properties in the inspector, and run the flow.

**Prerequisites:** Tutorial 0 — you know what each panel does.

### What Is a Flow, Exactly?

A PocketFlow flow is a **directed graph**: a set of nodes connected by directed edges.
Each node does a unit of work and then returns an action string (like `"default"` or
`"error"`). The edge labelled with that action string determines which node runs next.

This is fundamentally different from a plain Python function chain. There is no
hardcoded call sequence in the framework code — only a routing table that says
"if node A returns `'ok'`, go to node B; if it returns `'error'`, go to node C."
This makes flows easy to visualise, test, and modify without touching unrelated code.

Every flow needs at least three things:

- A **Start Node** — the unique entry point the runner looks for
- At least one **processing node** — where the real work happens
- A **Stop Node** — a terminal point (you can have several, one per exit path)

### Steps

**1. Create a project**

File > New Project… opens the project creation dialog. Give it the name `hello_world`
and choose a folder on disk.

*Why a project?* A project is a folder that holds everything together: graph files,
prompt files, node type definitions, generated code, and test files. Creator uses the
project structure to know where to look for each kind of file. Without a project, the
code editor and the export pipeline have nowhere to write.

**2. Open the graph**

In Project Explorer, double-click `graphs/main.pfcgraph.yaml`. The canvas appears empty.

*Why YAML?* Graph files are plain YAML — human-readable, diffable in git, and editable
in a text editor if needed. You are never locked into the visual format.

**3. Add a Start Node**

Drag **Start Node** from the Component Palette onto the canvas. Click it to select it,
then in the Object Inspector change **Title** to `Start`.

*Why rename?* The title is what you see on the canvas. Meaningful titles make large
flows readable at a glance. The ID (auto-generated, shown in the inspector but not editable)
is what the code uses internally.

**4. Add an LLM Prompt Node**

Drag **LLM Prompt Node** onto the canvas, to the right of Start. Set **Title** to
`Ask LLM`.

In the Inspector you will see two prompt-related properties:

- **`prompt_type`** — a drop-down with two choices:
  - `string` *(default)* — type the prompt directly into the `prompt_file` field
  - `path` — enter a relative file path; the file is read at run time
- **`prompt_file`** — the prompt text or file path, depending on `prompt_type`

For a quick first run, leave `prompt_type` as `string` and type your prompt directly
into `prompt_file` (e.g. `Say hello to the world in one sentence.`). Switch to `path`
when you want to manage longer prompts as reusable Markdown files.

**5. Add a Stop Node**

Drag **Stop Node** to the right of Ask LLM. Set **Title** to `End`.

*Why a Stop Node?* The runner stops when it reaches a node with no outgoing edges, or
explicitly when it reaches a Stop Node. Having an explicit Stop Node makes the exit point
visible in the graph and prevents accidental infinite loops.

**6. Wire the edges**

Click the **output port** (right side circle) of Start and drag to the **input port**
(left side circle) of Ask LLM. A dialog or inspector field will ask for the action label
— type `default`. Repeat: wire Ask LLM → End with action `default`.

*Why label edges?* PocketFlow routes by comparing the string returned by `post()` to the
edge labels. A node that returns `"default"` will follow any edge labelled `"default"`.
If a node has two edges — `"ok"` and `"error"` — it can route to different destinations
based on what happened in `exec`. Labelling everything `"default"` is fine for linear
flows; the labels matter when you start branching.

**7. Create the prompt file**

Click the **Markdown** tab at the bottom. Type:
```
Say hello to the world in one sentence.
```
Save with Ctrl+S to `prompts/hello.md`.

*Why Markdown for prompts?* Prompts are text that LLMs read. Markdown lets you structure
longer prompts with headers and bullet points without any special syntax. The live preview
on the right side of the Markdown tab lets you see the rendered version as you type.

**8. Validate the graph**

Project > Validate Project (Ctrl+Shift+V). Check the **Problems** tab.

*Why validate before running?* The validator catches structural errors — missing start
node, dangling edges, undeclared actions — that would cause the runner to fail at runtime.
It is faster to catch these in the designer than to read a Python traceback.

**9. Run with the mock provider**

Run > Run Active Flow (F5). Watch the **Run Log** tab.

*What is the mock provider?* When no real LLM provider is configured, Creator uses a
mock that echoes the prompt back. This lets you test the flow structure and routing
logic without an API key or internet connection.

**Expected result:** Three nodes on canvas, no red error badges, Run Log shows three
steps — Start, Ask LLM, End — each with a status of `completed`.

---

## Tutorial 3: Using the Properties Inspector

**What you'll learn:** Every field in the Object Inspector, how live sync works, and
why getting properties right before writing code saves time.

**Prerequisites:** Tutorial 2 — a project with nodes on the canvas.

### The Inspector as Your Node's Contract

The Inspector is not just a label editor. Every field you fill in here becomes part
of the node's public contract: what actions it can return, which shared-store keys it
reads and writes, and what its configuration parameters are. When you define these
clearly in the Inspector before writing code, you have a spec to code against. Other
nodes in the graph can see what you declared, and the validator can check that your
edges are consistent with your actions.

### Node Properties

Click any node on the canvas to see its properties:

| Field | Editable | Purpose |
|---|---|---|
| **ID** | No | Unique internal identifier — used in NODE_START markers and graph YAML |
| **Type** | No | The palette type this instance was created from |
| **Title** | Yes | The name shown on the canvas tile |
| **Position X/Y** | No | Canvas coordinates — drag the node to reposition |
| **Actions** | Yes | Comma-separated list of action strings this node's `post()` can return |
| **Reads** | Yes | Shared-store keys this node reads (documentation only — not enforced) |
| **Writes** | Yes | Shared-store keys this node writes (documentation only) |

**Why document Reads and Writes if they are not enforced?** Because they make the data
flow visible without opening the code. When you look at a graph with eight nodes, being
able to click any node and see "this reads `user_input` and writes `llm_response`" tells
you immediately what the data flow is. It also helps the Shared Store Designer know
which keys to expect.

### Live Sync in Practice

1. Select the **Ask LLM** node you created in Tutorial 2
2. Change **Actions** from `default` to `success, failure`
3. Watch the canvas — the edge you wired with `"default"` will now show a validation
   error badge because `"default"` is no longer a declared action on this node

This is live sync: the inspector change immediately propagates to the validator. You
do not have to save and reload — the designer maintains a consistent in-memory model
and the canvas reflects it continuously.

4. Change Actions back to `default` to clear the error
5. Change **Reads** to `user_input` and **Writes** to `llm_response`

These documentation fields appear in exported code comments and in the shared-store
schema helper, but do not affect runtime behaviour.

### Edge Properties

Click an edge (the connecting line) rather than a node. The Inspector shows:

- **Action** — the label on this edge. This must match one of the source node's declared
  Actions, otherwise the validator flags error PFCE2101. Clicking the action field lets
  you rename the edge in place.

### Node Port Labels

The canvas reflects the Inspector values without you needing to read any code:

- **Input label** (lower-left of the node tile) — displays the value of the node's
  `input_key` property, or `in` if none is set. This tells you at a glance which
  shared-store key the node expects to find when it runs.
- **Output labels** (right side, one per action) — each action port is labelled with
  its action string. Multi-action nodes grow taller so every port has its own clearly
  labelled row. Edges drawn from a specific port carry that action automatically.

If you change `input_key` in the Inspector, the canvas label updates immediately.

### The Data Flow Report

Once your graph has more than a few nodes, understanding which key is written where and
read by whom becomes non-trivial. The **Data Flow Report** answers that question in one
click:

**Project > Data Flow Report** — or look at the **Data Flow** tab in the bottom panel.

The report contains three sections:

**NODE DATA FLOW** — a table listing every node in BFS execution order, with columns for
the shared-store keys it reads and the keys it writes. Multi-action nodes also show their
branch destinations.

**SHARED STORE KEY LIFECYCLE** — for every key that appears in the graph, one row showing
which node writes it and which nodes read it. A key marked `(external)` in the
"Written by" column must be supplied by the caller before the flow starts.

**DATA FLOW NOTES** — routing and key warnings:
- A key that is written but never read (likely dead output)
- A key that is read but never written (must come from outside the flow)
- A key written by more than one node (later write silently overwrites the earlier one)
- An edge whose action doesn't match any action the source node declares

Run the report whenever you add new nodes, change `input_key`/`output_key` properties,
or add a new routing branch. It is the fastest way to catch data-contract mismatches
before running the flow.

### When to Use the Inspector vs. the Code Editor

Use the Inspector for everything structural: titles, actions, documented reads/writes,
and any properties defined by the node type (like `prompt_type`, `prompt_file`, or `top_k`). Use the
code editor for the actual implementation of `prep`, `exec`, and `post`. The split keeps
the graph self-describing — you can understand a flow's structure without reading any code.

---

## Tutorial 4: The Code Editor — RAD Node Coding

**What you'll learn:** How double-clicking a node opens and scaffolds its Python class,
what the NODE_START and NODE_END markers do, and how changes in the code file sync back
to the canvas.

**Prerequisites:** Tutorial 2 — an open project with nodes on the canvas.

### The Code File and the Graph File are Two Views of the Same Thing

Every graph (`graphs/main.pfcgraph.yaml`) has a companion code file (`code/main.py`).
The graph file describes the structure — which nodes exist, how they are connected. The
code file contains the implementation — what each node actually does. Creator keeps these
two files in sync automatically:

- When you **add a node** to the canvas (drag from palette or click a toolbar button),
  Creator adds a class stub to the code file immediately
- When you **double-click a node**, Creator opens the code file and scrolls to that
  node's class
- When you **delete a node** from the canvas, Creator removes its class from the code
  file
- When you **delete a node's class** from the code file and save, Creator removes the
  node from the canvas

This bidirectional sync means you never have orphaned code and you never have nodes
with missing implementations.

### The NODE_START / NODE_END Markers

Creator wraps each node class in a pair of marker comments:

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

The markers use the node's unique ID (not the title) so they survive title changes.
**Do not remove the markers.** They are how Creator locates your class when syncing.
Everything between them is yours to edit freely — the markers are just bookends.

### Steps

**1. Open a node's code**

Double-click the **Ask LLM** node on the canvas. The Python tab opens and scrolls to
the `AskLlm` class. If the code file does not exist yet, Creator creates it with the
file header and a stub for this node.

*Why double-click rather than navigating to the file manually?* Because the code file
may contain many node classes. Double-clicking is a direct jump — you land exactly at
the class you want to edit, regardless of how many other classes are in the file.

**2. Read the stub**

The generated stub shows all three methods with placeholder return values. The docstring
tells you the type_id and title. The type signature is intentionally loose (`object`) so
you can annotate it with real types as you implement each method.

**3. Implement the node**

Replace the stub bodies with real logic:

```python
# --- NODE_START: node_abc12345 ---
class AskLlm(Node):
    """llm_prompt_node: Ask LLM"""

    def prep(self, shared: dict) -> str:
        # Resolve the prompt based on prompt_type set in the Inspector.
        # "string" → use the text directly; "path" → read from a file.
        prompt_type = shared.get("prompt_type", "string")
        prompt_value = shared.get("prompt_file", "")
        if prompt_type == "path" and prompt_value:
            with open(prompt_value, encoding="utf-8") as f:
                return f.read()
        return prompt_value or "What is PocketFlow?"

    def exec(self, prep_res: str) -> str:
        # call_llm is your provider helper from Tutorial 1.
        return call_llm(prep_res)

    def post(self, shared: dict, prep_res: str, exec_res: str) -> str:
        # Store the response for downstream nodes.
        shared["llm_response"] = exec_res
        return "default"

# --- NODE_END: node_abc12345 ---
```

**4. Save**

Ctrl+S writes the file to disk. The canvas does not need to be refreshed — the graph
model and the code file are separate concerns that stay in sync through the bidirectional
markers, not through re-parsing.

**5. Delete a node from the canvas**

Click a node and press Delete. The node disappears from the canvas and its class (the
entire NODE_START…NODE_END block) is removed from the code file automatically. This
prevents the code file from accumulating dead classes as your graph evolves.

**6. Delete a class from the code file**

Open the Python tab, manually delete the NODE_START…NODE_END block for a node, and
save (Ctrl+S). Creator detects that the marker is gone and removes the corresponding
node from the canvas. This is the reverse direction of the sync.

### When to Write Code Here vs. Exporting

The embedded editor is for active development. It gives you immediate feedback via
the Run Log and Shared Store tabs. When you are done and want to ship, use File > Export
to get a clean standalone Python package that runs without Creator.

---

## Tutorial 5: Creating a Custom Node Type

**What you'll learn:** When to create a custom node type (versus using a Basic Node),
how the Node Type Wizard works, and how custom types appear in the palette.

**Prerequisites:** Tutorial 2.

### When to Create a Custom Node Type

A **Basic Node** is the right choice for one-off logic that is specific to a single
flow. But when you find yourself building the same kind of node repeatedly — with the
same structure, the same properties, and the same action pattern — that is a signal to
create a custom node type.

Custom node types give you:
- A named entry in the Component Palette so you can drag and drop them like built-ins
- Typed properties with defaults that appear in the Inspector for every instance
- A YAML definition that can be shared across projects and checked into version control
- A Python skeleton generated automatically, ready for your implementation

The rule of thumb: if you would build this node more than twice, define it as a type.

### Steps

**1. Open the Node Type Wizard**

Node > New Custom Node Type… opens the wizard.

**2. Fill in the identity fields**

- **Node Type ID:** `sentiment_node` — this is the internal identifier, used in graph
  files and code markers. Use lowercase with underscores. Once set, changing this breaks
  existing graphs that use the type.
- **Display Name:** `Sentiment Analyser` — what appears in the palette and on the canvas tile
- **Category:** `Analysis` — groups related types in the palette

*Why separate ID and display name?* The ID is a stable technical identifier; the display
name can change freely without breaking anything.

**3. Set the base class**

Leave **Base Class** as `Node` for a standard single-execution node. Choose `BatchNode`
if this type will process a list of items, or `AsyncNode` if it performs async I/O.
The base class is what PocketFlow uses to call the right execution strategy.

**4. Declare actions**

In the **Actions** field, enter: `positive, negative, neutral`

These are the strings your `post()` method can return. The wizard records them in the
YAML definition so that when someone adds an instance of this type to a canvas, the
validator knows which actions are valid. Every outgoing edge must match one of these.

**5. Add a property**

Click **Add Property**:
- Name: `threshold`
- Type: `number`
- Default: `0.5`

Properties defined here appear in the Object Inspector for every instance of this type.
A developer can configure the threshold per-instance without touching the code — the
inspector writes the value into the graph YAML, and your `prep` can read it from
`shared` or from the node's properties dict.

**6. Click Create**

The wizard writes two files:
- `node_types/sentiment_node.yaml` — the full type definition, including properties
  schema and action declarations
- `custom/sentiment_node.py` — a Python skeleton with the correct base class

**7. Implement the skeleton**

Open `custom/sentiment_node.py` from Project Explorer and fill in the logic:

```python
class SentimentNode(Node):
    def prep(self, shared: dict) -> str:
        # Read the text to classify from the shared store.
        return shared.get("text", "")

    def exec(self, prep_res: str) -> str:
        # Simple keyword-based classifier for demonstration.
        # Replace with a real model call in production.
        text = prep_res.lower()
        if any(w in text for w in ["great", "love", "excellent", "happy"]):
            return "positive"
        if any(w in text for w in ["bad", "hate", "terrible", "awful"]):
            return "negative"
        return "neutral"

    def post(self, shared: dict, prep_res: str, exec_res: str) -> str:
        shared["sentiment"] = exec_res
        # Return the sentiment label as the action — the graph routes on it.
        return exec_res
```

**8. Use the new type**

`Sentiment Analyser` now appears in the Component Palette under "Analysis". Drag it
onto any canvas and wire three outgoing edges: `positive`, `negative`, `neutral`.
The validator will flag an error if any of the three declared actions is unwired,
reminding you to handle every exit path.

---

## Tutorial 6: Project Templates

**What you'll learn:** How to start a new project from a built-in template, what files
a template creates, and when templates save meaningful time.

**Prerequisites:** None.

### Why Templates Matter

Starting from a blank canvas is fine for learning, but real workflows have a predictable
structure: a graph file, one or more prompt files, a code file, and a project manifest.
Templates pre-build that structure so you can jump straight to the interesting part —
designing the flow — without repeating boilerplate setup.

Templates also enforce consistency. On a team, everyone starting from the same template
means every project has the same folder layout, the same naming conventions, and the
same initial graph structure. That makes onboarding and code review much easier.

### Steps

**1. Open the template picker**

File > New From Template… shows the available templates. Select **Simple LLM Flow**.

**2. Configure and create**

Choose a folder and enter a project name. Click **Create**. Creator generates:

```
my_project/
├── project.pfcproj.yaml        ← project manifest (name, provider, model settings)
├── graphs/
│   └── main.pfcgraph.yaml      ← Start → LLM Prompt → Stop, pre-wired
├── prompts/
│   └── main.md                 ← placeholder prompt file
├── code/
│   └── (generated on first node open)
└── node_types/
    └── (empty — add custom types here)
```

**3. Explore the pre-wired graph**

Open `graphs/main.pfcgraph.yaml`. You see three nodes already placed and connected.
Use View > Zoom to Fit (Ctrl+0) to centre the view. The template has done the structural
work; your job is to replace the placeholder prompt and implement the node bodies.

**4. Edit the prompt**

Double-click `prompts/main.md` in Project Explorer. The Markdown editor opens. Replace
the placeholder with an instruction relevant to what you are building. Save.

**5. Run**

F5 — the mock provider echoes the prompt. Switch to a real provider in Tools > Provider
Manager and run again to see a genuine LLM response.

### What to Do When No Template Fits

If none of the templates matches your use case, start from the **Blank Project** template
(File > New Project…). Build the first version manually, then use File > Export to get
the raw file structure. You can use that exported structure as the basis for your own
template for future projects.

---

[→ Continue to Part 2 — PocketFlow Patterns](part2_patterns.md)
