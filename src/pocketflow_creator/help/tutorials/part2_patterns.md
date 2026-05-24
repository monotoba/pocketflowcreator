# Part 2 — PocketFlow Patterns in Creator

Each tutorial in this section maps a PocketFlow cookbook example to a Creator project.
You can complete these in any order after finishing Part 1.

[← Tutorials Index](index.md)

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
3. Wire: Start → Ask LLM (`default`), Ask LLM → Stop (`default`)
4. Auto Layout; Zoom to Fit
5. Double-click **Ask LLM** to open code editor

```python
class AskLlm(Node):
    def prep(self, shared):
        return shared.get("question", "What is PocketFlow?")

    def exec(self, prep_res):
        return call_llm(prep_res)

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
                         ^                                                  |
                         └──────────────────────────────────────────────────┘
[GetInput] --exit--> [Stop]
```

### Steps

1. New project: `tut_chat`
2. Add nodes:
   - **Start Node** (title: `Start`)
   - **Basic Node** (title: `Get Input`) — Actions: `continue, exit`
   - **LLM Prompt Node** (title: `Call LLM`)
   - **Basic Node** (title: `Print Reply`)
   - **Stop Node**
3. Wire edges with the loop: Print Reply → Get Input (`default`)
4. Double-click **Get Input**:

```python
class GetInput(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return input("You: ").strip()

    def post(self, shared, prep_res, exec_res):
        if exec_res.lower() in ("quit", "exit", "bye"):
            return "exit"
        shared.setdefault("history", [])
        shared["history"].append({"role": "user", "content": exec_res})
        return "continue"
```

5. Double-click **Call LLM**:

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

6. Run > Debug Active Flow; step through the loop

---

## Tutorial 9: Structured Output — Resume Data Extraction

**PocketFlow example:** `pocketflow-structured-output`
**What you'll learn:** Use an LLM to extract typed fields from unstructured text.

### Graph

```
[Start] → [LoadResume] → [ExtractFields] → [ValidateOutput] → [Stop]
```

### Steps

1. New project: `tut_structured_output`
2. Add nodes: Start, 3× Basic Node, Stop; wire sequentially
3. In Inspector for **Extract Fields**: Reads: `resume_text`, Writes: `extracted_data`
4. Double-click **Extract Fields**:

```python
class ExtractFields(Node):
    def prep(self, shared):
        return shared["resume_text"]

    def exec(self, prep_res):
        prompt = f"""Extract from this resume:
- name, email, years_of_experience (number), skills (list)

Resume:
{prep_res}

Respond as JSON only."""
        import json
        return json.loads(call_llm(prompt))

    def post(self, shared, prep_res, exec_res):
        shared["extracted_data"] = exec_res
        return "default"
```

5. Use Tools > Shared Store Inspector to define schema keys: `extracted_data`, `resume_text`

---

## Tutorial 10: Multi-Stage Workflow — Article Writer

**PocketFlow example:** `pocketflow-workflow`
**What you'll learn:** Chain LLM calls through distinct stages: outline → draft → style.

### Graph

```
[Start] → [GenerateOutline] → [WriteDraft] → [ApplyStyle] → [Stop]
```

### Steps

1. New project: `tut_workflow`
2. Add Start, 3× LLM Prompt Node, Stop; wire sequentially
3. Create prompt files: `prompts/outline.md`, `prompts/draft.md`, `prompts/style.md`
4. `prompts/outline.md`:
   ```
   Create a 5-point outline for an article about: {topic}
   Return only the outline as a numbered list.
   ```
5. Double-click **Generate Outline**:

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

6. Implement Write Draft and Apply Style similarly

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
2. Add Router Node (title: `Classify Input`) — Actions: `on_topic, off_topic`
3. Wire branches; validate that both action edges exist
4. Double-click **Classify Input**:

```python
class ClassifyInput(Node):
    def prep(self, shared):
        return shared.get("user_question", "")

    def exec(self, prep_res):
        prompt = f"Is this question about travel? Answer YES or NO.\nQuestion: {prep_res}"
        answer = call_llm(prompt).strip().upper()
        return "on_topic" if answer == "YES" else "off_topic"

    def post(self, shared, prep_res, exec_res):
        return exec_res
```

---

## Tutorial 12: Agent with Tools

**PocketFlow example:** `pocketflow-agent`
**What you'll learn:** Build an LLM agent that decides which tool to call.

### Graph

```
[Start] → [Decide] ──search────→ [WebSearch]  → [Decide]
                  ├─calculate──→ [Calculator] → [Decide]
                  └─answer────→ [FinalAnswer] → [Stop]
```

