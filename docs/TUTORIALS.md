# PocketFlow Creator — Tutorials

This document provides step-by-step tutorials for every major feature of PocketFlow Creator
and every core pattern from the PocketFlow framework. Work through Part 1 first to learn
the IDE; then pick any Part 2 or Part 3 tutorial in any order.

---

## How to Read These Tutorials

Each tutorial lists:
- **What you'll learn** — the skill or pattern covered
- **Prerequisites** — what to complete first
- **Step-by-step instructions** — exact UI actions
- **Expected result** — what success looks like

Node properties shown as `Property: value` are set in the **Object Inspector** panel (right side).
Code shown in `code blocks` is written in the **Python editor** tab (bottom panel).

---

# Part 1 — Getting Started with PocketFlow Creator

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
   - In Object Inspector, change **Title** to `Start` (click the blue value field, type, press Enter)

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
   - Project Explorer > right-click `prompts` folder > New File (or create manually)
   - Or: open the **Markdown** tab at bottom, type: `Say hello to the world in one sentence.`
   - Save (Ctrl+S) to `prompts/hello.md`

8. **Validate the graph**
   - Project > Validate Project (Ctrl+Shift+V)
   - Problems tab shows any errors (red border on nodes with issues)

9. **Run with mock provider**
   - Run > Run Active Flow (F5)
   - Check **Run Log** tab — you'll see one step per node

**Expected result:** Three nodes on canvas, green (no error badges), run log shows Start → Ask LLM → End.

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
   - The validator now expects edges with labels `success` or `failure` leaving this node
3. Change **Reads** to `user_input`
4. Change **Writes** to `llm_response`

