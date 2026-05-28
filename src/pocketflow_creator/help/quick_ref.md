# PocketFlow Node Reference

A concise description of every built-in node type available in the Component Palette.
Each node generates a class that inherits from the named PocketFlow base class.

---

## The Node Data Contract: Actions, Reads, and Writes

Every node has three Inspector fields that together describe its **data contract** — the
formal agreement between the node and the rest of the flow.

### Actions — the routing outputs

When a node finishes, its `post()` method returns a **string**. PocketFlow follows the
outgoing edge whose label matches that string to reach the next node. The **Actions**
field in the Inspector is the comma-separated list of strings `post()` might return.

```
post() returns "approved"  →  graph follows the "approved" edge  →  next node runs
```

Every outgoing edge label must match one of the node's declared actions. The validator
enforces this — undeclared actions produce error PFCE2101. Declaring all actions before
drawing edges causes the canvas to create a labelled output port for each one, making
the routing structure visible without opening any code.

| Pattern | Actions declaration |
|---|---|
| Simple linear step | `default` |
| Binary gate | `approved, rejected` |
| Multi-way classifier | `positive, negative, neutral` |
| Self-looping agent | `done, continue` |

### Reads — what the node takes from the shared store

The **shared store** is the `dict` that flows through every node in the graph. It is the
only channel through which nodes pass data to each other. A node's `prep()` method pulls
the inputs it needs:

```python
def prep(self, shared: dict) -> str:
    return shared["user_input"]   # reads "user_input" from the shared store
```

The **Reads** field documents which keys `prep()` consumes. It is not enforced at
runtime, but it powers the **Data Flow Report** and makes dependencies visible on the
canvas without reading code.

### Writes — what the node puts back into the shared store

After doing its work, `post()` stores results for downstream nodes:

```python
def post(self, shared: dict, prep_res, exec_res: str) -> str:
    shared["llm_response"] = exec_res   # writes "llm_response" for downstream nodes
    return "default"
```

The **Writes** field documents which keys `post()` produces. Combined with Reads across
all nodes, the **Data Flow Report** (Project > Data Flow Report) can show the full key
lifecycle: who writes each key, who reads it, and whether any key is read before it is
written.

### Summary table

```
Inspector field  Maps to        Role
───────────────  ─────────────  ─────────────────────────────────────────────
Reads            prep(shared)   Pull inputs from the shared store
Writes           post(shared)   Push outputs into the shared store
Actions          return value   Choose which outgoing edge to follow
                 of post()
```

> Reads and Writes are **documentation** — not runtime enforcement. Fill them in
> carefully and the Data Flow Report becomes a live audit of your graph's data flow.

---

## Flow Control

### Start Node
**Base class:** `Node`

Marks the entry point of a flow. Every graph must have exactly one start node.
The `post()` method returns `"default"` to continue to the first real processing node.
The Start Node itself does no work — it is a routing anchor only.

### Stop Node
**Base class:** `Node`

Marks a terminal point in the flow. A graph may have multiple Stop Nodes (one per
exit path). When the flow reaches a Stop Node it halts execution. Use separate Stop Nodes
for distinct exit conditions (e.g. `success` vs `error`) to make the graph self-documenting.

### Router Node
**Base class:** `Node`

Routes execution to one of several branches based on a decision made in `exec()`.
The `post()` method returns the chosen action string; each action must be wired to a
downstream node. Declare all possible actions in the Inspector **Actions** field.
Use this for conditional logic, guardrails, and state-machine transitions.

### Subflow Node
**Base class:** `Node`

Embeds a reusable sub-graph inside the current flow. Set the `subflow_ref` property to a
path relative to the project root (e.g. `graphs/summarizer.pfcgraph.yaml`). When the
runner reaches this node it executes the referenced graph inline, merging its shared store
state back into the parent flow before continuing.

---

## LLM / AI

### LLM Prompt Node
**Base class:** `Node`

The standard node for making a single call to a language model.

| Property | Default | Description |
|---|---|---|
| `prompt_type` | `string` | `string` — treat `prompt_file` as literal text; `path` — read from a file |
| `prompt_file` | _(empty)_ | The prompt text or file path, depending on `prompt_type` |
| `model` | _(project default)_ | Override the model for this node only |
| `temperature` | `0.7` | Sampling temperature 0–1 |
| `max_tokens` | `1024` | Max tokens in the response |
| `output_key` | `output` | Shared store key where the response is written |

Choose `prompt_type = string` to type the prompt directly into the Inspector.
Choose `prompt_type = path` to load a Markdown file at runtime — useful for long or
version-controlled prompts. The `Prompt Preview` tab shows the resolved prompt either way.

### JSON LLM Node
**Base class:** `Node`

Like LLM Prompt Node but instructs the model to respond with structured JSON. Supports
the same `prompt_type` / `prompt_file` duality — use `string` for short inline instructions
or `path` for a Markdown schema-description file. The parsed JSON object is written to
the shared store under `output_key`. Use this for data extraction, classification with
typed output, and any workflow that feeds LLM output into downstream Python code.

### Classifier Node
**Base class:** `Node`

Sends a classification prompt to the LLM and returns one of a fixed set of labels.
The labels are declared as **Actions** in the Inspector so the graph can route on the
result without a separate Router Node. Simpler than a Router Node for pure
text-in → label-out patterns (sentiment, intent detection, topic routing).

### Agent Node
**Base class:** `Node`

Implements the decide-act loop of an autonomous LLM agent. On each iteration the LLM
chooses an action from the `tools` list; the loop continues until the agent returns
`"answer"` or `max_iterations` is reached. Wire `tool_call` edges to individual tool
nodes that each loop back to the Agent Node. Wire `answer` to the final output node.

