# Part 3 — Advanced Creator Features

This section covers Creator features that go beyond building and running a single flow.
You will learn how to catch problems before they happen (validation), investigate them
when they do (debugging), compose flows from reusable sub-graphs (subflow composition),
take your work outside Creator (export), document your data contracts formally (Shared
Store Designer), and share your tools with others (packaging).

Each tutorial explains not just the steps but the reasoning behind each feature — why
it exists, what problem it solves, and when you would reach for it.

[← Tutorials Index](index.md)

---

## Tutorial 18: Validation and Error Badges

**What you'll learn:** How Creator's validator detects structural problems in your graph
before you run, what each error code means, and how to read the visual error indicators.

### Why validation exists

A flow that looks correct on the canvas can fail at runtime in ways that are hard to
diagnose: a node with no outgoing edges leaves the runner nowhere to go; an action label
that does not match a declared action causes a silent routing failure; a missing start node
means the runner cannot determine where to begin. Catching these problems before running
saves the time spent reading Python tracebacks to find graph-level errors.

Creator's validator analyses the graph structure — not the Python code — and reports
problems as numbered error codes. Validation runs automatically before Run and before Export,
so you cannot accidentally run a structurally broken flow.

### Understanding error codes

| Code | What is wrong | How to fix it |
|---|---|---|
| PFCE1001 | No start node is set | Mark a node as the entry point: select it and choose Flow > Set Start Node |
| PFCE1002 | Two nodes share the same ID | Delete and re-add the duplicate; Creator assigns a fresh ID |
| PFCE1003 | The declared start node ID does not exist | Re-set the start node via Flow > Set Start Node |
| PFCE2001 | An edge's source node has been deleted | Delete the dangling edge and re-wire |
| PFCE2002 | An edge's destination node has been deleted | Delete the dangling edge and re-wire |
| PFCE2003 | An edge has no action label | Click the edge label and type an action name |
| PFCE2101 | An edge's action is not in the source node's declared Actions | Add the action to the node's Actions field in Inspector |
| PFCE2102 | A Subflow Node has no `subflow_ref` set | Set `subflow_ref` in Inspector to a valid graph file path |

### Reading error badges

When validation finds a problem, Creator draws a red border around the affected node and
marks the node's corner with a red badge. These badges persist until the error is resolved.
The Problems panel (View > Problems) lists all errors with their codes, descriptions, and
the node or edge where the error was found. Clicking a problem in the panel selects the
affected element on the canvas.

### Step-by-step

**Step 1: Create a deliberately broken graph.**

New project: `tut_validation`. Add a Basic Node onto the canvas. Do not add Start or Stop
nodes. Do not wire any edges. This graph has PFCE1001 (no start node) and implicitly
PFCE2001/PFCE2002 issues if any edges existed.

**Step 2: Run the validator.**

Project > Validate Project (Ctrl+Shift+V). The Problems panel opens listing at least
PFCE1001. The Basic Node gains a red border badge because it is the only node and therefore
implicated in the missing-start-node problem.

**Step 3: Fix each error.**

Select the Basic Node. Flow > Set Start Node. Run the validator again — PFCE1001 clears.

Add a Stop Node. Draw an edge from the Basic Node to the Stop Node. The edge has no label:
PFCE2003 appears. Click the edge label (double-click the arrow between nodes) and type
`default`. PFCE2003 clears.

Add a second Basic Node. Draw an edge from the first Basic Node to this second node with
action `process`. The second node's declared Actions list does not include `process`:
PFCE2101 appears. Select the first Basic Node. In Inspector, add `process` to the Actions
field. PFCE2101 clears.

**Step 4: Verify a clean graph.**

Run Validate again. The Problems panel should be empty. All red badges should be gone.
The flow is now structurally valid and can be run or exported.

**Tip:** Use validation as a first check whenever a flow fails unexpectedly. Graph-level
errors in Creator are caught here; Python logic errors appear in the Run Log during execution.

---

## Tutorial 19: Debug Mode and Breakpoints

**What you'll learn:** How to step through a running flow node by node, inspect the shared
store at each pause, and use breakpoints to isolate where things go wrong.

### Why debug mode exists

