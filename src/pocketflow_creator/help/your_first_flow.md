# Your First Flow

This guide walks you through building a complete Hello World flow — a single LLM node that
answers a question — from an empty project to a running, exportable PocketFlow application.

**Time:** ~15 minutes  
**Prerequisites:** Application installed and launched. See [Getting Started](getting_started.md).

---

## Step 1 — Create a New Project

1. Choose **File > New Project…**
2. Enter project name: `HelloWorld`
3. Choose a folder for the project files
4. Click **OK**

The Project Explorer now shows:
```
HelloWorld/
  graphs/
  prompts/
  node_types/
  tools/
```

---

## Step 2 — Create a New Flow

1. Choose **Flow > New Flow…**
2. Name it `main`
3. Click **OK**

A blank canvas appears and `graphs/main.pfcgraph.yaml` appears in the Project Explorer.

---

## Step 3 — Add a Start Node

1. In the **Component Palette** (left panel), find **Start Node**
2. Drag it onto the canvas

The Start Node appears as a rounded rectangle with a green port on its right edge.
It is automatically set as the flow's start node.

---

## Step 4 — Add an LLM Node

1. In the Component Palette, find **LLM Node**
2. Drag it to the right of the Start Node
3. In the **Object Inspector** (right panel), set:
   - **Title:** `Ask LLM`
   - **Prompt File:** `prompts/hello.md` *(type the path; the file will be created)*

---

## Step 5 — Connect the Nodes

1. Hover over the Start Node until its `default` action port (right edge) turns blue
2. Click and drag from that port to the LLM Node's input port (left edge)
3. Release — an edge labelled **default** appears

---

## Step 6 — Add a Stop Node

1. Drag a **Stop Node** from the palette to the right of the LLM Node
2. Connect the LLM Node's `default` action port to the Stop Node's input port

Your canvas should now look like:

```
[Start] --default--> [Ask LLM] --default--> [Stop]
```

---

## Step 7 — Write the Prompt

1. In the Project Explorer, double-click `prompts/hello.md`
2. The **Markdown** editor tab opens
3. Type:

```markdown
You are a helpful assistant.

Answer this question in one sentence:

What is PocketFlow?
```

4. Press **Ctrl+S** to save

---

## Step 8 — Validate

1. Choose **Project > Validate Project** (or **Ctrl+Shift+V**)
2. The status bar should show: `Validation passed — 0 errors`

If you see red badges on nodes, click the node to read the error in the Object Inspector,
fix the property, and validate again.

---

## Step 9 — Run

1. Choose **Run > Run Active Flow** (or **F5**)
2. Switch to the **Run Log** tab at the bottom
3. You will see one entry per node executed, with the shared store state before and after

If you have Ollama running locally the LLM Node will call it. Otherwise configure a provider
in **Tools > Provider Manager** or accept the Mock Provider output for testing.

---

## Step 10 — Export

1. Choose **File > Export PocketFlow Project…**
2. PocketFlow Creator writes a standalone Python package to `exports/HelloWorld/`
3. Run it independently:

```bash
cd exports/HelloWorld
pip install -e .
python main.py
```

---

## What You Built

| File | Purpose |
|---|---|
| `graphs/main.pfcgraph.yaml` | Graph structure — nodes, edges, properties |
| `prompts/hello.md` | LLM prompt (Markdown, never overwritten on re-export) |
| `exports/HelloWorld/generated/nodes.py` | Generated node class stubs |
| `exports/HelloWorld/generated/flow.py` | Generated PocketFlow wiring code |
| `exports/HelloWorld/custom/` | Your hand-edited node implementations |

---

## Next Steps

- [Tutorial 3: Using the Properties Inspector](tutorials/part1_fundamentals.md#tutorial-3-using-the-properties-inspector)
- [Tutorial 4: The Code Editor — RAD Node Coding](tutorials/part1_fundamentals.md#tutorial-4-the-code-editor--rad-node-coding)
- [Tutorial 7: Hello World — Single Node Q&A](tutorials/part2_patterns.md#tutorial-7-hello-world--single-node-qa)
