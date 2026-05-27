# Part 2 — PocketFlow Patterns in Creator

Every AI workflow, no matter how complex, is built from a small set of recurring patterns.
This section maps each pattern to a Creator project you can build and run. Understanding
these patterns — not just their code — is what lets you design systems confidently.

Work through these tutorials in any order after completing Part 1. Each tutorial begins
with a conceptual explanation of the pattern and why it exists, then walks through every
step with a reason for it.

[← Tutorials Index](index.md)

---

## Tutorial 7: Hello World — Single Node Q&A

**What you'll learn:** The simplest possible flow: one question, one answer, and why even
this trivial case benefits from the prep/exec/post structure.

### Why this pattern exists

Before building multi-node pipelines, it helps to see the full lifecycle in its simplest
form. A single-node Q&A flow has no branching, no looping, and no shared state complexity
— it's the clearest possible illustration of how PocketFlow moves data through a node.

The `prep` → `exec` → `post` split may seem like overhead when all three fit in ten lines.
It pays off the moment you want to retry `exec` without re-reading the database, or mock
`exec` in a test without touching real storage. The discipline starts here.

### The pattern

```
[Start] --default--> [AskLLM] --default--> [Stop]
```

A single active node reads from shared state, calls the LLM, and writes the answer back.
Start and Stop are structural markers, not code.

### Step-by-step

**Step 1: Create the project.**

Open Creator and choose File > New Project. Name it `tut_hello_world`. Creator creates
the folder structure (`graphs/`, `code/`, `prompts/`) and opens an empty canvas. Starting
with a fresh project — not a template — forces you to make every decision consciously.

**Step 2: Add Start and Stop nodes.**

Drag **Start Node** onto the canvas. Drag **Stop Node** onto the canvas. These nodes hold
no code; they are entry and exit markers that the validator uses to confirm your flow has
a clear beginning and end. PocketFlow requires exactly one node declared as the start; the
Start Node sets this automatically.

**Step 3: Add an LLM Prompt Node.**

Drag **LLM Prompt Node** onto the canvas. In the Inspector, set its Title to `Ask LLM`.
The LLM Prompt Node is a Basic Node with a predefined code template — it already contains
`prep`, `exec`, and `post` stubs wired for calling an LLM. You will fill in the logic.

Set the prompt properties in the Inspector:

- **`prompt_type`** — choose `string` to type the prompt directly, or `path` to load it
  from a Markdown file at run time
- **`prompt_file`** — the prompt text (if `string`) or relative file path (if `path`)

For this tutorial, leave `prompt_type` as `string` and enter your question directly in
`prompt_file` — no file needed.

**Step 4: Wire the edges.**

Draw an edge from **Start → Ask LLM**, typing `default` as the action. Draw another from
**Ask LLM → Stop**, also `default`. Every edge in PocketFlow is a named action — even when
there is only one path, the action must be explicit. This explicitness becomes critical in
routing flows where multiple outgoing edges exist.

**Step 5: Arrange and Zoom to Fit.**

Drag nodes into a left-to-right arrangement that matches the flow, then use View > Zoom
to Fit (Ctrl+0) to centre the canvas. For automatic layout, use **View > Auto Arrange…**
(Ctrl+Shift+L) — choose an algorithm (Layered BFS, Grid, or Force-directed), a connector
style, and spacing, then click OK. The arrangement is undoable with Ctrl+Z.

**Step 6: Write the node code.**

Double-click **Ask LLM** to open it in the code editor. You will see `# --- NODE_START`
and `# --- NODE_END` markers. Everything you write goes between those markers. Fill in:

```python
class AskLlm(Node):
    def prep(self, shared):
        # Read the question from shared state, or use a default.
        # prep's job is to gather inputs. Keep it free of side effects.
        return shared.get("question", "What is PocketFlow?")

    def exec(self, prep_res):
        # exec receives exactly what prep returned.
        # It does the work — here, the LLM call.
        # exec is retried on failure, so it must be idempotent.
        return call_llm(prep_res)

    def post(self, shared, prep_res, exec_res):
        # post writes results back to shared state and chooses the next action.
        # It runs exactly once, even if exec was retried.
        shared["answer"] = exec_res
        print("Answer:", exec_res)
        return "default"
```

Notice the role separation: `prep` reads, `exec` works, `post` writes. The LLM call lives
in `exec` because that is the unit the framework knows how to retry. If the API times out,
PocketFlow retries `exec` without re-running `prep` or re-writing `post`.

**Step 7: Run the flow.**

Run > Run Active Flow. The Run Log tab shows each node as it executes. The Shared Store
tab shows the `answer` key appear after Ask LLM completes. If you see an error, read the
full traceback in the Run Log — it includes the node name and method where the failure
occurred.

**Expected result:** The Shared Store shows `answer: "PocketFlow is a minimal LLM
orchestration framework..."` (or whatever your LLM returns).

---

## Tutorial 8: Chat with History

**What you'll learn:** How to maintain conversational context across multiple turns by
accumulating a history list in the shared store, and how to model a loop in a Creator graph.

### Why this pattern exists

A single-turn Q&A forgets everything between calls. A chatbot must remember what was said.
PocketFlow's shared store is the natural place to keep history — it persists across every
node execution for the life of the flow. The trick is designing the graph to loop: after
printing a reply, the flow returns to the input node and waits for the next message.

Modeling a loop in a directed graph requires at least one node with two outgoing actions:
one to continue the loop and one to exit it. The `GetInput` node plays this role.

### The pattern

```
[Start] → [GetInput] ──continue──→ [CallLLM] → [PrintReply] → [GetInput]
          [GetInput] ──exit──────→ [Stop]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_chat`. This flow will use five nodes — slightly more complex than Tutorial 7.

**Step 2: Add the nodes.**

Add in order: Start Node, two Basic Nodes (titles: `Get Input`, `Print Reply`), one
LLM Prompt Node (title: `Call LLM`), Stop Node. The order you add them does not matter;
wiring defines the execution order.

**Step 3: Configure actions on Get Input.**

Select **Get Input** in the Inspector. Set Actions to `continue, exit`. A node's declared
Actions list is what the validator checks against outgoing edges — if you wire an edge with
action `exit` but the node doesn't declare it, the validator flags an error. Declare every
action the node's `post` can return.

**Step 4: Wire the graph.**

- Start → Get Input: `default`
- Get Input → Call LLM: `continue`
- Get Input → Stop: `exit`
- Call LLM → Print Reply: `default`
- Print Reply → Get Input: `default`  ← this is the loop-back edge

The loop-back is what makes this a conversation rather than a one-shot flow. Without it,
the flow would end after one turn.

**Step 5: Write Get Input's code.**

```python
class GetInput(Node):
    def prep(self, shared):
        # Nothing to read from shared — this node reads from the user.
        return None

    def exec(self, prep_res):
        # input() blocks until the user types. In a UI, this would be replaced
        # with an async await on a message queue.
        return input("You: ").strip()

    def post(self, shared, prep_res, exec_res):
        if exec_res.lower() in ("quit", "exit", "bye"):
            return "exit"
        # setdefault initialises the key on first turn without overwriting it.
        shared.setdefault("history", [])
        shared["history"].append({"role": "user", "content": exec_res})
        return "continue"
```

`setdefault` is the right tool here: it initialises the list on the first turn without
clearing it on subsequent turns. Using `shared["history"] = []` would reset the history
every turn — a subtle bug that wouldn't show up until the second message.

**Step 6: Write Call LLM's code.**

```python
class CallLlm(Node):
    def prep(self, shared):
        # Pass the full history so the LLM has context for each reply.
        return shared.get("history", [])

    def exec(self, prep_res):
        return call_llm_with_history(prep_res)

    def post(self, shared, prep_res, exec_res):
        # Append the assistant's reply so future turns include it as context.
        shared["history"].append({"role": "assistant", "content": exec_res})
        shared["last_reply"] = exec_res
        return "default"
```

Both user and assistant messages go into `history`. That full list is what you pass to the
LLM on the next turn. Without the assistant messages, the LLM cannot refer to what it said.

**Step 7: Write Print Reply's code.**