### Steps

1. New project: `tut_agent`
2. Add Router Node (title: `Decide`) — Actions: `search, calculate, answer`
3. Wire loops: Web Search → Decide, Calculator → Decide
4. Double-click **Decide**:

```python
class Decide(Node):
    TOOLS = ["search", "calculate", "answer"]

    def prep(self, shared):
        return shared.get("question", ""), shared.get("tool_history", [])

    def exec(self, prep_res):
        question, history = prep_res
        history_text = "\n".join(f"- {h}" for h in history)
        prompt = f"Question: {question}\nPrevious: {history_text or 'none'}\nChoose: search, calculate, or answer."
        action = call_llm(prompt).strip().lower()
        return action if action in self.TOOLS else "answer"

    def post(self, shared, prep_res, exec_res):
        shared.setdefault("tool_history", []).append(f"chose: {exec_res}")
        return exec_res
```

---

## Tutorial 13: Retrieval-Augmented Generation (RAG)

**PocketFlow example:** `pocketflow-rag`
**What you'll learn:** Index documents, retrieve relevant chunks, generate an answer.

### Graph

```
[Start] → [LoadDocs] → [EmbedChunks] → [StoreIndex]
        → [GetQuestion] → [RetrieveChunks] → [GenerateAnswer] → [Stop]
```

### Steps

1. New project: `tut_rag`
2. Set Reads/Writes in Inspector for each node to document the data contracts
3. Double-click **Embed Chunks**:

```python
class EmbedChunks(Node):
    def prep(self, shared):
        text = shared["raw_docs"]
        return [text[i:i+500] for i in range(0, len(text), 500)]

    def exec(self, prep_res):
        return [(chunk, [0.1] * 128) for chunk in prep_res]

    def post(self, shared, prep_res, exec_res):
        shared["chunks"] = [c for c, _ in exec_res]
        shared["embeddings"] = [e for _, e in exec_res]
        return "default"
```

4. Double-click **Generate Answer**:

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
        return "default"
```

---

## Tutorial 14: Map-Reduce / Batch Processing

**PocketFlow example:** `pocketflow-map-reduce`
**What you'll learn:** Use a Batch Node to process many items and reduce results.

### Graph

```
[Start] → [LoadItems] → [ProcessEach (BatchNode)] → [Aggregate] → [Stop]
```

### Steps

1. New project: `tut_map_reduce`
2. Add a **Batch Node** (title: `Process Each`)
3. Double-click **Process Each**:

```python
class ProcessEach(BatchNode):
    def prep(self, shared):
        return shared["items"]  # BatchNode calls exec once per item

    def exec(self, item):
        return call_llm(f"Rate this resume 1-10:\n{item}")

    def post(self, shared, prep_res, exec_res):
        shared["ratings"] = exec_res  # exec_res is a list
        return "default"
```

---

## Tutorial 15: Human-in-the-Loop

**PocketFlow example:** `pocketflow-fastapi-hitl`
**What you'll learn:** Pause execution for user approval before continuing.

### Graph

```
[Start] → [DraftContent] → [Review] ──approved──→ [Publish] → [Stop]
                                    └─rejected────→ [Revise]  → [Review]
```

### Steps

1. New project: `tut_hitl`
2. Add Human Review Node (Actions: `approved, rejected`)
3. Wire the approval loop (Revise → Review)
4. Double-click **Review**:

```python
class ReviewDraft(Node):
    def prep(self, shared):
        return shared.get("draft", "")

    def exec(self, prep_res):
        print("\n=== DRAFT ===\n", prep_res)
        return input("Approve? (yes/no): ").strip().lower()

    def post(self, shared, prep_res, exec_res):
        if exec_res in ("yes", "y"):
            return "approved"
        shared["feedback"] = input("Feedback: ").strip()
        return "rejected"
```

5. Run > Debug Active Flow; set breakpoint at Review to step through approvals

---

## Tutorial 16: LLM-as-Judge / Evaluator Loop

**PocketFlow example:** `pocketflow-judge`
**What you'll learn:** Use one LLM to generate content and another to evaluate and refine it.

### Graph

```
[Start] → [Generate] → [Evaluate] ──pass──→ [Stop]
                    ^              └─fail──→ [Refine] → [Generate]