### RAG Node
**Base class:** `Node`

Encapsulates the embedding and retrieval step of a Retrieval-Augmented Generation
pipeline. Given a query, it embeds the query vector and retrieves the `top_k` most
similar chunks from the index stored at `index_key` in the shared store. The retrieved
context is written to `shared["context"]` for a downstream LLM Prompt Node to consume.

### Judge Node
**Base class:** `Node`

Evaluates LLM-generated output against a `criteria` string using a second LLM call.
Returns `"pass"` if the output meets the bar or `"fail"` to trigger a refinement loop.
A `max_iterations` guard in `post()` forces `"pass"` after N attempts so the flow
always terminates. Wire `fail` to a Refine node that improves the output and loops back
to the generator.

---

## Data / I/O

### File Reader Node
**Base class:** `Node`

Reads a file from disk and writes its contents into the shared store. Set `file_path`
in the Inspector to a path relative to the project root. The node is intentionally
minimal — decoding, parsing, and chunking belong in a downstream Basic Node so you
control the format.

### File Writer Node
**Base class:** `Node`

Writes data from the shared store to a file on disk. The node stub is intentionally
left for you to implement because the format (text, JSON, CSV, binary), path strategy,
and encoding are application-specific. Fill in `exec()` with the serialisation logic
your flow requires.

### Python Tool Node
**Base class:** `Node`

Runs an arbitrary Python function or shell command. Use this for calculations,
external API calls, data transformations, or any work that does not involve an LLM.
`exec()` is generated as a plain Python method body — write whatever code you need.
The node is the escape hatch for anything that does not fit another node type.

---

## Processing

### Basic Node
**Base class:** `Node`

The general-purpose building block. Use a Basic Node for any step that does not fit a
more specific type: data preparation, state updates, printing output, calling a library,
or any single-step operation with a `"default"` exit. When in doubt, start with a Basic
Node and refactor to a more specific type once the pattern becomes clear.

### Batch Node
**Base class:** `BatchNode`

Processes a list of items by calling `exec()` once per item. `prep()` returns the list;
`exec(item)` handles one item; `post()` receives the full results list. Use this for
map-style processing: scoring a batch of resumes, translating a list of sentences,
or embedding a list of text chunks. The batch runs synchronously and sequentially.

### Async Node
**Base class:** `AsyncNode`

A single-step node whose `exec_async()` method is an `async def` coroutine. Use this
whenever the work is I/O-bound (HTTP requests, database queries, file reads) and you
want to yield the event loop rather than block. Methods are named `prep_async`,
`exec_async`, and `post_async`. The runner wraps execution in `asyncio.run()`.

### Async Batch Node
**Base class:** `AsyncBatchNode`

Processes a list of items by awaiting `exec_async(item)` for each item in turn.
Like Batch Node but non-blocking: each item's I/O yields the event loop while
waiting. Use when each item requires an async operation (e.g. fetching a URL,
querying an async database driver) but you do not need parallel execution.

### Async Parallel Batch Node
**Base class:** `AsyncParallelBatchNode`

Processes a list of items by launching all `exec_async(item)` calls concurrently
via `asyncio.gather`. Results are collected in the original order. Set `max_concurrency`
in the Inspector to limit how many coroutines run simultaneously. Use this when items
are independent and latency dominates — fetching many URLs, calling an API in parallel,
or embedding many chunks concurrently.

---

## Human in the Loop

### Human Review Node
**Base class:** `Node`

Pauses the flow and presents content to a human reviewer. `exec()` prints or displays
the content and waits for input. `post()` routes to `"approved"` or `"rejected"` (or
any custom actions you declare). Use this for content moderation, data labelling,
quality gates, or any step that requires a human decision before the flow continues.

### Human Input Node
**Base class:** `Node`

Reads a string from the user at runtime (via `input()` or a UI prompt) and writes it
to the shared store under `output_key`. Use this as the interactive entry point for
flows that require user input each time they run — chatbots, question-answer tools, or
any pipeline where the query varies per invocation.

---

## Reference

| Node Type | Base Class | Primary Use |
|---|---|---|
| Start Node | `Node` | Flow entry point |
| Stop Node | `Node` | Flow exit point |
| Basic Node | `Node` | General-purpose single step |
| Router Node | `Node` | Conditional branching |
| Subflow Node | `Node` | Embedded sub-graph |
| LLM Prompt Node | `Node` | LLM call — inline string or file prompt |
| JSON LLM Node | `Node` | LLM call — structured JSON output, inline string or file prompt |
| Classifier Node | `Node` | LLM-based label classification |
| Agent Node | `Node` | Autonomous tool-calling loop |
| RAG Node | `Node` | Embedding and retrieval step |
| Judge Node | `Node` | LLM output evaluation |
| File Reader Node | `Node` | Read file from disk |
| File Writer Node | `Node` | Write file to disk |
| Python Tool Node | `Node` | Arbitrary Python / shell |
| Batch Node | `BatchNode` | Sequential batch processing |
| Async Node | `AsyncNode` | Single async I/O step |
| Async Batch Node | `AsyncBatchNode` | Sequential async batch |
| Async Parallel Batch Node | `AsyncParallelBatchNode` | Concurrent async batch |
| Human Review Node | `Node` | Human approval gate |
| Human Input Node | `Node` | Interactive user input |

---

- [Tutorials](tutorials/index.md)
- [About PocketFlow](about_pocketflow.md)
- [Help Home](index.md)