```python
class PrintReply(Node):
    def prep(self, shared):
        return shared.get("last_reply", "")

    def exec(self, prep_res):
        print(f"\nAssistant: {prep_res}\n")
        return None

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 8: Debug the loop.**

Run > Debug Active Flow. Set a breakpoint on **Call LLM** (F9). Each time the flow pauses
there, check the Shared Store tab — watch `history` grow with each turn. This is the most
reliable way to verify your history accumulation logic is correct.

**Expected result:** A working multi-turn conversation where the LLM remembers prior
messages until you type "quit", "exit", or "bye".

---

## Tutorial 9: Structured Output — Resume Data Extraction

**What you'll learn:** How to instruct an LLM to return JSON, how to parse and validate
that JSON in `exec`, and when structured output is the right pattern to use.

### Why this pattern exists

LLMs naturally produce prose. When downstream code needs to read specific fields — a name,
a list of skills, a number — prose is the wrong format. Structured output means prompting
the LLM to return JSON, then parsing it in `exec` before handing the result to `post`.

The discipline here is important: parsing happens in `exec`, not `post`. That way, if the
LLM returns malformed JSON, `exec` raises an exception and the framework can retry the call
rather than writing bad data to the shared store.

### The pattern

```
[Start] → [LoadResume] → [ExtractFields] → [ValidateOutput] → [Stop]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_structured_output`.

**Step 2: Add and wire the nodes.**

Add Start, three Basic Nodes (titles: `Load Resume`, `Extract Fields`, `Validate Output`),
Stop. Wire sequentially with `default` actions.

**Step 3: Set Inspector metadata for Extract Fields.**

Select **Extract Fields**. In Inspector set Reads: `resume_text` and Writes: `extracted_data`.
This metadata does not affect execution but documents the data contract — future readers
of the graph can immediately see what this node consumes and produces. Think of it as the
function signature for the node.

**Step 4: Write Load Resume's code.**

```python
class LoadResume(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        # In production, read from a file or API. Here we use a static string.
        return """Jane Smith, jane@example.com
        10 years of experience in software engineering.
        Skills: Python, SQL, Machine Learning, Docker, Kubernetes"""

    def post(self, shared, prep_res, exec_res):
        shared["resume_text"] = exec_res
        return "default"
```

**Step 5: Write Extract Fields's code.**

```python
import json

class ExtractFields(Node):
    def prep(self, shared):
        return shared["resume_text"]

    def exec(self, prep_res):
        prompt = f"""Extract from this resume:
- name (string)
- email (string)
- years_of_experience (integer)
- skills (list of strings)

Resume:
{prep_res}

Return ONLY valid JSON. No explanation, no markdown fences. Example:
{{"name": "...", "email": "...", "years_of_experience": 5, "skills": ["Python"]}}"""

        raw = call_llm(prompt)
        # Strip markdown fences if the LLM adds them despite the instruction.
        if raw.strip().startswith("```"):
            raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        # json.loads raises ValueError on malformed JSON — exec retries on exception.
        return json.loads(raw)

    def post(self, shared, prep_res, exec_res):
        shared["extracted_data"] = exec_res
        return "default"
```

The fence-stripping code handles a common LLM behaviour: wrapping JSON in markdown code
blocks despite being told not to. Do this defensively in `exec` rather than hoping the LLM
follows instructions perfectly every time.

**Step 6: Write Validate Output's code.**

```python
class ValidateOutput(Node):
    REQUIRED = {"name", "email", "years_of_experience", "skills"}

    def prep(self, shared):
        return shared.get("extracted_data", {})

    def exec(self, prep_res):
        missing = self.REQUIRED - set(prep_res.keys())
        if missing:
            raise ValueError(f"Missing fields: {missing}")
        return prep_res

    def post(self, shared, prep_res, exec_res):
        print("Extracted:", exec_res)
        return "default"
```

Validation in a separate node (not inside Extract Fields) makes the pipeline easy to
extend: swap the extractor, keep the validator, and the contract is enforced regardless.

**Step 7: Use the Shared Store Designer.**

Tools > Shared Store Designer. Add rows: `resume_text` (string), `extracted_data` (object).
This documents the schema so team members reading the project understand what the store holds.

**Expected result:** The Shared Store shows `extracted_data` as a populated JSON object
with the four required fields.

---

## Tutorial 10: Multi-Stage Workflow — Article Writer

**What you'll learn:** How to chain multiple LLM calls through distinct stages — outline,
draft, polish — and why separating stages produces better output than a single giant prompt.

### Why this pattern exists

A single prompt asking for "a complete article" gives the LLM no room to reason step by
step. Breaking the task into stages lets the LLM focus on one goal at a time: first produce
structure, then expand it, then refine it. Each stage can have its own prompt, its own
retry budget, and its own output stored separately in the shared store for inspection.

This pattern also makes debugging practical. If the final article is poor, you can inspect
the outline and draft separately to identify where quality degraded.

### The pattern

```
[Start] → [GenerateOutline] → [WriteDraft] → [ApplyStyle] → [Stop]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_workflow`.

**Step 2: Add nodes and wire them.**

Add Start, three LLM Prompt Nodes (titles: `Generate Outline`, `Write Draft`, `Apply Style`),
Stop. Wire sequentially with `default` actions.

**Step 3: Create prompt files.**

In Project Explorer, right-click the `prompts/` folder and create three files:
`outline.md`, `draft.md`, `style.md`. Storing prompts as files (not inline strings) means
you can edit them without touching node code — and they show up in version control diffs
as readable text changes, not code changes.

`prompts/outline.md`:
```
Create a 5-point outline for an article about: {topic}
Return only the outline as a numbered list. No introduction, no conclusion header yet.
```

`prompts/draft.md`:
```
Expand this outline into a complete draft article:

{outline}

Write in a clear, engaging style. Include an introduction and conclusion.
```

`prompts/style.md`:
```
Polish this article for publication. Make it concise, vivid, and professional.
Remove redundancy. Keep all factual content.

{draft}
```

**Step 4: Write Generate Outline's code.**

```python
class GenerateOutline(Node):
    def prep(self, shared):
        topic = shared.get("topic", "the future of AI")
        template = open("prompts/outline.md").read()
        return template.format(topic=topic)

    def exec(self, prep_res):
        return call_llm(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["outline"] = exec_res
        return "default"
```

**Step 5: Write Write Draft's code.**

```python
class WriteDraft(Node):
    def prep(self, shared):
        template = open("prompts/draft.md").read()
        return template.format(outline=shared["outline"])

    def exec(self, prep_res):
        return call_llm(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["draft"] = exec_res
        return "default"
```

**Step 6: Write Apply Style's code.**

```python
class ApplyStyle(Node):
    def prep(self, shared):
        template = open("prompts/style.md").read()
        return template.format(draft=shared["draft"])

    def exec(self, prep_res):
        return call_llm(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["final_article"] = exec_res
        print(exec_res)
        return "default"
```

**Step 7: Set the topic and run.**

In the Shared Store Designer, set `topic` with a default value (e.g., `"the future of AI"`).
Run > Run Active Flow. After completion, inspect `outline`, `draft`, and `final_article`
separately in the Shared Store tab to see how each stage built on the previous.

**Expected result:** Three intermediate keys in the shared store plus a polished final
article that is noticeably better than what a single-prompt approach produces.

---

## Tutorial 11: Conditional Routing — Chat Guardrail

**What you'll learn:** How to use a Router Node to branch the flow based on an LLM
classification, and when guardrails belong in the graph structure versus in application code.

### Why this pattern exists

Guardrails — topic filters, safety checks, input validators — are naturally expressed as
branches in the flow graph, not as `if` statements buried inside a node. Putting the branch
in the graph makes it visible, testable, and replaceable without touching unrelated code.

A Router Node is a node whose `post` method returns one of several named actions. Each
action corresponds to an outgoing edge leading to a different path. The graph structure
itself documents the branching logic.

### The pattern

```
[Start] → [ClassifyInput] ──on_topic──→ [AnswerQuestion] → [Stop]
                          └─off_topic──→ [Redirect]       → [Stop]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_guardrail`.

**Step 2: Add the Router Node.**

Drag **Router Node** onto the canvas. Set its Title to `Classify Input`. In Inspector,
set Actions to `on_topic, off_topic`. The Router Node is a visual hint that this node
controls branching — functionally it is a Basic Node, but its icon communicates intent.

**Step 3: Add answer and redirect nodes.**

Add two Basic Nodes: `Answer Question` and `Redirect`. Add two Stop Nodes (one per path).
Wire: Start → Classify Input (`default`), Classify Input → Answer Question (`on_topic`),
Classify Input → Redirect (`off_topic`), Answer Question → Stop (`default`),
Redirect → Stop (`default`).

**Step 4: Write Classify Input's code.**

```python
class ClassifyInput(Node):
    def prep(self, shared):
        return shared.get("user_question", "")

    def exec(self, prep_res):
        if not prep_res.strip():
            return "off_topic"
        prompt = (
            "You are a guardrail for a travel assistance chatbot.\n"
            "Is the following question about travel, destinations, flights, hotels, or itineraries?\n"
            "Answer YES or NO only.\n\n"
            f"Question: {prep_res}"
        )
        answer = call_llm(prompt).strip().upper()
        return "on_topic" if answer.startswith("YES") else "off_topic"

    def post(self, shared, prep_res, exec_res):
        shared["route"] = exec_res
        return exec_res  # return the action string directly
```

`exec` returns the action string, and `post` returns it unchanged. This is a valid
PocketFlow pattern: when `exec` directly computes the routing decision, `post` simply
propagates it. The `shared["route"] = exec_res` line stores the decision for debugging.

**Step 5: Write Answer Question and Redirect.**

```python
class AnswerQuestion(Node):
    def prep(self, shared):
        return shared.get("user_question", "")

    def exec(self, prep_res):
        return call_llm(f"Answer this travel question helpfully: {prep_res}")

    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res
        print("Answer:", exec_res)
        return "default"

class Redirect(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        print("I can only help with travel questions. Please ask about destinations, flights, or hotels.")
        return "default"
```

**Step 6: Test both paths.**

Set `user_question` in the Shared Store Designer. Run once with a travel question (`"Best
beaches in Thailand"`) and once with an off-topic question (`"Explain quantum physics"`).
Verify the Shared Store shows `route: on_topic` and `route: off_topic` respectively. Check
the Run Log to confirm the correct path executed.

**Expected result:** Travel questions produce an answer; off-topic questions produce a
redirect message. The graph visually documents this branching logic.

---

## Tutorial 12: Agent with Tools

**What you'll learn:** How an agent decides which tool to call, executes it, and loops back
to decide again — and why this decision loop is the right model for open-ended tasks.

### Why this pattern exists

A workflow runs a fixed sequence of steps. An agent runs a variable sequence determined
at runtime by the LLM's reasoning. The agent pattern — decide, act, observe, decide again
— is how you build systems that can handle tasks where the number of steps is unknown in
advance.

The key design choice: the Router Node decides, separate tool nodes act. Keeping decision
and action apart makes each testable in isolation and makes it easy to add new tools
without touching the decision logic.

### The pattern

```
[Start] → [Decide] ──search────→ [WebSearch]  → [Decide]
                  ├─calculate──→ [Calculator] → [Decide]
                  └─answer────→ [FinalAnswer] → [Stop]
```

The loop-back edges (WebSearch → Decide, Calculator → Decide) are what make this an agent
rather than a workflow. The agent decides, acts, then decides again with new information.

### Step-by-step

**Step 1: Create the project.**

New project: `tut_agent`.

**Step 2: Add the Router Node.**

Add Router Node, title `Decide`. Set Actions: `search, calculate, answer`. This node is
the heart of the agent — every iteration of the loop passes through it.

**Step 3: Add tool nodes and final answer node.**

Add Basic Nodes: `Web Search`, `Calculator`, `Final Answer`. Add Stop Node.

**Step 4: Wire the graph.**

- Start → Decide: `default`
- Decide → Web Search: `search`
- Decide → Calculator: `calculate`
- Decide → Final Answer: `answer`
- Web Search → Decide: `default`  ← loop-back
- Calculator → Decide: `default`  ← loop-back
- Final Answer → Stop: `default`

**Step 5: Write Decide's code.**

```python
class Decide(Node):
    TOOLS = ["search", "calculate", "answer"]

    def prep(self, shared):
        return shared.get("question", ""), shared.get("tool_history", [])

    def exec(self, prep_res):
        question, history = prep_res
        history_text = "\n".join(f"- {h}" for h in history[-6:])
        prompt = (
            f"Question: {question}\n"
            f"Steps taken so far:\n{history_text or 'none'}\n\n"
            "What should I do next? Choose EXACTLY one: search, calculate, or answer.\n"
            "Respond with just the single word."
        )
        action = call_llm(prompt).strip().lower()
        return action if action in self.TOOLS else "answer"

    def post(self, shared, prep_res, exec_res):
        shared.setdefault("tool_history", []).append(f"decided: {exec_res}")
        return exec_res
```

The `[-6:]` slice limits history to the last six steps. Without this, the prompt grows
indefinitely and eventually exceeds the LLM's context window.

**Step 6: Write the tool nodes.**

```python
class WebSearch(Node):
    def prep(self, shared):
        return shared.get("question", "")

    def exec(self, prep_res):
        # In production, call a real search API here.
        result = f"[Search result for: {prep_res}] The answer is approximately 42."
        return result

    def post(self, shared, prep_res, exec_res):
        shared.setdefault("tool_history", []).append(f"search result: {exec_res[:100]}")
        shared["last_search"] = exec_res
        return "default"

class Calculator(Node):
    def prep(self, shared):
        return shared.get("question", "")

    def exec(self, prep_res):
        # In production, parse and evaluate a mathematical expression.
        return f"[Calculator result for: {prep_res}] = 1764"

    def post(self, shared, prep_res, exec_res):
        shared.setdefault("tool_history", []).append(f"calculated: {exec_res}")
        shared["last_calculation"] = exec_res
        return "default"

class FinalAnswer(Node):
    def prep(self, shared):
        history = shared.get("tool_history", [])
        question = shared.get("question", "")
        return question, history

    def exec(self, prep_res):
        question, history = prep_res
        context = "\n".join(history)
        return call_llm(
            f"Question: {question}\nResearch done:\n{context}\n\nProvide a final answer:"
        )

    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res
        print("Final answer:", exec_res)
        return "default"
```

**Step 7: Set a question and run in debug mode.**

In the Shared Store Designer set `question` to `"What is 42 squared?"`. Run in Debug Mode
(Shift+F5) with a breakpoint on `Decide`. Watch each iteration: the agent decides to
calculate, acts, then decides to answer. The tool history grows with each step.

**Expected result:** The agent loop terminates when `Decide` returns `answer`. The Shared
Store shows the full `tool_history` and a final answer.

---

## Tutorial 13: Retrieval-Augmented Generation (RAG)

**What you'll learn:** The complete RAG pipeline — chunking, embedding, indexing, retrieval,
and generation — and when RAG is the right approach versus fine-tuning or longer prompts.

### Why this pattern exists

LLMs have a knowledge cutoff and a limited context window. When a question requires
information the LLM wasn't trained on (your company's documents, recent events, private
data), you can't simply ask the LLM — you must retrieve the relevant passages first and
include them in the prompt.

RAG splits this into four stages:
1. **Index time:** Chunk documents, embed each chunk, store vectors.
2. **Query time:** Embed the question, find the closest chunks, generate an answer.

PocketFlow represents these as separate nodes, which means you can optimise each
independently — swap the embedding model, change the chunk size, use a different retrieval
strategy — without redesigning the whole pipeline.

### The pattern

```
[Start] → [LoadDocs] → [EmbedChunks] → [StoreIndex] → [GetQuestion]
        → [EmbedQuery] → [RetrieveChunks] → [GenerateAnswer] → [Stop]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_rag`.

**Step 2: Add and wire nodes in two phases.**

Phase 1 (indexing): Start → Load Docs → Embed Chunks → Store Index → Get Question.
Phase 2 (query): Get Question → Embed Query → Retrieve Chunks → Generate Answer → Stop.

In a real system these phases might run independently. For this tutorial they run in
sequence so you can inspect intermediate state in one flow.

**Step 3: Document the data contracts.**

Select each node and set Reads/Writes in Inspector. This makes the shared store schema
explicit before writing any code:

- Load Docs: Writes `raw_docs`
- Embed Chunks: Reads `raw_docs`, Writes `chunks`, `embeddings`
- Get Question: Writes `question`
- Embed Query: Reads `question`, Writes `query_vector`
- Retrieve Chunks: Reads `query_vector`, `embeddings`, `chunks`, Writes `context`
- Generate Answer: Reads `context`, `question`, Writes `answer`

**Step 4: Write the index-phase nodes.**

```python
class LoadDocs(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        # In production, read from files, a database, or an API.
        return (
            "PocketFlow is a minimal 100-line LLM orchestration framework. "
            "It uses a shared store to pass data between nodes. "
            "Nodes implement prep, exec, and post methods. "
            "The framework supports sync, async, batch, and parallel processing. "
            "PocketFlow is designed for clarity and composability."
        )

    def post(self, shared, prep_res, exec_res):
        shared["raw_docs"] = exec_res
        return "default"

class EmbedChunks(Node):
    CHUNK_SIZE = 100  # characters per chunk

    def prep(self, shared):
        text = shared["raw_docs"]
        return [text[i:i+self.CHUNK_SIZE] for i in range(0, len(text), self.CHUNK_SIZE)]

    def exec(self, prep_res):
        # In production, call a real embedding model (e.g. OpenAI text-embedding-3-small).
        # Here we use a deterministic mock: hash-based floats.
        import hashlib
        def mock_embed(text):
            h = hashlib.md5(text.encode()).digest()
            return [b / 255.0 for b in h]
        return [(chunk, mock_embed(chunk)) for chunk in prep_res]

    def post(self, shared, prep_res, exec_res):
        shared["chunks"] = [c for c, _ in exec_res]
        shared["embeddings"] = [e for _, e in exec_res]
        return "default"
```

**Step 5: Write the query-phase nodes.**

```python
class GetQuestion(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return input("Question: ").strip()

    def post(self, shared, prep_res, exec_res):
        shared["question"] = exec_res
        return "default"

class EmbedQuery(Node):
    def prep(self, shared):
        return shared["question"]

    def exec(self, prep_res):
        import hashlib
        h = hashlib.md5(prep_res.encode()).digest()
        return [b / 255.0 for b in h]

    def post(self, shared, prep_res, exec_res):
        shared["query_vector"] = exec_res
        return "default"

class RetrieveChunks(Node):
    TOP_K = 3

    def prep(self, shared):
        return shared["query_vector"], shared.get("embeddings", []), shared.get("chunks", [])

    def exec(self, prep_res):
        q_vec, emb_list, chunks = prep_res
        def dot(a, b):
            return sum(x * y for x, y in zip(a, b))
        scored = [(dot(q_vec, e), c) for e, c in zip(emb_list, chunks)]
        top = sorted(scored, reverse=True)[:self.TOP_K]
        return [chunk for _, chunk in top]

    def post(self, shared, prep_res, exec_res):
        shared["context"] = exec_res
        return "default"

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

**Step 6: Run and inspect.**

Run > Run Active Flow. Type a question about PocketFlow when prompted. Inspect the Shared
Store: `chunks`, `embeddings`, `query_vector`, `context` (the retrieved passages), and
`answer` are all visible. This transparency — seeing every intermediate value — is one of
the key advantages of the node-per-stage approach.

**Expected result:** The LLM answers based on the retrieved context, not its training data.

---

## Tutorial 14: Map-Reduce / Batch Processing

**What you'll learn:** How BatchNode automatically iterates over a list without a manual
loop, and when to use batch processing versus building an explicit loop in the graph.

### Why this pattern exists

When you need to apply the same operation to every item in a list — summarise each
document, classify each image, rate each resume — you could build an explicit loop in the
graph. But that adds four extra nodes and wiring for something the framework can handle
automatically.

`BatchNode` is the answer: its `prep` returns a list, and the framework calls `exec` once
per item. Your `exec` code is written for a single item, not a list. `post` receives all
results as a list and writes them to the shared store in one place.

### The pattern

```
[Start] → [LoadItems] → [ProcessEach (BatchNode)] → [Aggregate] → [Stop]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_map_reduce`.

**Step 2: Add a Batch Node.**

Drag **Batch Node** from the palette. Title it `Process Each`. In Inspector, note that
Base Class shows `BatchNode`. The palette distinguishes BatchNode visually to signal that
this node has special iteration semantics.

**Step 3: Write Load Items's code.**

```python
class LoadItems(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return [
            "Alice Johnson — 5 years Python, 3 years ML. Led team of 4.",
            "Bob Smith — 2 years JavaScript, 1 year React. Junior developer.",
            "Carol White — 12 years Java, 8 years architecture. Principal engineer.",
        ]

    def post(self, shared, prep_res, exec_res):
        shared["items"] = exec_res
        return "default"
```

**Step 4: Write Process Each's code.**

```python
class ProcessEach(BatchNode):
    def prep(self, shared):
        # Return the list. BatchNode calls exec once per element.
        return shared["items"]

    def exec(self, item):
        # item is a single resume string, not the full list.
        # Write exec as if you're handling one item — the framework handles iteration.
        return call_llm(f"Rate this resume 1-10 and explain why:\n{item}")

    def post(self, shared, prep_res, exec_res):
        # exec_res is a list: one result per item, in the same order as prep returned.
        shared["ratings"] = exec_res
        return "default"
```

The mental model: `prep` hands the framework a shopping list. The framework checks off
each item by calling `exec`. `post` receives the completed list.

**Step 5: Write Aggregate's code.**

```python
class Aggregate(Node):
    def prep(self, shared):
        items = shared.get("items", [])
        ratings = shared.get("ratings", [])
        return list(zip(items[:30], ratings))  # first 30 chars of each resume

    def exec(self, prep_res):
        lines = [f"Candidate {i+1}: {rating}" for i, (_, rating) in enumerate(prep_res)]
        return "\n".join(lines)

    def post(self, shared, prep_res, exec_res):
        shared["summary"] = exec_res
        print(exec_res)
        return "default"
```

**Step 6: Run and inspect.**

Run > Run Active Flow. The Shared Store shows `ratings` as a three-element list — one
rating per resume. The batch ran three LLM calls automatically without any loop logic in
the graph or the code.

**When to use BatchNode vs. explicit loops:**
- Use BatchNode when every item gets the same treatment.
- Use an explicit loop in the graph (a node that increments an index and loops back)
  when different items need different paths through the graph.

**Expected result:** `ratings` contains three independent LLM evaluations; `summary` formats them.

---

## Tutorial 15: Human-in-the-Loop

**What you'll learn:** How to pause a flow for human review, accept approval or rejection,
and loop back for revision — and why this is structurally different from a simple prompt.

### Why this pattern exists

Fully automated LLM pipelines are efficient but fallible. When the cost of a mistake is
high (publishing content, sending an email, making a purchase), a human review gate is
worth the latency. Human-in-the-loop is not a workaround for a bad LLM — it is a
deliberate architectural choice that keeps a human in the critical path.

In PocketFlow, the review node is a regular node that reads from standard input. In
production this becomes an async node waiting on a message queue or a web form submission.
The graph structure is identical either way — only the implementation of `exec` changes.

### The pattern

```
[Start] → [DraftContent] → [Review] ──approved──→ [Publish] → [Stop]
                                    └─rejected────→ [Revise]  → [Review]
```

The loop from Revise back to Review is what makes this iterative rather than binary.

### Step-by-step

**Step 1: Create the project.**

New project: `tut_hitl`.

**Step 2: Add nodes.**

Add: Start, Basic Node (`Draft Content`), Router Node (`Review`, Actions: `approved, rejected`),
Basic Node (`Publish`), Basic Node (`Revise`), Stop.

**Step 3: Wire the approval loop.**

- Start → Draft Content: `default`
- Draft Content → Review: `default`
- Review → Publish: `approved`
- Review → Revise: `rejected`
- Revise → Review: `default`  ← the loop-back
- Publish → Stop: `default`

**Step 4: Write Draft Content's code.**

```python
class DraftContent(Node):
    def prep(self, shared):
        topic = shared.get("topic", "benefits of morning exercise")
        feedback = shared.get("feedback", "")
        if feedback:
            return f"Topic: {topic}\nPrevious feedback to incorporate: {feedback}"
        return f"Topic: {topic}"

    def exec(self, prep_res):
        return call_llm(f"Write a short 3-paragraph blog post about: {prep_res}")

    def post(self, shared, prep_res, exec_res):
        shared["draft"] = exec_res
        return "default"
```

When `feedback` exists (from a prior rejection), it is incorporated into the new prompt.
This is how the revision loop improves on each iteration.

**Step 5: Write Review's code.**

```python
class ReviewDraft(Node):
    def prep(self, shared):
        return shared.get("draft", "")

    def exec(self, prep_res):
        print("\n" + "="*60)
        print("DRAFT FOR REVIEW:")
        print("="*60)
        print(prep_res)
        print("="*60)
        decision = input("\nApprove? (yes/no): ").strip().lower()
        if decision in ("yes", "y"):
            return "approved"
        feedback = input("What should be improved? ").strip()
        return ("rejected", feedback)

    def post(self, shared, prep_res, exec_res):
        if isinstance(exec_res, tuple):
            action, feedback = exec_res
            shared["feedback"] = feedback
            return action
        return exec_res
```

**Step 6: Write Publish and Revise.**

```python
class Publish(Node):
    def prep(self, shared):
        return shared.get("draft", "")

    def exec(self, prep_res):
        with open("output/published_post.md", "w") as f:
            f.write(prep_res)
        return "Published."

    def post(self, shared, prep_res, exec_res):
        print(exec_res)
        return "default"

class Revise(Node):
    def prep(self, shared):
        return shared.get("draft", ""), shared.get("feedback", "")

    def exec(self, prep_res):
        draft, feedback = prep_res
        return call_llm(f"Revise this draft based on the feedback.\nFeedback: {feedback}\n\nDraft:\n{draft}")

    def post(self, shared, prep_res, exec_res):
        shared["draft"] = exec_res
        return "default"
```

**Step 7: Run in debug mode.**

Run > Debug Active Flow. Set a breakpoint on **Review** so you can inspect the Shared Store
before each review decision. After rejecting, watch `feedback` appear in the store. After
approving, confirm the file was written.

**Expected result:** The flow loops until you approve, then writes the approved draft to a file.

---

## Tutorial 16: LLM-as-Judge / Evaluator Loop

**What you'll learn:** How to use a second LLM call to evaluate the output of a first, loop
for refinement, and use a maximum-iteration guard to ensure the flow always terminates.

### Why this pattern exists

An LLM's first attempt at a creative or analytical task is often good but not great. Rather
than accepting first-pass output or manually reviewing it, you can automate the evaluation:
one LLM generates, a second (the "judge") evaluates and provides feedback, and the first
refines based on that feedback. This is the evaluator loop.

The judge does not have to be a different model — it is a different call with a different
prompt, focused on evaluation rather than generation. The separation of roles (generate vs.
evaluate) improves quality because each call is optimised for its specific task.

The loop must always terminate. The maximum-iteration guard is not optional: without it, a
stubborn judge and a poor generator could loop forever.

### The pattern

```
[Start] → [Generate] → [Evaluate] ──pass──→ [Stop]
              ^                   └─fail──→ [Refine] → [Generate]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_judge`.

**Step 2: Add and wire nodes.**

Add Start, Basic Node (`Generate`), Router Node (`Evaluate`, Actions: `pass, fail`),
Basic Node (`Refine`), Stop.

Wire: Start → Generate → Evaluate, Evaluate → Stop (`pass`), Evaluate → Refine (`fail`),
Refine → Generate (`default`).

**Step 3: Write Generate's code.**

```python
class Generate(Node):
    def prep(self, shared):
        task = shared.get("task", "Write a haiku about software engineering.")
        feedback = shared.get("judge_feedback", "")
        if feedback:
            current = shared.get("output", "")
            return f"Task: {task}\n\nCurrent attempt:\n{current}\n\nFeedback: {feedback}\n\nRevise:"
        return task

    def exec(self, prep_res):
        return call_llm(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["output"] = exec_res
        shared["judge_feedback"] = ""  # Clear feedback after incorporating it.
        return "default"
```

**Step 4: Write Evaluate's code.**

```python
class Evaluate(Node):
    MAX_ITERATIONS = 3

    def prep(self, shared):
        return shared.get("output", ""), shared.get("judge_iteration", 0)

    def exec(self, prep_res):
        output, iteration = prep_res
        # The guard: force pass after MAX_ITERATIONS to ensure termination.
        if iteration >= self.MAX_ITERATIONS:
            return "pass"
        criteria = shared.get("criteria", "The output should be creative, precise, and complete.")
        prompt = (
            f"Evaluate this output.\n"
            f"Criteria: {criteria}\n"
            f"Output:\n{output}\n\n"
            "Respond with PASS if the output meets the criteria, or FAIL followed by "
            "one sentence of specific feedback on what to improve."
        )
        verdict = call_llm(prompt).strip()
        if verdict.upper().startswith("PASS"):
            return "pass"
        return ("fail", verdict)

    def post(self, shared, prep_res, exec_res):
        output, iteration = prep_res
        shared["judge_iteration"] = iteration + 1
        if isinstance(exec_res, tuple):
            action, feedback = exec_res
            shared["judge_feedback"] = feedback
            return action
        return exec_res
```

**Step 5: Write Refine's code.**

Refine is handled by Generate reading `judge_feedback` on its next call (see Step 3 above).
Refine can be a simple passthrough that just signals the loop should continue:

```python
class Refine(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        return "default"  # Routes back to Generate.
```

**Step 6: Set criteria and run.**

In the Shared Store Designer, set:
- `task`: `"Write a haiku about software engineering."`
- `criteria`: `"Must be exactly 3 lines, 5-7-5 syllable structure, and relate to coding."`

Run > Debug Active Flow. Set a breakpoint on **Evaluate**. Watch `judge_iteration` increment
with each loop. After `MAX_ITERATIONS`, the judge forces `pass` regardless of quality.

**Expected result:** The flow runs 1–4 times (depending on quality) and produces a final
output. `judge_iteration` in the Shared Store shows how many rounds it took.

---

## Tutorial 17: Multi-Agent System

**What you'll learn:** How to model two independent agents with different roles in one flow,
coordinate them through a shared store, and use a third agent as arbitrator.

### Why this pattern exists

Some tasks benefit from adversarial or complementary perspectives: one agent argues for a
position, another argues against, a third decides. This is the debate pattern, and it
generalises to any multi-agent coordination problem — reviewer and author, planner and
critic, proposer and validator.

In PocketFlow, multiple "agents" are just nodes with different system prompts. They share
the same store, so each can read what the others produced. The coordinator (judge) node
reads the full debate history and decides when to conclude.

### The pattern

```
[Start] → [AgentA] → [AgentB] → [Judge] ──continue──→ [AgentA]
                                          └─conclude──→ [Summary] → [Stop]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_debate`.

**Step 2: Add and wire nodes.**

Add Start, Basic Node (`Agent A`), Basic Node (`Agent B`), Router Node (`Judge`, Actions:
`continue, conclude`), Basic Node (`Summary`), Stop.

Wire: Start → Agent A → Agent B → Judge, Judge → Agent A (`continue`),
Judge → Summary (`conclude`), Summary → Stop.

**Step 3: Write Agent A's code (pro argument).**

```python
class AgentAPropose(Node):
    ROLE = "You argue IN FAVOR of the topic. Be persuasive and specific."

    def prep(self, shared):
        topic = shared.get("topic", "AI regulation is necessary")
        history = shared.get("debate_history", [])
        return topic, history

    def exec(self, prep_res):
        topic, history = prep_res
        context = "\n".join(history[-4:])  # Last 4 exchanges only.
        prompt = (
            f"Topic: {topic}\n"
            f"Role: {self.ROLE}\n"
            f"Debate so far:\n{context or 'None'}\n\n"
            "Make your argument in 2-3 sentences:"
        )
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared.setdefault("debate_history", []).append(f"PRO: {exec_res}")
        return "default"
```

**Step 4: Write Agent B's code (counter argument).**

```python
class AgentBCounter(Node):
    ROLE = "You argue AGAINST the topic. Be critical and precise."

    def prep(self, shared):
        topic = shared.get("topic", "AI regulation is necessary")
        history = shared.get("debate_history", [])
        return topic, history

    def exec(self, prep_res):
        topic, history = prep_res
        context = "\n".join(history[-4:])
        prompt = (
            f"Topic: {topic}\n"
            f"Role: {self.ROLE}\n"
            f"Debate so far:\n{context or 'None'}\n\n"
            "Make your counter-argument in 2-3 sentences:"
        )
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["debate_history"].append(f"CON: {exec_res}")
        return "default"
```

**Step 5: Write Judge's code.**

```python
class Judge(Node):
    MAX_ROUNDS = 4

    def prep(self, shared):
        history = shared.get("debate_history", [])
        round_num = shared.get("round", 0)
        return history, round_num

    def exec(self, prep_res):
        history, round_num = prep_res
        if round_num >= self.MAX_ROUNDS:
            return "conclude"
        recent = "\n".join(history[-4:])
        prompt = (
            f"You are an impartial debate judge.\n"
            f"Recent arguments:\n{recent}\n\n"
            "Is the debate sufficiently developed to conclude? "
            "Answer CONCLUDE if yes, CONTINUE if another round would add value."
        )
        verdict = call_llm(prompt).strip().upper()
        return "conclude" if "CONCLUDE" in verdict else "continue"

    def post(self, shared, prep_res, exec_res):
        shared["round"] = shared.get("round", 0) + 1
        return exec_res
```

**Step 6: Write Summary's code.**

```python
class Summary(Node):
    def prep(self, shared):
        return shared.get("debate_history", []), shared.get("topic", "")

    def exec(self, prep_res):
        history, topic = prep_res
        full_debate = "\n".join(history)
        return call_llm(
            f"Summarise this debate on '{topic}'. Identify the strongest arguments "
            f"on both sides and state which side made the more compelling case.\n\n"
            f"Debate:\n{full_debate}"
        )

    def post(self, shared, prep_res, exec_res):
        shared["conclusion"] = exec_res
        print("\n=== DEBATE CONCLUSION ===\n", exec_res)
        return "default"
```

**Step 7: Run and watch the debate.**

Set `topic` in the Shared Store Designer. Run > Run Active Flow. Watch `debate_history`
grow in the Shared Store tab as each agent argues. The Run Log shows which agent ran each
iteration.

**Expected result:** A multi-round debate terminates with a judge summary stored in
`conclusion`. `round` in the Shared Store shows how many rounds the debate ran.

---

## Tutorial 23: Streaming Output

**What you'll learn:** How to design a flow that makes incremental output visible as it is
produced, and why streaming matters for user-facing applications.

### Why this pattern exists

Standard `call_llm` returns the complete response when the model finishes generating.
For a short response this is fine. For a long response — a detailed analysis, a full
article — the user waits with no feedback and then sees everything at once. Streaming
sends tokens as they are generated, making the system feel responsive.

In Creator, you model streaming by separating the generation step from the display step.
The generator node produces output incrementally (or simulates it); the display node
reads from the shared store and renders it.

### The pattern

```
[Start] → [StreamLLM] → [PrintChunks] → [Stop]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_streaming`.

**Step 2: Add and wire nodes.**

Add Start, Basic Node (`Stream LLM`, Writes: `chunks`), Basic Node (`Print Chunks`), Stop.
Wire sequentially with `default` actions.

**Step 3: Write Stream LLM's code.**

```python
class StreamLlm(Node):
    def prep(self, shared):
        return shared.get("prompt", "Tell me a story in 5 sentences about a robot learning to paint.")

    def exec(self, prep_res):
        # With a real streaming API, you would yield tokens here.
        # With call_llm, we receive the full text and split it into word chunks
        # to simulate streaming behavior for demonstration purposes.
        full_text = call_llm(prep_res)
        return full_text.split()  # word-level chunks

    def post(self, shared, prep_res, exec_res):
        shared["chunks"] = exec_res
        return "default"
```

In production, replace `call_llm` with a streaming API call that yields tokens. The
node structure — prep, exec, post — stays identical. Only `exec` changes.

**Step 4: Write Print Chunks's code.**

```python
import time

class PrintChunks(Node):
    def prep(self, shared):
        return shared.get("chunks", [])

    def exec(self, prep_res):
        print()
        for chunk in prep_res:
            print(chunk, end=" ", flush=True)
            time.sleep(0.05)  # simulate network latency between tokens
        print()
        return len(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["word_count"] = exec_res
        return "default"
```

**Step 5: Run and observe.**

Run > Run Active Flow. Watch words appear one at a time in the Run Log's output section.
After the flow completes, the Shared Store shows `chunks` (the full list) and `word_count`.

**Expected result:** Words appear progressively, simulating the experience of a real
streaming LLM response.

---

## Tutorial 24: Memory — Short-Term and Long-Term Context

**What you'll learn:** How to maintain two memory layers — recent conversation history and
a condensed long-term summary — and when to condense to avoid context window overflow.

### Why this pattern exists

A chat history grows indefinitely. Eventually it exceeds the LLM's context window, causing
errors or forcing the oldest messages to be truncated. The two-layer memory pattern solves
this by periodically condensing old history into a summary, then resetting the short-term
buffer. The LLM always has: (a) the full recent history, and (b) a compressed summary of
everything older.

This is roughly how long-running AI assistants manage memory. The threshold for condensing
(e.g., every 10 messages) and the quality of the summary determine how well the system
remembers older context.

### The pattern

```
[Start] → [GetInput] → [UpdateShortTerm] → [ShouldCondense?]
    ──yes──→ [CondenseToLongTerm] → [CallLLM] → [GetInput]
    ──no───→                        [CallLLM] → [GetInput]
[GetInput] ──exit──→ [Stop]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_memory`.

**Step 2: Add and wire nodes.**

Add: Start, Basic Node (`Get Input`, Actions: `continue, exit`), Basic Node (`Update Short Term`),
Router Node (`Should Condense?`, Actions: `yes, no`), Basic Node (`Condense To Long Term`),
LLM Prompt Node (`Call LLM`), Stop.

Wire: Start → Get Input, Get Input → Update Short Term (`continue`), Get Input → Stop (`exit`),
Update Short Term → Should Condense?, Should Condense? → Condense To Long Term (`yes`),
Should Condense? → Call LLM (`no`), Condense To Long Term → Call LLM (`default`),
Call LLM → Get Input (`default`).

**Step 3: Define the shared store schema.**

Tools > Shared Store Designer. Add:

| Key | Type | Default |
|---|---|---|
| short_term_history | array | |
| long_term_summary | string | |
| condensation_threshold | integer | 10 |

**Step 4: Write Get Input and Update Short Term.**

```python
class GetInput(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return input("You: ").strip()

    def post(self, shared, prep_res, exec_res):
        if exec_res.lower() in ("quit", "exit", "bye"):
            return "exit"
        shared.setdefault("short_term_history", []).append(
            {"role": "user", "content": exec_res}
        )
        return "continue"

class UpdateShortTerm(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 5: Write Should Condense? and Condense To Long Term.**

```python
class ShouldCondense(Node):
    def prep(self, shared):
        history = shared.get("short_term_history", [])
        threshold = shared.get("condensation_threshold", 10)
        return len(history), threshold

    def exec(self, prep_res):
        count, threshold = prep_res
        return "yes" if count >= threshold else "no"

    def post(self, shared, prep_res, exec_res):
        return exec_res

class CondenseToLongTerm(Node):
    def prep(self, shared):
        return (
            shared.get("short_term_history", []),
            shared.get("long_term_summary", "")
        )

    def exec(self, prep_res):
        history, old_summary = prep_res
        msgs = "\n".join(f"{m['role']}: {m['content']}" for m in history)
        prompt = (
            f"Existing summary of older conversation:\n{old_summary or 'None'}\n\n"
            f"New messages to incorporate:\n{msgs}\n\n"
            "Write an updated concise summary that captures all important facts, "
            "decisions, and context from both the old summary and the new messages:"
        )
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["long_term_summary"] = exec_res
        shared["short_term_history"] = []  # Reset the short-term buffer.
        return "default"
```

**Step 6: Write Call LLM.**

```python
class CallLlm(Node):
    def prep(self, shared):
        summary = shared.get("long_term_summary", "")
        history = shared.get("short_term_history", [])
        messages = []
        if summary:
            messages.append({
                "role": "system",
                "content": f"Context from earlier in the conversation: {summary}"
            })
        messages.extend(history)
        return messages

    def exec(self, prep_res):
        return call_llm_with_history(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared.setdefault("short_term_history", []).append(
            {"role": "assistant", "content": exec_res}
        )
        print(f"\nAssistant: {exec_res}\n")
        return "default"
```

**Step 7: Test condensation.**

Run > Debug Active Flow. Set the `condensation_threshold` to `2` in the Shared Store
Designer so condensation triggers after two exchanges. After two messages, watch
`long_term_summary` populate and `short_term_history` reset to an empty list.

**Expected result:** After every `condensation_threshold` messages, the short-term history
is compressed into `long_term_summary` and cleared. The conversation continues with the
summary providing context for older exchanges.

---

## Tutorial 26: Async Processing with AsyncNode

**What you'll learn:** How to write non-blocking I/O operations using `AsyncNode`, why async
matters for I/O-bound tasks, and how `prep_async`/`exec_async`/`post_async` correspond to
the synchronous lifecycle.

### Why this pattern exists

A standard `Node.exec` blocks the thread while it waits for a network response, a database
query, or a file system read. If you are running one node at a time, this is fine. If you
want to run multiple operations concurrently — or if you are integrating with an async web
framework — blocking is a problem.

`AsyncNode` uses `async def` methods so the event loop can suspend execution during I/O
waits and run other coroutines. The lifecycle is identical to a synchronous node:
`prep_async` reads, `exec_async` works, `post_async` writes. The only difference is that
each method is awaited.

### The pattern

```
[Start] → [FetchData (AsyncNode)] → [Process] → [Stop]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_async_node`.

**Step 2: Drag the Async Node from the palette.**

Drag **Async Node** onto the canvas. Title it `Fetch Data`. In Inspector, confirm that
Base Class shows `AsyncNode`. This tells the code generator and runner that this node
uses the async lifecycle.

**Step 3: Write Fetch Data's code.**

```python
import aiohttp

class FetchData(AsyncNode):
    async def prep_async(self, shared):
        return shared.get("url", "https://httpbin.org/get")

    async def exec_async(self, prep_res):
        async with aiohttp.ClientSession() as session:
            async with session.get(prep_res) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def post_async(self, shared, prep_res, exec_res):
        shared["response"] = exec_res
        return "default"
```

The `async with` pattern ensures the HTTP session is closed even if an exception occurs.
`raise_for_status()` turns HTTP error codes into exceptions, which triggers the framework's
retry logic rather than silently writing an error response to the shared store.

**Step 4: Wire Start → Fetch Data → Process → Stop.**

Add a Basic Node (`Process`) that reads `shared["response"]` and formats the output.

**Step 5: Install aiohttp if needed.**

```bash
pip install aiohttp
```

**Step 6: Run and inspect.**

Run > Run Active Flow. The Shared Store shows `response` as a parsed JSON object from
the HTTP response. Even though `exec_async` awaits a network call, the runner handles
this transparently.

**When to use AsyncNode:**
- HTTP calls, database queries, file I/O — any operation that waits on external systems.
- When integrating with async web frameworks (FastAPI, aiohttp server).
- Do not use it for CPU-bound work (e.g., matrix operations) — async does not add
  parallelism for CPU work, only for I/O waits.

**Expected result:** The Shared Store shows the parsed JSON response from `httpbin.org/get`.

---

## Tutorial 27: Async Batch Processing with AsyncBatchNode

**What you'll learn:** How to process a list of items with async operations, one item at a
time sequentially, and why sequential async is sometimes preferable to parallel async.

### Why this pattern exists

`AsyncBatchNode` is to `AsyncNode` what `BatchNode` is to `Node`: it iterates over a list
returned by `prep_async`, calling `exec_async` once per item. The iteration is sequential
— each `exec_async` completes before the next begins.

This makes `AsyncBatchNode` the right choice when you need async I/O (to avoid blocking)
but also need to respect rate limits or ordering guarantees. For true concurrency, use
`AsyncParallelBatchNode` (Tutorial 28).

### The pattern

```
[Start] → [FetchAll (AsyncBatchNode)] → [Aggregate] → [Stop]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_async_batch`.

**Step 2: Drag Async Batch from the palette.**

Title it `Fetch All`. Confirm Base Class: `AsyncBatchNode` in Inspector.

**Step 3: Write Fetch All's code.**

```python
import aiohttp

class FetchAll(AsyncBatchNode):
    async def prep_async(self, shared):
        # Return the list. AsyncBatchNode calls exec_async once per URL.
        return shared.get("urls", [
            "https://httpbin.org/get",
            "https://httpbin.org/ip",
            "https://httpbin.org/headers",
        ])

    async def exec_async(self, url):
        # url is a single string, not the full list.
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return await resp.text()

    async def post_async(self, shared, prep_res, exec_res):
        # exec_res is a list: one result per URL.
        shared["pages"] = exec_res
        return "default"
```

**Step 4: Write Aggregate's code.**

```python
class Aggregate(Node):
    def prep(self, shared):
        return shared.get("pages", [])

    def exec(self, prep_res):
        # Extract just the first 200 characters of each page.
        return [p[:200] for p in prep_res]

    def post(self, shared, prep_res, exec_res):
        shared["summaries"] = exec_res
        for i, s in enumerate(exec_res):
            print(f"Page {i+1}: {s[:80]}...")
        return "default"
```

**Step 5: Run and compare timing.**

Run > Run Active Flow. The three URLs are fetched one after the other. Check the Run Log's
timing information — the total time is the sum of all three individual fetch times.

Now compare this to Tutorial 28 (parallel) where the total time is approximately the
slowest single fetch.

**Expected result:** `pages` contains three raw HTTP response bodies; `summaries` contains
their first 200 characters each.

---

## Tutorial 28: Concurrent Async Batch with AsyncParallelBatchNode

**What you'll learn:** How to fire multiple async operations simultaneously using
`AsyncParallelBatchNode`, and when concurrency is worth the added complexity.

### Why this pattern exists

When you have ten URLs to fetch and each takes one second, sequential async takes ten
seconds. Parallel async fires all ten simultaneously and finishes in approximately one
second. The speedup is real and significant for I/O-bound workloads.

The tradeoff: parallel requests hit external services all at once. Most APIs have rate
limits. The `max_concurrency` property caps how many requests run simultaneously, giving
you control over the burst rate.

### The pattern

```
[Start] → [ParallelFetch (AsyncParallelBatchNode)] → [Summarise] → [Stop]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_parallel_batch`.

**Step 2: Drag Async Parallel Batch from the palette.**

Title it `Parallel Fetch`. In Inspector, set `max_concurrency` to `5`. This means no more
than five requests run simultaneously even if the URL list has 100 entries.

**Step 3: Write Parallel Fetch's code.**

```python
import aiohttp

class ParallelFetch(AsyncParallelBatchNode):
    async def prep_async(self, shared):
        return shared.get("urls", [
            "https://httpbin.org/get",
            "https://httpbin.org/ip",
            "https://httpbin.org/headers",
            "https://httpbin.org/user-agent",
            "https://httpbin.org/uuid",
        ])

    async def exec_async(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return {
                    "url": url,
                    "status": resp.status,
                    "size": len(await resp.text()),
                }

    async def post_async(self, shared, prep_res, exec_res):
        # Results are in the same order as the input list, even though
        # execution happened concurrently.
        shared["results"] = exec_res
        return "default"
```

The result order guarantee is important: even though requests complete in arbitrary order,
`post_async` receives results in the original URL list order. You can safely zip results
with the input list.

**Step 4: Write Summarise's code.**

```python
class Summarise(Node):
    def prep(self, shared):
        return shared.get("results", [])

    def exec(self, prep_res):
        lines = [f"{r['url']} → status {r['status']}, {r['size']} bytes" for r in prep_res]
        return "\n".join(lines)

    def post(self, shared, prep_res, exec_res):
        shared["report"] = exec_res
        print(exec_res)
        return "default"
```

**Step 5: Run and observe the timing.**

Run > Run Active Flow. All five requests fire concurrently. The Run Log shows them all
completing before `Summarise` begins. The total time is close to the slowest individual
request, not the sum of all requests.

**When to use parallel vs. sequential async:**
- Use parallel when you have independent I/O operations and want minimum total time.
- Use sequential (`AsyncBatchNode`) when you need to respect rate limits or when
  results from one call affect the next.
- Use plain `BatchNode` when the operations are synchronous (no async I/O needed).

**Expected result:** `results` contains five entries with status codes and sizes. Total
execution time is much less than five times the per-request time.

---

## Tutorial 29: Using the Agent Node

**What you'll learn:** How the Agent Node encapsulates the tool-calling loop as a single
configured component, and how it differs from building the agent loop manually in Tutorial 12.

### Why this pattern exists

Tutorial 12 showed the agent pattern in full detail: a Router Node, three tool nodes, loop-
back edges. That approach gives you complete control. The Agent Node is the same pattern
wrapped into a reusable component with configurable properties.

Use the Agent Node when the tool list is known at configuration time and the decision logic
is standard (ask the LLM, pick a tool, loop). Build the manual pattern when you need
custom routing logic, non-standard tools, or visibility into each decision step.

### The pattern

```
[Start] → [Agent (AgentNode)] ──tool_call──→ [ExecuteTool] → [Agent]
                               └─answer────→ [Stop]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_agent_node`.

**Step 2: Drag Agent Node from the palette.**

Title it `Agent`. In Inspector, set:
- `tools`: `["search", "calculate"]`
- `max_iterations`: `10`

These properties configure the node without requiring code changes.

**Step 3: Write Agent's code.**

```python
TOOLS = {
    "search": lambda q: f"[Search result for '{q}': relevant information found]",
    "calculate": lambda expr: f"[Calculation result: {eval(expr) if expr.replace('.','').replace('-','').isdigit() else 'N/A'}]",  # noqa: S307
}

class Agent(Node):
    def prep(self, shared):
        return shared.get("question", ""), shared.get("tool_history", [])

    def exec(self, prep_res):
        question, history = prep_res
        ctx = "\n".join(f"- {h}" for h in history[-6:])
        prompt = (
            f"Question: {question}\n"
            f"Available tools: {', '.join(TOOLS.keys())}\n"
            f"Steps taken:\n{ctx or 'none'}\n\n"
            "What should I do next? Reply with exactly one tool name, or 'answer' to give a final response."
        )
        return call_llm(prompt).strip().lower()

    def post(self, shared, prep_res, exec_res):
        question, history = prep_res
        iterations = shared.get("agent_iterations", 0) + 1
        shared["agent_iterations"] = iterations
        shared.setdefault("tool_history", []).append(f"step {iterations}: {exec_res}")

        if iterations >= 10 or exec_res not in TOOLS:
            return "answer"
        return "tool_call"
```

**Step 4: Write Execute Tool's code.**

```python
class ExecuteTool(Node):
    def prep(self, shared):
        history = shared.get("tool_history", [])
        # The last entry is the most recent decision.
        last = history[-1] if history else ""
        # Parse "step N: tool_name" to find which tool to call.
        tool_name = last.split(": ", 1)[-1] if ": " in last else "search"
        return tool_name, shared.get("question", "")

    def exec(self, prep_res):
        tool_name, question = prep_res
        tool_fn = TOOLS.get(tool_name, TOOLS["search"])
        return tool_fn(question)

    def post(self, shared, prep_res, exec_res):
        shared["tool_history"].append(f"result: {exec_res}")
        shared["last_tool_result"] = exec_res
        return "default"
```

**Step 5: Wire and run in debug mode.**

Wire: Start → Agent, Agent → Execute Tool (`tool_call`), Execute Tool → Agent (`default`),
Agent → Stop (`answer`).

Run > Debug Active Flow. Set a breakpoint on **Agent** to watch each decision. After each
tool call, check `tool_history` growing in the Shared Store. The loop terminates when
the LLM decides `answer` or when `max_iterations` is reached.

**Expected result:** The agent loops through tool calls and terminates with a final answer
in the Shared Store. `agent_iterations` shows how many rounds it took.

---

## Tutorial 30: Using the RAG Node

**What you'll learn:** How the RAG Node separates the embedding step from the retrieval step
in a clean, inspectable way, and when to use it versus the full RAG pipeline from Tutorial 13.

### Why this pattern exists

Tutorial 13 showed the complete RAG pipeline: chunking, embedding, storing, querying,
retrieving, generating. The RAG Node packages the embedding step into a single configured
component, making the pipeline shorter to set up for standard use cases.

Use the full pipeline from Tutorial 13 when you need to customise chunking strategy,
embedding models, or retrieval algorithms. Use the RAG Node when the defaults are
sufficient and you want less boilerplate.

### The pattern

```
[Start] → [EmbedQuery (RAG Node)] → [Retrieve] → [Generate] → [Stop]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_rag_node`.

**Step 2: Drag RAG Node from the palette.**

Title it `Embed Query`. In Inspector, set:
- `top_k`: `5` — how many chunks to retrieve
- `index_key`: `embeddings` — the shared store key where embeddings are stored

**Step 3: Write Embed Query's code.**

```python
class EmbedQuery(Node):
    def prep(self, shared):
        return shared.get("question", "")

    def exec(self, prep_res):
        # In production: return embedding_model.encode(prep_res)
        import hashlib
        h = hashlib.md5(prep_res.encode()).digest()
        return [b / 255.0 for b in h]

    def post(self, shared, prep_res, exec_res):
        shared["query_vector"] = exec_res
        return "default"
```

**Step 4: Write Retrieve's code.**

```python
class Retrieve(Node):
    TOP_K = 5

    def prep(self, shared):
        return (
            shared["query_vector"],
            shared.get("embeddings", []),
            shared.get("chunks", []),
        )

    def exec(self, prep_res):
        q_vec, emb_list, chunks = prep_res
        def dot(a, b):
            return sum(x * y for x, y in zip(a, b))
        scored = sorted(
            [(dot(q_vec, e), c) for e, c in zip(emb_list, chunks)],
            reverse=True,
        )
        return [c for _, c in scored[:self.TOP_K]]

    def post(self, shared, prep_res, exec_res):
        shared["context"] = exec_res
        return "default"
```

**Step 5: Write Generate's code.**

```python
class Generate(Node):
    def prep(self, shared):
        context = "\n\n".join(shared.get("context", []))
        question = shared.get("question", "")
        return (
            f"Use only the following context to answer the question.\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n"
            f"Answer:"
        )

    def exec(self, prep_res):
        return call_llm(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res
        print("Answer:", exec_res)
        return "default"
```

**Step 6: Set up the index.**

Before running, populate `embeddings` and `chunks` in the Shared Store Designer with
pre-computed values, or run the indexing phase from Tutorial 13 first and copy the values
across. In production, indexing runs once and the index is stored in a vector database.

**Step 7: Run and inspect.**

Set `question` in the Shared Store Designer. Run > Run Active Flow. Inspect `query_vector`,
`context` (retrieved chunks), and `answer` in the Shared Store tab.

**Expected result:** The retrieved `context` chunks are semantically related to the
question, and the `answer` is grounded in that context rather than the LLM's training data.

---

## Tutorial 31: Using the Judge Node

**What you'll learn:** How the Judge Node evaluates LLM output against explicit criteria,
how the max-iteration guard ensures termination, and how to configure the criteria for
different quality standards.

### Why this pattern exists

Tutorial 16 showed the evaluator loop built manually from scratch. The Judge Node packages
that pattern into a single configured component. The criteria, the maximum iterations, and
the pass/fail routing are all set in the Inspector rather than coded into `exec`.

This makes the judge easy to reuse: change the criteria for a new task without touching
the node's code structure.

### The pattern

```
[Start] → [Generate] → [Judge (Judge Node)] ──pass──→ [Stop]
              ^                              └─fail──→ [Refine] → [Generate]
```

### Step-by-step

**Step 1: Create the project.**

New project: `tut_judge_node`.

**Step 2: Drag Judge Node from the palette.**

Title it `Judge`. In Inspector, set:
- `max_iterations`: `3` — the flow will always pass after 3 evaluations regardless of quality
- `criteria`: `"Is the output clear, accurate, and complete? Does it fully answer the question?"`

**Step 3: Write Generate's code.**

```python
class Generate(Node):
    def prep(self, shared):
        task = shared.get("task", "Explain recursion in one paragraph for a beginner.")
        feedback = shared.get("judge_feedback", "")
        if feedback:
            output = shared.get("output", "")
            return f"Revise this output based on the feedback.\nFeedback: {feedback}\n\nOriginal:\n{output}"
        return task

    def exec(self, prep_res):
        return call_llm(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["output"] = exec_res
        return "default"
```

**Step 4: Write Judge's code.**

```python
class Judge(Node):
    MAX_ITERATIONS = 3

    def prep(self, shared):
        return shared.get("output", ""), shared.get("judge_iteration", 0)

    def exec(self, prep_res):
        output, iteration = prep_res
        if iteration >= self.MAX_ITERATIONS:
            return "pass"

        criteria = shared.get(
            "criteria",
            "Is the output clear, accurate, and complete?"
        )
        prompt = (
            f"Evaluate this output against the criteria.\n"
            f"Criteria: {criteria}\n\n"
            f"Output:\n{output}\n\n"
            "Respond with PASS if the criteria are met, or FAIL followed by "
            "one sentence of specific, actionable feedback."
        )
        verdict = call_llm(prompt).strip()
        if verdict.upper().startswith("PASS"):
            return "pass"
        return ("fail", verdict)

    def post(self, shared, prep_res, exec_res):
        output, iteration = prep_res
        shared["judge_iteration"] = iteration + 1
        if isinstance(exec_res, tuple):
            action, feedback = exec_res
            shared["judge_feedback"] = feedback
            return action
        return exec_res
```

**Step 5: Write Refine's code.**

Refine is a passthrough — Generate reads `judge_feedback` directly on its next call:

```python
class Refine(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 6: Wire the refinement loop.**

Start → Generate → Judge, Judge → Stop (`pass`), Judge → Refine (`fail`),
Refine → Generate (`default`).

**Step 7: Run in debug mode.**

Set `task` and `criteria` in the Shared Store Designer. Run > Debug Active Flow with a
breakpoint on **Judge**. After each evaluation, check `judge_feedback` in the Shared Store.
After `max_iterations`, the Judge forces `pass` regardless of the verdict.

**Step 8: Tune the criteria.**

Change `criteria` in the Shared Store Designer and rerun without changing any code.
The same Judge node evaluates against the new criteria. This is the advantage of
making criteria a runtime property rather than hardcoding it in `exec`.

**Expected result:** The flow terminates in 1–4 iterations. `judge_iteration` shows the
count. `output` contains the final (possibly refined) result. `judge_feedback` shows
the last piece of feedback given (empty if the first attempt passed).

---

## Tutorial 32: Human Input + Classifier — Interactive Sentiment Triage

**What you'll learn:** How to collect free-text input from the user at runtime using a
Human Input Node, then route the flow to different branches based on sentiment
classification with a Classifier Node.

**Prerequisites:** Tutorial 15 (Human-in-the-Loop) and Tutorial 11 (Conditional Routing).

---

### Why this combination exists

Most LLM workflows operate on data that was prepared before the run started — a file, a
database query, a previous step's output. But many real applications need to ask the user
something mid-flow: which document to process, what question to answer, or — as in this
tutorial — what text to analyse.

The Human Input Node pauses the runner, shows a dialog to collect data, and merges the
result into shared state before the next node executes. Paired with a Classifier Node, you
get a pattern that appears constantly in customer support, content moderation, and triage
systems: the user provides the input, the LLM labels it, and the flow branches to the
handler that matches that label.

---

### The flow you will build

A customer review sentiment triage tool. The user types a review into a dialog at runtime.
The Classifier Node sends it to an LLM and asks it to label the sentiment as `positive`,
`negative`, or `neutral`. Each branch drafts an appropriate follow-up response using a
separate LLM Prompt Node.

```
                                    ┌──positive──► [Draft Praise]    ──► [Stop]
                                    │
[Start] ──► [Collect Review] ──saved──► [Classify Sentiment] ──negative──► [Draft Apology]  ──► [Stop]
                             │
                             │                              ──neutral───► [Draft Follow-up] ──► [Stop]
                             │
                          cancelled──────────────────────────────────────────────────────────► [Stop]
```

The `saved` / `cancelled` split handles the case where the user closes the dialog without
saving — the flow exits cleanly without calling the LLM.

---

### Step-by-step

**Step 1: Create the project.**

File > New Project. Name it `tut_sentiment_triage`. Creator creates the standard folder
structure and opens an empty canvas.

---

**Step 2: Add the Start Node.**

Drag **Start Node** from the palette onto the canvas. It becomes the flow's entry point
automatically.

---

**Step 3: Add a Human Input Node.**

Drag **Human Input Node** onto the canvas to the right of Start. In the Inspector, set:

| Property | Value |
|---|---|
| **Title** | `Collect Review` |
| **input_type** | `form` |
| **fields** | `review:string::` |
| **output_key** | `input` |

The `fields` value `review:string::` defines a single text field:
- `review` — the field label shown in the dialog and the key written to shared state
- `string` — data type (plain text)
- third segment empty — no default value
- fourth segment empty — no dropdown choices

When the node runs, a dialog appears with a single text box labelled **review**. When the
user clicks **Save**, the value is written to `shared['review']`. When the user clicks
**Cancel**, the node takes the `cancelled` action instead.

> **Field definition syntax:** `label:type:default:choices`
>
> Multiple fields are separated by semicolons. Examples:
> - `name:string:Anonymous:` — text field, default "Anonymous"
> - `rating:integer:5:` — integer spinner, default 5
> - `status:string::active,closed,pending` — dropdown, three choices

---

**Step 4: Add a Classifier Node.**

Drag **Classifier Node** onto the canvas to the right of Collect Review. In the Inspector,
set:

| Property | Value |
|---|---|
| **Title** | `Classify Sentiment` |
| **input_key** | `review` |
| **categories** | `positive,negative,neutral` |

`input_key: review` tells the Classifier to read `shared['review']` — the same key the
Human Input Node wrote. `categories` lists the exact labels the LLM should choose from.
These labels must match the action names on the outgoing edges you will draw in Step 6.

Leave `prompt_file` empty. The Classifier auto-builds a prompt from `categories` and the
text at `input_key`.

---

**Step 5: Add three LLM Prompt Nodes and a Stop Node.**

Drag three **LLM Prompt Node** items onto the canvas, one for each branch. Name them:

- `Draft Praise` (positive branch)
- `Draft Apology` (negative branch)
- `Draft Follow-up` (neutral branch)

Drag a **Stop Node** onto the canvas. A single Stop Node handles all three branches — you
will connect all three LLM nodes to it.

For each LLM node, set `prompt_type` to `string` and fill `prompt_file` with a
branch-specific prompt:

**Draft Praise** — `prompt_file`:
```
The customer left this positive review: {review}

Write a short, warm thank-you message (2–3 sentences) acknowledging their feedback.
```

**Draft Apology** — `prompt_file`:
```
The customer left this negative review: {review}

Write a sincere apology and offer to resolve the issue. Keep it under 4 sentences.
```

**Draft Follow-up** — `prompt_file`:
```
The customer left this neutral review: {review}

Write a friendly follow-up asking what we could do better. Keep it under 3 sentences.
```

The `{review}` placeholder is replaced at runtime with `shared['review']` — the text the
user entered in the dialog.

For each LLM node, set `output_key` to `response` so all three branches write to the
same key (the Stop node just ends the flow regardless).

---

**Step 6: Wire the edges.**

Connect nodes in this order, using the action names shown:

| From | Action | To |
|---|---|---|
| Start | `default` | Collect Review |
| Collect Review | `saved` | Classify Sentiment |
| Collect Review | `cancelled` | Stop |
| Classify Sentiment | `positive` | Draft Praise |
| Classify Sentiment | `negative` | Draft Apology |
| Classify Sentiment | `neutral` | Draft Follow-up |
| Draft Praise | `default` | Stop |
| Draft Apology | `default` | Stop |
| Draft Follow-up | `default` | Stop |

The Classifier Node's outgoing action names (`positive`, `negative`, `neutral`) must
exactly match the category labels you set in the `categories` property. The Classifier
asks the LLM to reply with one of those labels, then uses the reply to choose which edge
to follow.

> **If the LLM returns a label that is not an exact match**, the Classifier does fuzzy
> matching — it checks whether the response *contains* one of the action names. For
> example, `"The sentiment is negative."` matches the `negative` edge. If no match is
> found, it falls through to the first available action.

---

**Step 7: Arrange and Validate.**

Drag the nodes into a left-to-right arrangement that reflects the flow structure — Start
on the left, Stop on the right, branches fanning out in between. Then Project > Validate
Project (Ctrl+Shift+V). All nodes should show green — no missing connections or
unreachable edges.

---

**Step 8: Run the flow.**

Run > Run Active Flow (F5).

A dialog titled **Collect Review** appears with a single field:

```
┌─────────────────────────────────────────┐
│ Collect Review                          │
├─────────────────────────────────────────┤
│                                         │
│  review: [                            ] │
│                                         │
│              [  Save  ]  [ Cancel ]     │
└─────────────────────────────────────────┘
```

> **Form vs List mode buttons:**
> In **form mode** the dialog has **Save** and **Cancel** — click Save once all fields are
> filled.
> In **list mode** the dialog has **Add**, **Remove**, **Done**, and **Cancel** — use Add
> to collect as many items as needed, then click Done to finalise.

Type a review and click **Save**. The flow continues to the Classifier, which labels the
sentiment, routes to the matching LLM node, and writes the drafted response to
`shared['response']`.

Switch to the **Run Log** tab. You will see:

```
  [start]           Start               → default
  [collect_review]  Collect Review      → saved
  [classify]        Classify Sentiment  → negative
  [draft_apology]   Draft Apology       → default
  [stop]            Stop                → default
```

Switch to the **Shared Store** tab. You will see:

```
review: This product broke after two days. Very disappointed.
classify_label: negative
response: We're truly sorry to hear about your experience...
```

Click **Cancel** in the dialog instead of Save: the Run Log shows `Collect Review →
cancelled` and the flow goes straight to Stop — no LLM call is made.

---

**Step 9: Extend the flow.**

Now that the skeleton works, try these variations:

**Add a second field.** Change `fields` in Collect Review to:

```
name:string:Anonymous:;review:string::
```

Two fields: `name` (with default "Anonymous") and `review`. The Shared Store now contains
`shared['name']` and `shared['review']`. Update the prompts to include `{name}` where
appropriate.

**Add a dropdown.** Change `fields` to:

```
product:string::Widget Pro,Widget Lite,Widget Max;review:string::
```

The `product` field becomes a dropdown. Shared state gets `shared['product']` and
`shared['review']`.

**Add more categories.** Add `urgent` to `categories`: `positive,negative,neutral,urgent`.
Draw a new edge from **Classify Sentiment** with action `urgent` to a new **Draft Escalation**
LLM node. No other node changes — just wire the new branch.

---

### Key concepts from this tutorial

| Concept | Where it appears |
|---|---|
| Human Input pauses the runner | `Collect Review` shows a dialog; the runner thread blocks until Save or Cancel |
| Field definitions | `label:type:default:choices` syntax; multiple fields separated by `;` |
| `saved` / `cancelled` routing | Human Input takes `saved` when the user clicks Save, `cancelled` on Cancel |
| Prompt interpolation | `{review}` in any prompt is replaced with `shared['review']` at runtime |
| Classifier label matching | The LLM is asked to choose one of the categories; the reply selects the outgoing edge |
| Fuzzy label matching | If the LLM elaborates rather than replying with just the label, the runner extracts the best match |

---

[→ Continue to Part 3 — Advanced Features](part3_advanced.md)