```

### Steps

1. New project: `tut_judge`
2. Add Router Node (Evaluate) with Actions: `pass, fail`; wire the refinement loop
3. Double-click **Evaluate**:

```python
class Evaluate(Node):
    MAX_ITERATIONS = 3

    def prep(self, shared):
        return shared.get("output", ""), shared.get("iteration", 0)

    def exec(self, prep_res):
        output, iteration = prep_res
        if iteration >= self.MAX_ITERATIONS:
            return "pass"
        verdict = call_llm(f"Is the quality good enough? PASS or FAIL.\nOutput: {output}").strip().upper()
        return "pass" if verdict == "PASS" else "fail"

    def post(self, shared, prep_res, exec_res):
        shared["iteration"] = shared.get("iteration", 0) + 1
        return exec_res
```

---

## Tutorial 17: Multi-Agent System

**PocketFlow example:** `pocketflow-debate`
**What you'll learn:** Two agents with different roles run in a debate pattern.

### Graph

```
[Start] → [AgentA] → [AgentB] → [Judge] ──continue──→ [AgentA]
                                          └─conclude──→ [Summary] → [Stop]
```

### Steps

1. New project: `tut_debate`
2. Add Router Node (Judge) — Actions: `continue, conclude`
3. Double-click **Agent A**:

```python
class AgentAPropose(Node):
    def prep(self, shared):
        return shared.get("topic", "AI regulation"), shared.get("debate_history", [])

    def exec(self, prep_res):
        topic, history = prep_res
        context = "\n".join(history[-4:])
        return call_llm(f"Argue IN FAVOR of: {topic}\nContext:\n{context}\nMake your argument:")

    def post(self, shared, prep_res, exec_res):
        shared.setdefault("debate_history", []).append(f"PRO: {exec_res}")
        return "default"
```

4. Implement Agent B as the counter-argument and Judge to evaluate the winner
5. Run > Run Active Flow to watch the debate unfold in Run Log

---

## Tutorial 23: Streaming Output

**PocketFlow example:** `pocketflow-streaming`
**What you'll learn:** Design a flow that produces incremental output visible in real time.

### Graph

```
[Start] → [StreamLLM] → [PrintChunks] → [Stop]
```

### Steps

1. New project: `tut_streaming`
2. Add Basic Node (title: `Stream LLM`) with Writes: `chunks`
3. Double-click **Stream LLM**:

```python
class StreamLlm(Node):
    def prep(self, shared):
        return shared.get("prompt", "Tell me a story in 5 sentences.")

    def exec(self, prep_res):
        full_text = call_llm(prep_res)
        return full_text.split()  # simulate streaming as word chunks

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
**What you'll learn:** Maintain two memory layers: recent conversation and condensed summaries.

### Graph

```
[Start] → [GetInput] → [UpdateShortTerm] → [ShouldCondense?]
    ──yes──→ [CondenseToLongTerm] → [CallLLM] → [GetInput]
    ──no───→                        [CallLLM] → [GetInput]
[GetInput] --exit--> [Stop]
```

### Steps

1. New project: `tut_memory`
2. Add Router Node (`ShouldCondense?`) — Actions: `yes, no`
3. In Shared Store Designer define: `short_term_history` (array), `long_term_summary` (string), `condensation_threshold` (integer, default: 10)
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
        return shared.get("short_term_history", []), shared.get("long_term_summary", "")

    def exec(self, prep_res):
        history, old_summary = prep_res
        msgs = "\n".join(f"{m['role']}: {m['content']}" for m in history)
        prompt = f"Existing summary: {old_summary}\n\nNew messages:\n{msgs}\n\nCreate updated summary:"
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["long_term_summary"] = exec_res
        shared["short_term_history"] = []
        return "default"
```

---

## Tutorial 26: Async Processing with AsyncNode

**PocketFlow example:** `pocketflow-async`
**What you'll learn:** Run a single non-blocking operation using `AsyncNode` and `async def exec`.

### Graph

```
[Start] → [FetchData (AsyncNode)] → [Process] → [Stop]
```

### Steps

1. New project: `tut_async_node`
2. Drag **Async Node** from the palette; title it `Fetch Data`
3. In Inspector note that **Base Class** is set to `AsyncNode`
4. Double-click **Fetch Data** in the code editor:

```python
import asyncio
import aiohttp

class FetchData(AsyncNode):
    async def prep_async(self, shared):
        return shared.get("url", "https://httpbin.org/get")

    async def exec_async(self, prep_res):
        async with aiohttp.ClientSession() as session:
            async with session.get(prep_res) as resp:
                return await resp.json()

    async def post_async(self, shared, prep_res, exec_res):
        shared["response"] = exec_res
        return "default"