When a flow produces wrong output, the question is: which node produced it? You could add
`print` statements everywhere and re-run, but that is slow and leaves the code cluttered.
Debug Mode lets you pause execution at any node and inspect the full shared store state
at that exact moment — before and after every key transformation.

Breakpoints in Creator work like breakpoints in a code debugger: execution pauses when the
flow reaches the marked node, you inspect what you need, and you resume when ready. Unlike
a code debugger, Creator's breakpoints pause between nodes (at the graph level) rather than
between lines of code.

### Step-by-step

**Step 1: Open a project with a non-trivial flow.**

Open the project from Tutorial 7 (Hello World), or any project with at least two active
nodes. A flow with a single node is not useful for breakpoint demonstration because there
is only one place to pause.

**Step 2: Set a breakpoint.**

Click the **Ask LLM** node to select it. Press F9, or use Node > Toggle Breakpoint. A red
dot appears in the node's top-right corner. This dot is a persistent marker — it is saved
with the project and visible every time you open the canvas.

**Step 3: Start a debug session.**

Run > Debug Active Flow (Shift+F5). The flow starts executing normally until it reaches
Ask LLM. At that point, execution pauses and the status bar shows "Paused at: Ask LLM".

**Step 4: Inspect state before the node runs.**

With execution paused before Ask LLM, check the Shared Store tab. You see everything that
nodes before Ask LLM have written. In this flow, Start wrote nothing — but in a multi-node
flow you would see the outputs of all completed nodes here.

This "before" state tells you whether the inputs to the paused node are correct. If `question`
is missing or malformed at this point, the bug is in an earlier node, not in Ask LLM.

**Step 5: Resume and inspect the "after" state.**

Run > Resume (F5). The flow runs Ask LLM and pauses again if there is another breakpoint,
or continues to the end. After the node completes, the Shared Store shows the new values
it wrote — in this case, `answer`.

**Step 6: Use multiple breakpoints in a loop.**

Open Tutorial 8 (Chat). Set breakpoints on **Get Input** and **Call LLM**. Run in debug
mode. The flow pauses at Get Input (before asking for user input), then at Call LLM (before
the LLM call). You can watch `history` accumulate in the Shared Store with each iteration
through the loop.

**Step 7: Stop a debug session.**

Run > Stop. The flow terminates immediately regardless of where it was paused. Any shared
store state accumulated so far is discarded.

**Tips for effective debugging:**
- Set breakpoints on the node just *before* the suspected problem to verify its inputs.
- Set breakpoints on the node just *after* the problem to verify its outputs.
- Use the Run Log tab alongside the Shared Store tab: the log shows timing and errors;
  the store shows data.
- Remove all breakpoints (Node > Remove All Breakpoints) before running for performance testing.

---

## Tutorial 20: Subflow Composition

**What you'll learn:** How to embed a reusable sub-graph inside a parent flow using the
Subflow Node, when composition is the right design choice, and what happens to shared store
state across the boundary.

### Why subflow composition exists

As flows grow, they become hard to read and maintain. A 20-node flow is difficult to
navigate; a parent flow with four Subflow Nodes each pointing to a 5-node sub-graph is
much clearer. More importantly, sub-graphs are reusable: if three different parent flows
all need a summarization pipeline, you build it once and reference it from all three.

Subflow composition in Creator maps directly to PocketFlow's `Flow` nesting. When the
runner reaches a Subflow Node, it executes the referenced graph inline and merges that
graph's shared store changes back into the parent's shared store. The boundary is
transparent at runtime.

### Step-by-step

**Step 1: Create the project.**

New project: `tut_subflow`. This project will have two graphs.

**Step 2: Build the reusable sub-graph.**

In Project Explorer, right-click the `graphs/` folder and create a new graph:
`summarizer.pfcgraph.yaml`. Click it to open the canvas for that graph.

Add: Start Node → Basic Node (`Load Text`) → LLM Prompt Node (`Summarize`) → Stop Node.
Wire sequentially with `default` actions.

Write `Summarize`'s code:
```python
class Summarize(Node):
    def prep(self, shared):
        return shared.get("text_to_summarize", "")

    def exec(self, prep_res):
        if not prep_res:
            return "No text provided."
        return call_llm(f"Summarize in one paragraph:\n{prep_res}")

    def post(self, shared, prep_res, exec_res):
        shared["summary"] = exec_res
        return "default"
```

