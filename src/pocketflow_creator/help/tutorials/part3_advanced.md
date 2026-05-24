# Part 3 — Advanced Creator Features

[← Tutorials Index](index.md)

---

## Tutorial 18: Validation and Error Badges

**What you'll learn:** Use the validator to find graph problems before running.

### Common Validation Errors

| Code | Meaning | Fix |
|---|---|---|
| PFCE1001 | No start node set | Mark a node as the flow's start node via Flow > Set Start Node |
| PFCE1002 | Duplicate node IDs | Delete and re-add the duplicate node |
| PFCE1003 | Start node ID doesn't exist | Re-set the start node |
| PFCE2001 | Edge source node missing | Re-wire or delete the dangling edge |
| PFCE2002 | Edge destination node missing | Re-wire or delete the dangling edge |
| PFCE2003 | Edge has no action label | Click the edge; add an action label |
| PFCE2101 | Action not declared on source node | Add the action to the node's Actions field in Inspector |
| PFCE2102 | Subflow node missing `subflow_ref` | Set `subflow_ref` in Inspector |

### Steps

1. Create a new project, add a Basic Node, leave it unwired
2. Project > Validate Project (Ctrl+Shift+V) — observe errors in the Problems tab
3. Notice red border badges on nodes with errors
4. Fix each error by editing properties or adding edges
5. Re-validate — badges clear when all errors are resolved

**Tip:** Validation runs automatically before Run and before Export. You cannot run a graph with active validation errors.

---

## Tutorial 19: Debug Mode and Breakpoints

**What you'll learn:** Step through a running flow node by node, inspect shared-store state at each point.

### Steps

1. Open the project from Tutorial 7 (Hello World)
2. Click the **Ask LLM** node to select it
3. Node > Toggle Breakpoint (F9) — a red dot appears in the node's corner
4. Run > Debug Active Flow (Shift+F5)
   - The flow runs until it reaches Ask LLM and pauses
5. Check the **Shared Store** tab — see values accumulated so far
6. Check the **Run Log** tab — completed steps are listed
7. Run > Resume to continue past the breakpoint
8. Run > Stop to abort the debug session

**Tip:** Set breakpoints on any node where you want to inspect state. Multiple breakpoints in a loop let you watch variables change on each iteration.

---

## Tutorial 20: Subflow Composition

**What you'll learn:** Embed a reusable sub-graph inside a parent flow using the Subflow Node.

### Steps

1. Create a project with two graphs:
   - `graphs/main.pfcgraph.yaml` — the parent flow
   - `graphs/summarizer.pfcgraph.yaml` — a reusable summarization sub-flow

2. Build `summarizer.pfcgraph.yaml`:
   - Start → Load Text → Summarize (LLM) → Stop

3. In `main.pfcgraph.yaml`, add a **Subflow Node**:
   - Drag **Subflow Node** from the palette
   - In Inspector, the **[Subflow]** section appears
   - Set `subflow_ref` to `graphs/summarizer.pfcgraph.yaml`

4. Validate — if `subflow_ref` is set correctly, no PFCE2102 error appears

5. Wire parent flow around the Subflow Node as usual

6. Run > Run Active Flow — the runner executes the subgraph's nodes inline
   and merges the subgraph's shared store state back into the parent

---

## Tutorial 21: Exporting and Running a Standalone Project

**What you'll learn:** Export a Creator project as a runnable Python package independent of Creator.

### Steps

1. Open any completed project (e.g., Tutorial 7)
2. File > Export PocketFlow Project… (Ctrl+E)
3. The exporter writes to `exports/<package_name>/`:

```
exports/hello_world/
├── generated/
│   ├── main_nodes.py       ← auto-generated Node subclasses
│   └── main_flow.py        ← wires the flow with >> syntax
├── custom/
│   └── main_custom.py      ← YOUR code (never overwritten)
├── tests/
│   └── test_main.py
└── main.py
```

4. Re-exporting: `generated/` is always overwritten; `custom/` is **never** touched
5. Run outside Creator:

```bash
cd exports/hello_world
pip install pocketflow
python main.py
```

---

## Tutorial 22: Shared Store Designer

**What you'll learn:** Define the shared-store schema to document and validate data contracts between nodes.

### Steps

1. Open a project in Creator
2. In Project Explorer, double-click **Shared Store**
3. The Shared Store Designer opens with columns: **Namespace**, **Key**, **Type**, **Default**
4. Add rows for your flow:

| Namespace | Key | Type | Default |
|---|---|---|---|
| user | question | string | |
| llm | response | string | |
| llm | model | string | gpt-4o |
| data | items | array | |

5. Click **Validate** to check type names are valid JSON Schema types
6. Click **OK** — the schema is stored in `project.pfcproj.yaml`
7. Use the **Shared Store** tab during a run to observe live values

---

## Tutorial 25: Packaging for Distribution

**What you'll learn:** Use the PyInstaller spec files to create a self-contained executable.

### Steps

1. Install PyInstaller:

```bash
pip install pyinstaller
```

2. Build for Linux:

```bash
bash scripts/package.sh linux
```

Output: `dist/pocketflow-creator` (single executable)

3. Build for Windows (on a Windows host):

```bash
bash scripts/package.sh windows
```

Output: `dist/pocketflow-creator.exe`

4. Share the executable — no Python installation required on the target machine

### What's Included in the Bundle

The spec files include:
- All application source files
- PySide6 Qt libraries
- All help documents and tutorials
- Translation `.qm` files (all locales)
- Jinja2 templates for code generation

---

[→ Continue to Part 4 — Exercises](part4_exercises.md)