```

5. Wire Start → Fetch Data (`default`) → Stop
6. Run > Run Active Flow; check **Shared Store** tab for `response`

**Tip:** `AsyncNode` methods are `prep_async`, `exec_async`, and `post_async`. The runner
awaits each in turn inside an `asyncio.run()` context. Use this whenever the work is I/O-bound
(HTTP, database, file system) and you want it to yield the event loop rather than block.

---

## Tutorial 27: Async Batch Processing with AsyncBatchNode

**PocketFlow example:** `pocketflow-async-batch`
**What you'll learn:** Process a list of items asynchronously, one awaitable call per item.

### Graph

```
[Start] → [FetchAll (AsyncBatchNode)] → [Aggregate] → [Stop]
```

### Steps

1. New project: `tut_async_batch`
2. Drag **Async Batch** from the palette; title it `Fetch All`
3. Double-click **Fetch All**:

```python
import aiohttp

class FetchAll(AsyncBatchNode):
    async def prep_async(self, shared):
        return shared.get("urls", [])  # returns list; exec_async called once per item

    async def exec_async(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.text()

    async def post_async(self, shared, prep_res, exec_res):
        shared["pages"] = exec_res  # exec_res is a list of per-item results
        return "default"
```

4. Double-click **Aggregate**:

```python
class Aggregate(Node):
    def prep(self, shared):
        return shared.get("pages", [])

    def exec(self, prep_res):
        return [p[:200] for p in prep_res]  # first 200 chars of each page

    def post(self, shared, prep_res, exec_res):
        shared["summaries"] = exec_res
        return "default"
```

5. Set `shared["urls"]` in Start or use Shared Store Designer to define the key
6. Run > Run Active Flow; inspect `pages` and `summaries` in the Shared Store tab

**Tip:** `AsyncBatchNode.prep_async` returns an iterable; the framework awaits
`exec_async(item)` for each element sequentially. Use `AsyncParallelBatchNode` when
you need concurrent execution.

---

## Tutorial 28: Concurrent Async Batch with AsyncParallelBatchNode

**PocketFlow example:** `pocketflow-parallel-batch`
**What you'll learn:** Fire multiple async tasks concurrently, collect all results.

### Graph

```
[Start] → [ParallelFetch (AsyncParallelBatchNode)] → [Summarise] → [Stop]
```

### Steps

1. New project: `tut_parallel_batch`
2. Drag **Async Parallel Batch** from the palette; title it `Parallel Fetch`
3. In Inspector set `max_concurrency: 5` to cap simultaneous requests
4. Double-click **Parallel Fetch**:

```python
import asyncio
import aiohttp

class ParallelFetch(AsyncParallelBatchNode):
    async def prep_async(self, shared):
        return shared.get("urls", [])

    async def exec_async(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                return {"url": url, "status": r.status, "body": await r.text()}

    async def post_async(self, shared, prep_res, exec_res):
        shared["results"] = exec_res  # all items fetched concurrently
        return "default"
```

5. Wire and run; observe that all fetches complete before `Summarise` begins

**Tip:** `AsyncParallelBatchNode` uses `asyncio.gather` under the hood. All `exec_async`
calls are launched together and results are collected in the original order. Set
`max_concurrency` in Inspector to avoid overwhelming external services.

---

## Tutorial 29: Using the Agent Node

**PocketFlow example:** `pocketflow-agent`
**What you'll learn:** Use the dedicated **Agent Node** to build a tool-calling loop
without manually wiring a Router Node.

### Graph

```
[Start] → [Agent (AgentNode)] ──tool_call──→ [ExecuteTool] → [Agent]
                               └─answer────→ [Stop]
```

### Steps

1. New project: `tut_agent_node`
2. Drag **Agent Node** from the palette; title it `Agent`
3. In Inspector set:
   - `tools`: `["search", "calculate"]`
   - `max_iterations`: `10`
4. Double-click **Agent**:

```python
TOOLS = {"search": search_web, "calculate": run_calculator}

class Agent(Node):
    def prep(self, shared):
        history = shared.get("tool_history", [])
        question = shared.get("question", "")
        return question, history

    def exec(self, prep_res):
        question, history = prep_res
        ctx = "\n".join(f"- {h}" for h in history)
        prompt = (
            f"Question: {question}\n"
            f"Previous steps:\n{ctx or 'none'}\n"
            "Choose an action: search, calculate, or answer."
        )
        return call_llm(prompt).strip().lower()

    def post(self, shared, prep_res, exec_res):
        shared.setdefault("tool_history", []).append(f"chose: {exec_res}")
        iterations = shared.get("agent_iterations", 0) + 1
        shared["agent_iterations"] = iterations
        if iterations >= 10:
            return "answer"
        return exec_res if exec_res in ("search", "calculate") else "answer"
```

5. Add `Execute Tool` node; wire its `default` back to `Agent`
6. Run > Debug Active Flow; set a breakpoint on `Agent` to watch each decision

**Tip:** The Agent Node pattern encapsulates the decide-act loop. Keep decision logic
in `exec` and side effects (tool calls) in separate nodes. The shared store accumulates
tool results across iterations.

---

## Tutorial 30: Using the RAG Node

**PocketFlow example:** `pocketflow-rag`
**What you'll learn:** Use the dedicated **RAG Node** to handle retrieval + generation
as a single configured node.

### Graph

```
[Start] → [Embed Query (RAG Node)] → [Retrieve] → [Generate] → [Stop]
```

### Steps

1. New project: `tut_rag_node`
2. Drag **RAG Node** from the palette; title it `Embed Query`
3. In Inspector set:
   - `top_k`: `5`
   - `index_key`: `embeddings`
4. Double-click **Embed Query**:

```python
class EmbedQuery(Node):
    def prep(self, shared):
        return shared.get("question", "")

    def exec(self, prep_res):
        return embed(prep_res)  # returns a vector

    def post(self, shared, prep_res, exec_res):
        shared["query_vector"] = exec_res
        return "default"
```

5. Double-click **Retrieve**:

```python
class Retrieve(Node):
    TOP_K = 5

    def prep(self, shared):
        return shared["query_vector"], shared.get("embeddings", []), shared.get("chunks", [])

    def exec(self, prep_res):
        q_vec, emb_list, chunks = prep_res
        scores = [dot(q_vec, e) for e in emb_list]
        top = sorted(zip(scores, chunks), reverse=True)[:self.TOP_K]
        return [chunk for _, chunk in top]

    def post(self, shared, prep_res, exec_res):
        shared["context"] = exec_res
        return "default"
```

6. Implement **Generate** as an LLM Prompt Node that reads `context` and `question`
7. Use Tools > Shared Store Inspector to define keys: `question`, `embeddings`, `chunks`, `context`

**Tip:** The RAG Node separates the embedding step cleanly from retrieval. In production,
replace `embed()` with a real embedding model and store vectors in a vector database.

---

## Tutorial 31: Using the Judge Node

**PocketFlow example:** `pocketflow-judge`
**What you'll learn:** Use the dedicated **Judge Node** to evaluate and iteratively refine
LLM output until it meets a quality bar.

### Graph

```
[Start] → [Generate] → [Judge (Judge Node)] ──pass──→ [Stop]
              ^                              └─fail──→ [Refine] → [Generate]
```

### Steps

1. New project: `tut_judge_node`
2. Drag **Judge Node** from the palette; title it `Judge`
3. In Inspector set:
   - `max_iterations`: `3`
   - `criteria`: `"Is the output complete, accurate, and well-written?"`
4. Double-click **Judge**:

```python
class Judge(Node):
    MAX_ITERATIONS = 3

    def prep(self, shared):
        return shared.get("output", ""), shared.get("judge_iteration", 0)

    def exec(self, prep_res):
        output, iteration = prep_res
        if iteration >= self.MAX_ITERATIONS:
            return "pass"
        criteria = "Is the output complete, accurate, and well-written?"
        prompt = (
            f"Evaluate this output against the criteria.\n"
            f"Criteria: {criteria}\n"
            f"Output:\n{output}\n\n"
            "Respond with PASS or FAIL and a one-sentence reason."
        )
        verdict = call_llm(prompt)
        return "pass" if verdict.strip().upper().startswith("PASS") else "fail"

    def post(self, shared, prep_res, exec_res):
        shared["judge_iteration"] = shared.get("judge_iteration", 0) + 1
        return exec_res
```

5. Double-click **Refine**:

```python
class Refine(Node):
    def prep(self, shared):
        return shared.get("output", ""), shared.get("feedback", "Improve quality.")

    def exec(self, prep_res):
        output, feedback = prep_res
        return call_llm(f"Revise this output.\nFeedback: {feedback}\nOutput:\n{output}")

    def post(self, shared, prep_res, exec_res):
        shared["output"] = exec_res
        return "default"
```

6. Run > Debug Active Flow; set a breakpoint on **Judge** to inspect each evaluation round
7. After `max_iterations` the Judge always returns `pass` to prevent infinite loops

**Tip:** The `judge_iteration` counter in the shared store is the safety net. Always
increment it in `post` and add a guard in `exec` so the flow terminates even if the LLM
repeatedly returns FAIL.

---

[→ Continue to Part 3 — Advanced Features](part3_advanced.md)