Validate the summarizer graph. It should be clean.

**Step 3: Build the parent flow.**

In Project Explorer, click `main.pfcgraph.yaml` to return to the main canvas. Add:
Start Node, Basic Node (`Prepare Content`), Subflow Node, Basic Node (`Use Summary`), Stop Node.

**Step 4: Configure the Subflow Node.**

Select the Subflow Node. In Inspector, the `[Subflow]` section appears at the bottom. Set
`subflow_ref` to `graphs/summarizer.pfcgraph.yaml`. This is the relative path from the
project root to the sub-graph file.

After setting `subflow_ref`, the Subflow Node's title updates to show the referenced graph
name. The validator checks that this file exists and is a valid graph (PFCE2102 clears).

**Step 5: Write the surrounding nodes.**

```python
class PrepareContent(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        # In production, fetch from an API, database, or file.
        return (
            "PocketFlow is a 100-line Python framework for building LLM pipelines. "
            "It uses a shared store to pass data between nodes. Nodes follow a "
            "prep/exec/post lifecycle. The framework is designed for clarity and "
            "minimal abstraction."
        )

    def post(self, shared, prep_res, exec_res):
        # Write to the key the summarizer reads from.
        shared["text_to_summarize"] = exec_res
        return "default"

class UseSummary(Node):
    def prep(self, shared):
        return shared.get("summary", "")

    def exec(self, prep_res):
        print("\nSummary result:", prep_res)
        return prep_res

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 6: Wire the parent flow.**

Start → Prepare Content → Subflow Node → Use Summary → Stop. All `default` actions.

**Step 7: Run the parent flow.**

Run > Run Active Flow from the main graph canvas. The runner executes `Prepare Content`,
then enters the summarizer sub-graph (Load Text → Summarize), then returns to the parent
and runs `Use Summary`. The Shared Store tab shows `text_to_summarize` (written by
Prepare Content) and `summary` (written by the sub-graph's Summarize node) — both visible
in the same store because the sub-graph merges its changes back.

**When to use subflow composition:**
- When the same sequence of nodes appears in multiple flows.
- When a flow is long enough that collapsing sections into sub-graphs improves readability.
- When different team members own different sub-graphs and need to develop them independently.

**Expected result:** `summary` in the Shared Store contains a one-paragraph condensation
of the prepared content, produced by the sub-graph's Summarize node.

---

## Tutorial 21: Exporting and Running a Standalone Project

**What you'll learn:** How to export a Creator project as a self-contained Python package
that runs without Creator installed, and how the export protects your custom code from
being overwritten.

### Why standalone export exists

Creator is a development tool. Your users, your CI/CD pipeline, and your production servers
do not run Creator — they run Python. The export feature converts your Creator project into
a standard Python package that anyone can install and run with `pip install pocketflow &&
python main.py`.

The export is designed around a critical safety rule: code you write by hand is never
overwritten. The generated files (which Creator rebuilds from your graph each time) are
always in `generated/`. The custom files (which you edit) are in `custom/`. Re-exporting
updates `generated/` and leaves `custom/` untouched.

### The project structure

When you export, Creator writes:

```
exports/<project_name>/
├── generated/
│   ├── main_nodes.py       ← auto-generated Node subclasses (from your code editor tabs)
│   └── main_flow.py        ← auto-generated flow wiring (from your graph edges)
├── custom/
│   └── main_custom.py      ← your code (never overwritten on re-export)
├── tests/
│   └── test_main.py        ← basic test scaffold
└── main.py                 ← entry point — imports and runs the flow
```

`generated/main_flow.py` translates your graph's edges into PocketFlow's `>>` wiring syntax:

```python
from pocketflow import Flow
from generated.main_nodes import AskLlm, Start, Stop