Notice how the canvas updates live (title changes show immediately; action changes may trigger validation badges if wired edges don't match).

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
        # Read the prompt template from disk
        prompt_path = shared.get("prompt_file", "prompts/hello.md")
        with open(prompt_path) as f:
            return f.read()

    def exec(self, prep_res: str) -> str:
        # Call the LLM (injected via shared["llm"])
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
        # Replace with a real sentiment model
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

# Part 2 — PocketFlow Patterns in Creator

Each tutorial in this section maps a PocketFlow cookbook example to a Creator project.

---

## Tutorial 7: Hello World — Single Node Q&A

**PocketFlow example:** `pocketflow-hello-world`
**What you'll learn:** The simplest possible flow: one question, one answer.

### Graph

```
[Start] --default--> [AskLLM] --default--> [Stop]
```

### Steps

1. New project: `tut_hello_world`
2. Add nodes: Start, LLM Prompt Node (title: `Ask LLM`), Stop Node
3. Wire: Start → Ask LLM (action: `default`), Ask LLM → Stop (action: `default`)
4. Auto Layout; Zoom to Fit
5. Double-click **Ask LLM** to open code editor

```python
class AskLlm(Node):
    def prep(self, shared):
        return shared.get("question", "What is PocketFlow?")

    def exec(self, prep_res):
        return call_llm(prep_res)  # your LLM helper

    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res
        print("Answer:", exec_res)
        return "default"
```

6. Create `prompts/main.md`:
   ```
   Answer the following question concisely: {question}
   ```
7. Run > Run Active Flow — check Run Log and Shared Store tabs

---

## Tutorial 8: Chat with History

**PocketFlow example:** `pocketflow-chat`
**What you'll learn:** Maintain conversation history in the shared store across turns.

### Graph

```
[Start] --default--> [GetInput] --continue--> [CallLLM] --default--> [PrintReply]
                                    ^                                      |
                                    └──────────────────────────────────────┘
                                              (loop back)
[GetInput] --exit--> [Stop]
```

### Steps

1. New project: `tut_chat`
2. Add nodes:
   - **Start Node** (title: `Start`)
   - **Basic Node** (title: `Get Input`) — Actions: `continue, exit`
   - **LLM Prompt Node** (title: `Call LLM`) — Actions: `default`
   - **Basic Node** (title: `Print Reply`) — Actions: `default`
   - **Stop Node** (title: `Stop`)
3. Wire edges:
   - Start → Get Input (`default`)
   - Get Input → Call LLM (`continue`)
   - Get Input → Stop (`exit`)
   - Call LLM → Print Reply (`default`)
   - Print Reply → Get Input (`default`)  ← this creates the loop
4. Auto Layout; notice the loop in the graph
5. Double-click **Get Input**:

```python
class GetInput(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        user_input = input("You: ").strip()
        return user_input

    def post(self, shared, prep_res, exec_res):
        if exec_res.lower() in ("quit", "exit", "bye"):
            return "exit"
        shared.setdefault("history", [])
        shared["history"].append({"role": "user", "content": exec_res})
        return "continue"
```

6. Double-click **Call LLM**:

```python
class CallLlm(Node):
    def prep(self, shared):
        return shared.get("history", [])

    def exec(self, prep_res):
        return call_llm_with_history(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["history"].append({"role": "assistant", "content": exec_res})
        shared["last_reply"] = exec_res
        return "default"
```

7. Double-click **Print Reply**:

```python
class PrintReply(Node):
    def prep(self, shared):
        return shared.get("last_reply", "")

    def exec(self, prep_res):
        print(f"Assistant: {prep_res}")
        return None

    def post(self, shared, prep_res, exec_res):
        return "default"
```

8. Run > Debug Active Flow; step through the loop

---

## Tutorial 9: Structured Output — Resume Data Extraction

**PocketFlow example:** `pocketflow-structured-output`
**What you'll learn:** Use an LLM to extract typed fields from unstructured text.

### Graph

```
[Start] --default--> [LoadResume] --default--> [ExtractFields] --default--> [ValidateOutput] --default--> [Stop]
```

### Steps

1. New project: `tut_structured_output`
2. Add nodes: Start, Basic Node × 3 (Load Resume, Extract Fields, Validate Output), Stop
3. Wire sequentially with `default` actions
4. In Object Inspector for **Extract Fields**:
   - Reads: `resume_text`
   - Writes: `extracted_data`

5. Double-click **Load Resume**:

```python
class LoadResume(Node):
    def prep(self, shared):
        return shared.get("resume_path", "sample_resume.txt")

    def exec(self, prep_res):
        with open(prep_res) as f:
            return f.read()

    def post(self, shared, prep_res, exec_res):
        shared["resume_text"] = exec_res
        return "default"
```

6. Double-click **Extract Fields**:

```python
class ExtractFields(Node):
    def prep(self, shared):
        return shared["resume_text"]

    def exec(self, prep_res):
        prompt = f"""Extract from this resume:
- name
- email
- years_of_experience (number)
- skills (list)

Resume:
{prep_res}

Respond as JSON only."""
        raw = call_llm(prompt)
        import json
        return json.loads(raw)

    def post(self, shared, prep_res, exec_res):
        shared["extracted_data"] = exec_res
        return "default"
```

7. Use the **Shared Store Designer** (Tools > Shared Store Inspector) to define the schema:
   - Key: `extracted_data`, Type: `object`
   - Key: `resume_text`, Type: `string`

---

## Tutorial 10: Multi-Stage Workflow — Article Writer

**PocketFlow example:** `pocketflow-workflow`
**What you'll learn:** Chain LLM calls through distinct stages: outline → draft → style.

### Graph

```
[Start] → [GenerateOutline] → [WriteDraft] → [ApplyStyle] → [Save] → [Stop]
```

### Steps

1. New project: `tut_workflow`
2. Add five nodes (Start, 3× LLM Prompt Node, Stop)
3. Set titles: `Generate Outline`, `Write Draft`, `Apply Style`
4. For each LLM node, set a separate prompt file:
   - `prompts/outline.md`
   - `prompts/draft.md`
   - `prompts/style.md`
5. Wire sequentially; Auto Layout
6. Create `prompts/outline.md`:
   ```
   Create a 5-point outline for an article about: {topic}
   Return only the outline as a numbered list.
   ```
7. Create `prompts/draft.md`:
   ```
   Write a 3-paragraph article using this outline:
   {outline}
   ```
8. Create `prompts/style.md`:
   ```
   Rewrite this article in an engaging, professional tone:
   {draft}
   ```
9. Double-click **Generate Outline**:

```python
class GenerateOutline(Node):
    def prep(self, shared):
        topic = shared.get("topic", "the future of AI")
        return open("prompts/outline.md").read().format(topic=topic)

    def exec(self, prep_res):
        return call_llm(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["outline"] = exec_res
        return "default"
```

10. Implement Write Draft and Apply Style similarly, reading `outline` / `draft` from shared store

---

## Tutorial 11: Conditional Routing — Chat Guardrail

**PocketFlow example:** `pocketflow-chat-guardrail`
**What you'll learn:** Use a Router Node to branch flow based on LLM classification.

### Graph

```
[Start] → [ClassifyInput] ──on_topic──→ [AnswerQuestion] → [Stop]
                          └─off_topic──→ [Redirect]       → [Stop]
```

### Steps

1. New project: `tut_guardrail`
2. Add nodes:
   - **Start Node**
   - **Router Node** (title: `Classify Input`) — Actions: `on_topic, off_topic`
   - **LLM Prompt Node** (title: `Answer Question`)
   - **Basic Node** (title: `Redirect`)
   - **Stop Node**
3. Wire:
   - Start → Classify Input (`default`)
   - Classify Input → Answer Question (`on_topic`)
   - Classify Input → Redirect (`off_topic`)
   - Answer Question → Stop (`default`)
   - Redirect → Stop (`default`)
4. Double-click **Classify Input**:

```python
class ClassifyInput(Node):
    def prep(self, shared):
        return shared.get("user_question", "")

    def exec(self, prep_res):
        prompt = f"""Is this question about travel? Answer only YES or NO.
Question: {prep_res}"""
        answer = call_llm(prompt).strip().upper()
        return "on_topic" if answer == "YES" else "off_topic"

    def post(self, shared, prep_res, exec_res):
        return exec_res  # routes the flow
```

5. Notice: the Router Node's `post()` return value selects which edge to follow
6. Validate — the validator checks that `on_topic` and `off_topic` edges exist from Classify Input
7. Run > Validate Project — confirms routing is correct

---

## Tutorial 12: Agent with Tools

**PocketFlow example:** `pocketflow-agent`
**What you'll learn:** Build an LLM agent that decides which tool to call based on a question.

### Graph

```
[Start] → [Decide] ──search──→ [WebSearch]  → [Decide]
                  └─calculate──→ [Calculator] → [Decide]
                  └─answer────→ [FinalAnswer] → [Stop]
```

### Steps

1. New project: `tut_agent`
2. Add nodes:
   - Start, Router Node (title: `Decide`, Actions: `search, calculate, answer`)
   - Basic Node × 2 (Web Search, Calculator)
   - Basic Node (Final Answer)
   - Stop
3. Wire the loop: Web Search → Decide, Calculator → Decide
4. Wire the exit: Final Answer → Stop
5. Double-click **Decide**:

```python
class Decide(Node):
    TOOLS = ["search", "calculate", "answer"]

    def prep(self, shared):
        history = shared.get("tool_history", [])
        question = shared.get("question", "")
        return question, history

    def exec(self, prep_res):
        question, history = prep_res
        history_text = "\n".join(f"- {h}" for h in history)
        prompt = f"""Question: {question}
Previous steps: {history_text or 'none'}
Choose the next action: search, calculate, or answer."""
        action = call_llm(prompt).strip().lower()
        return action if action in self.TOOLS else "answer"

    def post(self, shared, prep_res, exec_res):
        shared.setdefault("tool_history", []).append(f"chose: {exec_res}")
        return exec_res
```

6. Double-click **Web Search**:

```python
class WebSearch(Node):
    def prep(self, shared):
        return shared.get("question", "")

    def exec(self, prep_res):
        # Replace with real search API
        return f"[search result for: {prep_res}]"

    def post(self, shared, prep_res, exec_res):
        shared["search_result"] = exec_res
        shared["tool_history"].append(f"searched: {exec_res}")
        return "default"
```

---

## Tutorial 13: Retrieval-Augmented Generation (RAG)

**PocketFlow example:** `pocketflow-rag`
**What you'll learn:** Index documents, retrieve relevant chunks, generate an answer.

### Graph

```
[Start] → [LoadDocs] → [EmbedChunks] → [StoreIndex] → [GetQuestion]
        → [RetrieveChunks] → [GenerateAnswer] → [Stop]
```

### Steps

1. New project: `tut_rag`
2. Add nodes for each stage; set Reads/Writes in Inspector:
   - **Load Docs** — Writes: `raw_docs`
   - **Embed Chunks** — Reads: `raw_docs`, Writes: `chunks, embeddings`
   - **Store Index** — Reads: `chunks, embeddings`, Writes: `index`
   - **Get Question** — Writes: `question`
   - **Retrieve Chunks** — Reads: `index, question`, Writes: `context`
   - **Generate Answer** — Reads: `context, question`, Writes: `answer`

3. Double-click **Load Docs** and implement document loading
4. Double-click **Embed Chunks**:

```python
class EmbedChunks(Node):
    def prep(self, shared):
        text = shared["raw_docs"]
        # Split into 500-char chunks
        return [text[i:i+500] for i in range(0, len(text), 500)]

    def exec(self, prep_res):
        # Replace with a real embedding model
        return [(chunk, [0.1] * 128) for chunk in prep_res]

    def post(self, shared, prep_res, exec_res):
        shared["chunks"] = [c for c, _ in exec_res]
        shared["embeddings"] = [e for _, e in exec_res]
        return "default"
```

5. Double-click **Generate Answer**:

```python
class GenerateAnswer(Node):
    def prep(self, shared):
        context = "\n".join(shared.get("context", []))
        question = shared.get("question", "")
        return f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"

    def exec(self, prep_res):
        return call_llm(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res
        print("Answer:", exec_res)
        return "default"
```

---

## Tutorial 14: Map-Reduce / Batch Processing

**PocketFlow example:** `pocketflow-map-reduce`
**What you'll learn:** Use a Batch Node to process many items in parallel and reduce results.

### Graph

```
[Start] → [LoadItems] → [ProcessEach (BatchNode)] → [Aggregate] → [Stop]
```

### Steps

1. New project: `tut_map_reduce`
2. Add nodes: Start, Basic Node (Load Items), **Batch Node** (Process Each), Basic Node (Aggregate), Stop
3. Double-click **Load Items**:

```python
class LoadItems(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        # Load a list of items to evaluate
        return ["Resume A text...", "Resume B text...", "Resume C text..."]

    def post(self, shared, prep_res, exec_res):
        shared["items"] = exec_res
        return "default"
```

4. Double-click **Process Each** (BatchNode):

```python
class ProcessEach(BatchNode):
    def prep(self, shared):
        # Return the list — BatchNode calls exec once per item
        return shared["items"]

    def exec(self, item):
        prompt = f"Rate this resume 1-10 and explain why:\n{item}"
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        # exec_res is a list of results, one per item
        shared["ratings"] = exec_res
        return "default"
```

5. Double-click **Aggregate**:

```python
class Aggregate(Node):
    def prep(self, shared):
        return shared.get("ratings", [])

    def exec(self, prep_res):
        prompt = f"Summarise these {len(prep_res)} resume evaluations:\n" + \
                 "\n".join(f"{i+1}. {r}" for i, r in enumerate(prep_res))
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["summary"] = exec_res
        return "default"
```

---

## Tutorial 15: Human-in-the-Loop

**PocketFlow example:** `pocketflow-fastapi-hitl` / `pocketflow-cli-hitl`
**What you'll learn:** Pause execution at a Human Review Node for user approval before continuing.

### Graph

```
[Start] → [DraftContent] → [Human Review] ──approved──→ [Publish] → [Stop]
                                           └─rejected────→ [Revise]  → [Human Review]
```

### Steps

1. New project: `tut_hitl`
2. Add nodes:
   - Start, LLM Prompt (Draft Content)
   - **Human Review Node** (title: `Review Draft`) — Actions: `approved, rejected`
   - Basic Node (Publish), Basic Node (Revise), Stop
3. Wire with the approval loop (Revise → Review Draft)
4. Double-click **Review Draft**:

```python
class ReviewDraft(Node):
    def prep(self, shared):
        return shared.get("draft", "")

    def exec(self, prep_res):
        print("\n=== DRAFT FOR REVIEW ===")
        print(prep_res)
        print("=========================")
        decision = input("Approve? (yes/no): ").strip().lower()
        return decision

    def post(self, shared, prep_res, exec_res):
        if exec_res in ("yes", "y", "approve", "approved"):
            return "approved"
        feedback = input("Feedback for revision: ").strip()
        shared["feedback"] = feedback
        return "rejected"
```

5. Double-click **Revise**:

```python
class Revise(Node):
    def prep(self, shared):
        return shared.get("draft", ""), shared.get("feedback", "")

    def exec(self, prep_res):
        draft, feedback = prep_res
        prompt = f"Revise this draft based on feedback:\nDraft: {draft}\nFeedback: {feedback}"
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["draft"] = exec_res
        return "default"
```

6. Run > Debug Active Flow to step through with breakpoints at Review Draft

---

## Tutorial 16: LLM-as-Judge / Evaluator Loop

**PocketFlow example:** `pocketflow-judge`
**What you'll learn:** Use one LLM to generate content and another to evaluate and improve it.

### Graph

```
[Start] → [Generate] → [Evaluate] ──pass────→ [Stop]
                    ^              └─fail──────→ [Refine] → [Generate]
```

### Steps

1. New project: `tut_judge`
2. Add nodes:
   - Start, LLM Prompt (Generate), Router Node (Evaluate, Actions: `pass, fail`),
     LLM Prompt (Refine), Stop
3. Wire with loop: Refine → Generate
4. Add a safety counter in shared store to prevent infinite loops:

```python
class Evaluate(Node):
    MAX_ITERATIONS = 3

    def prep(self, shared):
        return shared.get("output", ""), shared.get("iteration", 0)

    def exec(self, prep_res):
        output, iteration = prep_res
        if iteration >= self.MAX_ITERATIONS:
            return "pass"  # force exit after max iterations
        prompt = f"""Evaluate this output. Is the quality good enough?
Output: {output}
Answer only PASS or FAIL."""
        verdict = call_llm(prompt).strip().upper()
        return "pass" if verdict == "PASS" else "fail"

    def post(self, shared, prep_res, exec_res):
        shared["iteration"] = shared.get("iteration", 0) + 1
        return exec_res
```

---

## Tutorial 17: Multi-Agent System

**PocketFlow example:** `pocketflow-multi-agent` / `pocketflow-debate`
**What you'll learn:** Two agents with different roles run in a debate or adversarial pattern.

### Graph

```
[Start] → [AgentA: Propose] → [AgentB: Challenge] → [Judge] ──continue──→ [AgentA]
                                                             └─conclude────→ [Summary] → [Stop]
```

### Steps

1. New project: `tut_debate`
2. Add nodes with descriptive titles; set Actions appropriately
3. Double-click **Agent A: Propose**:

```python
class AgentAPropose(Node):
    def prep(self, shared):
        topic = shared.get("topic", "AI regulation")
        history = shared.get("debate_history", [])
        return topic, history

    def exec(self, prep_res):
        topic, history = prep_res
        context = "\n".join(history[-4:])  # last 4 turns
        prompt = f"""You are arguing IN FAVOR of: {topic}
Previous debate:
{context}
Make your strongest argument (2-3 sentences):"""
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared.setdefault("debate_history", []).append(f"PRO: {exec_res}")
        return "default"
```

4. Implement Agent B as the counter-argument and Judge to evaluate the winner
5. Run > Run Active Flow to watch the debate unfold in Run Log

---

# Part 3 — Advanced Creator Features

---

## Tutorial 18: Validation and Error Badges

**What you'll learn:** Use the validator to find graph problems before running.

### Common Validation Errors

| Error Code | Meaning | Fix |
|---|---|---|
| PFCE1001 | No start node set | Mark a node as the flow's start node |
| PFCE1002 | Duplicate node IDs | Delete and re-add the duplicate node |
| PFCE1003 | Start node ID doesn't exist | Re-set the start node |
| PFCE2001 | Edge source node missing | Re-wire or delete the dangling edge |
| PFCE2002 | Edge destination node missing | Re-wire or delete the dangling edge |
| PFCE2003 | Edge has no action label | Add an action label to the edge |
| PFCE2101 | Action not declared on source node | Add the action to the node's Actions field |
| PFCE2102 | Subflow node missing `subflow_ref` | Set `subflow_ref` in Inspector |

### Steps

1. Create a new project, add a Basic Node, leave it unwired
2. Project > Validate Project (Ctrl+Shift+V) — observe errors in the Problems tab
3. Notice red border badges on the canvas nodes with errors
4. Fix each error by editing properties or adding edges
5. Re-validate — badges clear when all errors are resolved

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
6. Check the **Run Log** tab — steps completed are listed
7. Run > Resume (or click the Resume button) to continue
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
   - In Object Inspector, the **[Subflow]** section appears
   - Set `subflow_ref` to `graphs/summarizer.pfcgraph.yaml`

4. Validate — if `subflow_ref` is set correctly, no PFCE2102 error appears

5. Wire parent flow around the Subflow Node as usual

> **Note:** Subflow recursive execution is a planned enhancement (T-B05 MVP — passthrough only).
> The `subflow_ref` property documents intent and passes through the runner with the ref recorded
> in the shared store.

---

## Tutorial 21: Exporting and Running a Standalone Project

**What you'll learn:** Export a Creator project as a runnable Python package independent of Creator.

### Steps

1. Open any completed project (e.g., Tutorial 7 Hello World)
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
   │   └── test_main.py        ← test scaffolding
   └── main.py                 ← entry point
   ```
4. Re-exporting: `generated/` is always overwritten; `custom/` is never touched
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
2. In Project Explorer, double-click **Shared Store** (under the project root)
3. The Shared Store Designer dialog opens with a table:
   - **Namespace** — group keys by domain (e.g., `llm`, `user`, `data`)
   - **Key** — the dict key
   - **Type** — `string`, `integer`, `number`, `boolean`, `array`, `object`, `null`
   - **Default** — initial value if not set by any node

4. Add rows for your flow:
   | Namespace | Key | Type | Default |
   |---|---|---|---|
   | user | question | string | |
   | llm | response | string | |
   | llm | model | string | gpt-4o |
   | data | items | array | |

5. Click **Validate** to check type names are valid JSON Schema types
6. Click **OK** to save — the schema is stored in `project.pfcproj.yaml`

7. Use the **Shared Store** tab during a run to observe live values matching your schema

---

## Tutorial 23: Streaming Output

**PocketFlow example:** `pocketflow-streaming`
**What you'll learn:** Design a flow that produces incremental output visible to the user in real time.

### Graph

```
[Start] → [StreamLLM] → [PrintChunks] → [Stop]
```

### Steps

1. New project: `tut_streaming`
2. Add a Basic Node (title: `Stream LLM`) with Writes: `chunks`
3. Double-click **Stream LLM**:

```python
class StreamLlm(Node):
    def prep(self, shared):
        return shared.get("prompt", "Tell me a story in 5 sentences.")

    def exec(self, prep_res):
        # Replace with your streaming LLM client
        full_text = call_llm(prep_res)
        # Simulate streaming by splitting into words
        return full_text.split()

    def post(self, shared, prep_res, exec_res):
        shared["chunks"] = exec_res
        for chunk in exec_res:
            print(chunk, end=" ", flush=True)
        print()
        return "default"
```

4. In Run Log during execution, watch chunks accumulate in the Shared Store tab

---

## Tutorial 24: Memory — Short-Term and Long-Term Context

**PocketFlow example:** `pocketflow-memory`
**What you'll learn:** Maintain two memory layers — recent conversation (short-term) and condensed summaries (long-term).

### Graph

```
[Start] → [GetInput] → [UpdateShortTerm] → [ShouldCondense?]
    ──yes──→ [CondenseToLongTerm] → [CallLLM] → [GetInput]
    ──no───→                        [CallLLM] → [GetInput]
[GetInput] --exit--> [Stop]
```

### Steps

1. New project: `tut_memory`
2. Build the graph with a Router Node for `ShouldCondense?` (Actions: `yes, no`)
3. In Shared Store Designer, define:
   - `short_term_history` (array) — last N messages
   - `long_term_summary` (string) — condensed prior context
   - `condensation_threshold` (integer, default: 10)

4. Double-click **Should Condense?**:

```python
class ShouldCondense(Node):
    THRESHOLD = 10

    def prep(self, shared):
        return len(shared.get("short_term_history", []))

    def exec(self, prep_res):
        return "yes" if prep_res >= self.THRESHOLD else "no"

    def post(self, shared, prep_res, exec_res):
        return exec_res
```

5. Double-click **Condense To Long Term**:

```python
class CondenseToLongTerm(Node):
    def prep(self, shared):
        history = shared.get("short_term_history", [])
        old_summary = shared.get("long_term_summary", "")
        return history, old_summary

    def exec(self, prep_res):
        history, old_summary = prep_res
        msgs = "\n".join(f"{m['role']}: {m['content']}" for m in history)
        prompt = f"Existing summary: {old_summary}\n\nNew messages:\n{msgs}\n\nCreate updated summary:"
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["long_term_summary"] = exec_res
        shared["short_term_history"] = []  # reset short-term
        return "default"
```

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

---

# Part 4 — Creator System Exercises

These exercises combine multiple features and require you to build something non-trivial.

---

## Exercise A: Build a Complete News Summariser

**Skills exercised:** Multi-stage workflow, LLM chaining, Shared Store Designer, custom node type, export and run

**Objective:** Fetch news headlines, summarise each one, and produce a daily digest.

1. Create project `news_summariser`
2. Design the graph:
   - Fetch Headlines (Basic Node) — fetches from an RSS feed or static list
   - **Summarise Each** (Batch Node) — one LLM call per headline
   - Rank Headlines (Router Node) — routes `important` vs `routine`
   - Format Digest (Basic Node) — assembles the final output
   - Save Report (Basic Node) — writes to `output/digest.md`
3. Create a custom node type `rss_reader_node`:
   - Property: `feed_url` (string)
   - Action: `default`
4. Implement all node code via double-click
5. Define shared store schema for `headlines` (array), `summaries` (array), `digest` (string)
6. Validate, run with Mock Provider, inspect Run Log
7. Export and run standalone

---

## Exercise B: Coding Agent with Memory

**Skills exercised:** Agentic loop, tool nodes, subflow, breakpoints, debug stepping

**Objective:** Build an agent that can write, test, and fix simple Python code.

1. Create project `coding_agent`
2. Design the agent loop:
   - Get Task → Plan → Write Code → Run Tests (Human Review Node) → Fix Errors → Done
3. Add a **Subflow Node** embedding a `fix_loop.pfcgraph.yaml` sub-graph
4. Implement **Run Tests** as a Human Review Node that shows test output and asks for approval
5. Set breakpoints at Write Code and Fix Errors to debug iteratively
6. Use Debug Mode to inspect the shared store after each code generation step

---

## Exercise C: Multi-Provider LLM Router

**Skills exercised:** Custom node types, Router Node, Inspector properties, validation

**Objective:** Route LLM requests to different providers based on task type.

1. Create a custom node type `llm_router_node`:
   - Properties: `fast_model` (string), `smart_model` (string), `threshold` (integer)
   - Actions: `fast, smart, fallback`
2. Build the graph: input → classify complexity → route to Fast LLM or Smart LLM → merge → output
3. Wire the Router based on complexity score (low → fast, high → smart, error → fallback)
4. Test validation — confirm all three action edges are required
5. Export and test each provider path

---

## Exercise D: Full IDE Workout

**Skills exercised:** Everything — create, edit, custom nodes, debug, export, package

Complete all of the following in one session:

- [ ] Create a new project from the **Simple LLM Flow** template
- [ ] Add 3 additional nodes from the palette
- [ ] Edit node titles and Actions in the inspector
- [ ] Create one custom node type via the wizard
- [ ] Implement all node code using double-click → Python editor
- [ ] Define a shared store schema with at least 4 keys
- [ ] Set a breakpoint and run in debug mode
- [ ] Inspect the Shared Store mid-run
- [ ] Export the project; verify `custom/` and `generated/` directories
- [ ] Run `python main.py` from the exported directory
- [ ] Switch from Dark to System theme via Tools > Options

---

*End of Tutorials — PocketFlow Creator v0.1.0*