ask_llm = AskLlm()
flow = Flow(start=ask_llm)
ask_llm >> ask_llm  # default action
```

You never edit `generated/`. You do edit `custom/main_custom.py` to add helper functions,
configuration, or business logic that the nodes call.

### Step-by-step

**Step 1: Open a complete project.**

Open the Tutorial 7 project (Hello World) or any validated project. The project must pass
validation before export — Creator checks this automatically.

**Step 2: Export.**

File > Export PocketFlow Project… (Ctrl+E). A file dialog appears. Choose a parent
directory. Creator creates the `exports/<project_name>/` folder structure there.

Watch the progress bar in the status bar. When it completes, a toast notification confirms
the export path.

**Step 3: Inspect the exported files.**

In Project Explorer, navigate to the export directory (or open a terminal). Open
`generated/main_nodes.py` — you will recognise your `prep`, `exec`, and `post` code from
the Creator editor, with the proper imports added. Open `generated/main_flow.py` — you
will see the `>>` wiring derived from your graph edges.

Open `custom/main_custom.py`. This file is where you put `call_llm` implementations,
API keys, and any helper code the nodes reference.

**Step 4: Run outside Creator.**

```bash
cd exports/hello_world
pip install pocketflow
python main.py
```

If your nodes call `call_llm`, implement it in `custom/main_custom.py` before running.
A minimal implementation:

```python
# custom/main_custom.py
import os
from openai import OpenAI

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_llm(prompt: str) -> str:
    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content
```

**Step 5: Re-export after making changes.**

Return to Creator. Change a node's code or add an edge. Re-export (Ctrl+E). Open
`generated/main_nodes.py` — your changes are there. Open `custom/main_custom.py` — your
`call_llm` implementation is unchanged. The separation is guaranteed by the exporter.

**Tips:**
- Add your export directory to `.gitignore` if you do not want generated files in version control.
- Or commit the export and use it as the deployable artifact — `generated/` is deterministic,
  so diffs are clean.
- The `tests/` directory contains a scaffold. Expand it to test your business logic.

---

## Tutorial 22: Shared Store Designer

**What you'll learn:** How to use the Shared Store Designer to define, document, and
validate the schema of data flowing through your flow, and why schema documentation pays
dividends in multi-node pipelines.

### Why the Shared Store Designer exists

The shared store is a Python dictionary — at runtime, any node can write any key with any
value. This flexibility is powerful but makes large flows hard to reason about. Which node
writes `extracted_data`? Is `items` a list of strings or a list of dicts? What is the
default value of `model`?

The Shared Store Designer answers these questions visually. It does not enforce types at
runtime (Python's dynamic nature makes that impractical without invasive changes), but it
documents the contract so every developer knows what to expect. It also feeds Creator's
autocomplete when you type `shared["` in the code editor.

### Understanding the columns

| Column | Purpose |
|---|---|
| **Namespace** | Groups related keys (e.g., `user`, `llm`, `data`). Cosmetic only — no runtime effect. |
| **Key** | The exact string used in `shared["key"]` |
| **Type** | JSON Schema type: `string`, `integer`, `number`, `boolean`, `array`, `object` |
| **Default** | The value pre-loaded into the store before the flow starts. Leave blank for "not set". |

### Step-by-step

**Step 1: Open the Shared Store Designer.**

Open any project. In Project Explorer, double-click **Shared Store**. The designer opens
as a table with four columns and a toolbar above it.

**Step 2: Add keys for a typical LLM flow.**

Click the **+** button (or press Insert) to add a row. Fill in:

| Namespace | Key | Type | Default |
|---|---|---|---|
| user | question | string | What is PocketFlow? |
| llm | answer | string | |
| llm | model | string | gpt-4o-mini |
| app | max_tokens | integer | 512 |
| data | history | array | |

The `question` key has a default, so the flow can run without pre-populating the store.
The `answer` key has no default — it must be written by a node before it can be read.

**Step 3: Validate the schema.**

Click **Validate** in the toolbar. Creator checks that:
- All Type values are valid JSON Schema type names.
- Namespace and Key fields are non-empty.
- No two rows share the same Namespace + Key combination.

Fix any errors reported. Common mistakes: typing `str` instead of `string`, or `int`
instead of `integer`.

**Step 4: Save the schema.**

Click **OK**. The schema is saved to `project.pfcproj.yaml` under a `store_schema` key.
The file is human-readable YAML — you can inspect or edit it directly if needed.

**Step 5: Use the schema during a run.**

Run > Run Active Flow. When the flow is running, click the **Shared Store** tab. The tab
shows all keys — both those in the schema and any unscheduled keys nodes write dynamically.
Schema keys with defaults appear immediately; others appear when first written.

**Step 6: Use the schema in the code editor.**

Open any node in the code editor. When you type `shared["`, Creator shows an autocomplete
dropdown listing all keys from the schema. This prevents typos (`shared["anwser"]` instead
of `shared["answer"]`) that cause silent KeyError bugs.

**Tips:**
- Use namespaces consistently: all LLM inputs/outputs under `llm`, all user data under
  `user`, intermediate processing data under `data`. This makes the schema easy to scan.
- Define defaults for any key that must be set for the flow to run without manual intervention.
  A flow with sensible defaults can be run immediately after export without extra setup.
- The schema is living documentation. Update it when you add or rename keys — stale schemas
  are worse than no schema because they mislead readers.

---

## Tutorial 25: Packaging for Distribution

**What you'll learn:** How to use Creator's PyInstaller integration to build a single
self-contained executable, what is included in the bundle, and how to distribute it to
users who do not have Python installed.

### Why packaging matters

Distributing a Python application normally requires the recipient to install Python, create
a virtual environment, and install dependencies. For a developer tool like Creator, that is
acceptable. For an application you build with Creator — a custom AI assistant, a document
processor, an automated workflow — most users will not do this.

PyInstaller bundles the Python interpreter, all dependencies, and your application into a
single executable file. The user double-clicks it (or runs it from a terminal) and it just
works. No Python required on the target machine.

### What is included in the bundle

When you package Creator itself (or an exported Creator project), the bundle includes:

- All Python source files and compiled `.pyc` bytecode
- The PySide6 Qt libraries (for Creator's own UI)
- All help documents and tutorial Markdown files
- Translation `.qm` files for all supported locales
- Jinja2 templates used for code generation
- Your exported project's `generated/` and `custom/` directories (if packaging an export)

The resulting executable is large (typically 80–200 MB) because Qt libraries alone are
substantial. This is normal and expected for Qt applications.

### Step-by-step

**Step 1: Install PyInstaller.**

PyInstaller is not installed by default. Install it in your virtual environment:

```bash
pip install pyinstaller
```

Verify the installation:
```bash
pyinstaller --version
```

**Step 2: Package for your current platform.**

Creator ships with packaging scripts in `scripts/`:

For Linux:
```bash
bash scripts/package.sh linux
```

For macOS:
```bash
bash scripts/package.sh macos
```

For Windows (run in a Windows terminal or PowerShell):
```bash
bash scripts/package.sh windows
```

The script runs PyInstaller with the appropriate spec file. Output goes to `dist/`.

**Step 3: Locate the output.**

| Platform | Output |
|---|---|
| Linux | `dist/pocketflow-creator` (single executable) |
| macOS | `dist/PocketFlow Creator.app` (application bundle) |
| Windows | `dist/pocketflow-creator.exe` (single executable) |

**Step 4: Test the executable.**

Run the output directly from `dist/` without Creator running in the background:

```bash
# Linux / macOS
./dist/pocketflow-creator

# Windows
dist\pocketflow-creator.exe
```

Verify that the UI opens, a new project can be created, and the help browser works
(it reads from the bundled Markdown files, not from your source tree).

**Step 5: Distribute.**

Copy the output file to the target machine. No installation is required. On macOS, users
may need to right-click → Open the first time to bypass Gatekeeper.

**Packaging an exported project (not Creator itself):**

If you want to distribute the flow you built — not Creator — export it first (Tutorial 21),
then write a minimal PyInstaller spec for the exported `main.py`. A typical spec:

```python
# my_flow.spec
a = Analysis(
    ["main.py"],
    pathex=["exports/my_flow"],
    datas=[("custom", "custom"), ("generated", "generated")],
    hiddenimports=["pocketflow"],
)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, name="my_flow")
```

Build with:
```bash
pyinstaller my_flow.spec
```

**Troubleshooting common packaging issues:**

- **Missing module at runtime:** Add it to `hiddenimports` in the spec file.
- **Missing data file:** Add it to `datas` as a `(src, dest)` tuple.
- **File too large:** Use `--exclude-module` to drop unused heavy dependencies (e.g., `tkinter`).
- **Permission denied on Linux:** Run `chmod +x dist/pocketflow-creator` after packaging.

---

[→ Continue to Part 4 — Exercises](part4_exercises.md)
