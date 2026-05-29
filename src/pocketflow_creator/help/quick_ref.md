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

## AI / Reasoning

### Chain of Thought Node
**Base class:** `Node`

Prompts an LLM to reason step-by-step before delivering an answer. Each reasoning
step is a separate LLM call and the intermediate steps are stored so they can be
inspected or logged. Use this when a single-shot answer is unreliable and you want
the model to "show its work" across `steps` incremental reasoning passes.

| Property | Default | Description |
|---|---|---|
| `model` | `gpt-4o` | LLM model name |
| `steps` | `3` | Number of reasoning steps |
| `output_key` | `cot_result` | Shared-store key for the final result |

### Majority Vote Node
**Base class:** `Node`

Generates `samples` independent answers to the same prompt and returns the most
frequent response. Self-consistency via majority vote improves accuracy on tasks
where the model occasionally makes mistakes. Works best with deterministic-ish
questions (math, code, multi-choice reasoning) rather than open-ended generation.

| Property | Default | Description |
|---|---|---|
| `model` | `gpt-4o` | LLM model name |
| `samples` | `5` | Number of independent samples |
| `output_key` | `voted_result` | Shared-store key for the winning answer |

### Supervisor Node
**Base class:** `Node`

Orchestrates one or more sub-agent nodes by deciding at each iteration whether to
`continue` (hand off to the next agent step), declare `done`, or signal `error`.
Wire `continue` to the sub-agent node and back to the Supervisor Node to build the
supervision loop. Set `max_iterations` to prevent runaway loops.

| Property | Default | Description |
|---|---|---|
| `model` | `gpt-4o` | LLM model name |
| `max_iterations` | `10` | Maximum supervision iterations |
| `output_key` | `supervisor_result` | Shared-store key for the final result |

### Debate Advocate Node
**Base class:** `Node`

Takes one side of a debate (`pro` or `con`) and generates the strongest possible
argument for that position. Pair two Debate Advocate Nodes (one per position) and
feed their outputs to a Debate Judge Node to implement an adversarial evaluation
pattern that tends to surface counterarguments missed by single-shot critique.

| Property | Default | Description |
|---|---|---|
| `model` | `gpt-4o` | LLM model name |
| `position` | `pro` | Debate position: `pro` or `con` |
| `output_key` | `advocate_argument` | Shared-store key for the argument text |

### Debate Judge Node
**Base class:** `Node`

Reads arguments from both sides of a debate (produced by Debate Advocate Nodes) and
decides the winner. Returns `pro_wins`, `con_wins`, or `tie`. Wire each action to a
different downstream node to take position-specific actions based on the outcome.

| Property | Default | Description |
|---|---|---|
| `model` | `gpt-4o` | LLM model name |
| `output_key` | `debate_verdict` | Shared-store key for the verdict string |

---

## Web / Search

### Web Search Node
**Base class:** `Node`

Runs a web search query and returns a list of result dicts. Reads the query from
`query_key` in the shared store, runs it through the configured search engine, and
writes up to `num_results` results to `output_key`. Routes `no_results` when the
search returns nothing, allowing the flow to fall back gracefully.

| Property | Default | Description |
|---|---|---|
| `engine` | `duckduckgo` | Search engine: `duckduckgo`, `google`, `bing` |
| `num_results` | `5` | Maximum results to return |
| `query_key` | `search_query` | Shared-store key for the query string |
| `output_key` | `search_results` | Shared-store key for the results list |

### Web Scrape Node
**Base class:** `Node`

Fetches the HTML at the URL stored in `url_key` and extracts clean plain text.
Strips navigation, ads, and boilerplate via a readability-style pass. Routes `error`
on network failure or timeout. Use downstream with a Text Chunk Node for RAG ingestion
or with an LLM Prompt Node for single-page summarisation.

| Property | Default | Description |
|---|---|---|
| `url_key` | `url` | Shared-store key containing the target URL |
| `output_key` | `scraped_text` | Shared-store key for extracted text |
| `timeout` | `10` | HTTP timeout in seconds |

### API Call Node
**Base class:** `Node`

Makes an HTTP request to any REST endpoint. Supports GET, POST, PUT, and DELETE.
The URL supports `{{key}}` interpolation from the shared store. Request headers and
body are read from separate shared-store keys so they can be constructed dynamically
by upstream nodes. Routes `error` on non-2xx responses.

| Property | Default | Description |
|---|---|---|
| `url` | _(empty)_ | Endpoint URL (supports `{{key}}` interpolation) |
| `method` | `GET` | HTTP method |
| `headers_key` | _(empty)_ | Shared-store key for extra headers dict |
| `body_key` | _(empty)_ | Shared-store key for request body |
| `output_key` | `api_response` | Shared-store key for the response |

---

## Data / Vector

### Text Chunk Node
**Base class:** `Node`

Splits a long text into overlapping chunks of `chunk_size` tokens (or characters).
Writes a list of chunk strings to `output_key`. Use as the first step of a RAG
ingestion pipeline before an Embed Node and Vector Index Node.

| Property | Default | Description |
|---|---|---|
| `input_key` | `text` | Shared-store key for the source text |
| `chunk_size` | `512` | Chunk size in tokens/characters |
| `overlap` | `64` | Overlap between consecutive chunks |
| `output_key` | `chunks` | Shared-store key for the chunks list |

### Embed Node
**Base class:** `Node`

Generates embedding vectors for a string or list of strings using the configured
embedding model. Single string → single vector; list → list of vectors. Pair with
Vector Index Node to build an index or with Vector Retrieve Node to embed a query
before retrieval.

| Property | Default | Description |
|---|---|---|
| `model` | `text-embedding-3-small` | Embedding model name |
| `input_key` | `chunks` | Shared-store key for text or text list |
| `output_key` | `embeddings` | Shared-store key for the embedding vector(s) |

### Vector Index Node
**Base class:** `Node`

Builds a vector store index from a list of embedding vectors. Supports FAISS,
Chroma, and Pinecone backends. Writes the built index object to `index_key` for
use by a downstream Vector Retrieve Node. Use this once during ingestion; cache the
result if the document set rarely changes.

| Property | Default | Description |
|---|---|---|
| `store_type` | `faiss` | Vector store backend: `faiss`, `chroma`, `pinecone` |
| `embeddings_key` | `embeddings` | Shared-store key for the vectors to index |
| `index_key` | `vector_index` | Shared-store key for the built index |

### Vector Retrieve Node
**Base class:** `Node`

Queries a vector index for the `top_k` chunks most similar to the query. Reads the
index from `index_key` and the query from `query_key` (text string or pre-computed
vector). Routes `no_results` when the index is empty or the similarity threshold is
not met.

| Property | Default | Description |
|---|---|---|
| `index_key` | `vector_index` | Shared-store key for the vector index |
| `query_key` | `query` | Shared-store key for the query text or vector |
| `top_k` | `5` | Number of nearest neighbours to return |
| `output_key` | `retrieved_docs` | Shared-store key for the results list |

---

## Database / SQL

### DB Schema Node
**Base class:** `Node`

Inspects a database and generates a human-readable schema description. Reads the
connection string (DSN or SQLAlchemy URL) from `connection_key` and writes a
compact table/column description to `output_key`. Feed this into an NL to SQL Node
as context so the LLM knows the available tables and columns.

| Property | Default | Description |
|---|---|---|
| `connection_key` | `db_conn` | Shared-store key for the DB connection string |
| `output_key` | `db_schema` | Shared-store key for the schema description |

### NL to SQL Node
**Base class:** `Node`

Translates a natural-language question into a SQL query using an LLM. Reads the
schema from `schema_key` and the question from `question_key`; writes the generated
SQL to `output_key`. Wire to a SQL Execute Node to run the query and get results.
Supply a prompt file to control the system-level instructions and few-shot examples.

| Property | Default | Description |
|---|---|---|
| `model` | `gpt-4o` | LLM model name |
| `schema_key` | `db_schema` | Shared-store key for schema context |
| `question_key` | `nl_question` | Shared-store key for the natural-language question |
| `output_key` | `sql_query` | Shared-store key for the generated SQL |

### SQL Execute Node
**Base class:** `Node`

Executes a SQL statement against a database and writes the result rows to the
shared store. Reads the connection from `connection_key` and the query from
`sql_key`. Routes `error` on syntax errors or connection failures. The result is a
list of dicts, one per row.

| Property | Default | Description |
|---|---|---|
| `connection_key` | `db_conn` | Shared-store key for the DB connection string |
| `sql_key` | `sql_query` | Shared-store key for the SQL to execute |
| `output_key` | `query_results` | Shared-store key for the result rows |

---

## Voice / Audio

### Speech to Text Node
**Base class:** `Node`

Transcribes an audio file to text using an ASR model (default: Whisper). Reads
the audio file path from `audio_key` and writes the transcript to `output_key`.
Set `language` to a BCP-47 language code (e.g. `en`, `es`) for better accuracy;
leave empty for auto-detection. Routes `error` on file-not-found or API failure.

| Property | Default | Description |
|---|---|---|
| `model` | `whisper-1` | ASR model name |
| `audio_key` | `audio_path` | Shared-store key for the audio file path |
| `output_key` | `transcript` | Shared-store key for the transcript |
| `language` | _(empty)_ | ISO language code (empty = auto-detect) |

### Text to Speech Node
**Base class:** `Node`

Converts text to speech using a TTS model. Reads the input text from `text_key`,
synthesises audio with the chosen `voice`, and writes the output audio file path
to `output_key`. Pair with a Speech to Text Node for voice-in / voice-out pipelines.

| Property | Default | Description |
|---|---|---|
| `model` | `tts-1` | TTS model name |
| `voice` | `alloy` | Voice identifier |
| `text_key` | `tts_text` | Shared-store key for the input text |
| `output_key` | `audio_path` | Shared-store key for the output audio file path |

---

## Document / Vision

### PDF Extract Node
**Base class:** `Node`

Extracts plain text from a PDF file. Reads the file path from `pdf_key`. Set `pages`
to a range like `"1-5"` to extract only specific pages; leave empty to extract all
pages. Writes the combined extracted text to `output_key`. Pair with a Text Chunk
Node and Vector Index Node for PDF-based RAG.

| Property | Default | Description |
|---|---|---|
| `pdf_key` | `pdf_path` | Shared-store key for the PDF file path |
| `output_key` | `pdf_text` | Shared-store key for the extracted text |
| `pages` | _(empty)_ | Page range, e.g. `1-5` (empty = all pages) |

### Image Vision Node
**Base class:** `Node`

Sends an image to a vision-capable LLM and returns a description or analysis.
Reads the image path or URL from `image_key`. Supply a prompt file to ask specific
questions about the image (e.g. "List all text visible in this image" or "Describe
the chart"). Writes the model response to `output_key`.

| Property | Default | Description |
|---|---|---|
| `model` | `gpt-4o` | Vision-capable LLM model name |
| `image_key` | `image_path` | Shared-store key for image path or URL |
| `output_key` | `vision_result` | Shared-store key for the description/analysis |

### Data Validate Node
**Base class:** `Node`

Validates data in the shared store against a JSON Schema. Reads the data from
`input_key` and the schema from `schema_key`. Routes `valid` if validation passes,
`invalid` otherwise, and writes the list of validation error messages to
`errors_key` for downstream error-handling or human review.

| Property | Default | Description |
|---|---|---|
| `input_key` | `data` | Shared-store key for the data to validate |
| `schema_key` | `validation_schema` | Shared-store key for the JSON Schema |
| `errors_key` | `validation_errors` | Shared-store key for the error list |

---

## Code / Execution

### Code Gen Node
**Base class:** `Node`

Generates source code from a specification using an LLM. Reads the spec from
`spec_key`, writes the generated code to `output_key`. Set `language` to control
the target (Python, JavaScript, SQL, etc.). Supply a prompt file to give the model
style guidelines, import conventions, or a partial code template to fill in.

| Property | Default | Description |
|---|---|---|
| `model` | `gpt-4o` | LLM model name |
| `language` | `python` | Target programming language |
| `spec_key` | `code_spec` | Shared-store key for the code specification |
| `output_key` | `generated_code` | Shared-store key for the generated code |

### Code Exec Node
**Base class:** `Node`

Executes Python code from the shared store in a subprocess. Reads code from
`code_key`, runs it with a `timeout` second limit, and writes stdout/result to
`output_key`. Enable `sandbox` to run in a restricted subprocess with limited
imports. Routes `error` on non-zero exit code or timeout. Use after Code Gen Node
for a generate → execute → verify pattern.

| Property | Default | Description |
|---|---|---|
| `code_key` | `generated_code` | Shared-store key for code to execute |
| `sandbox` | `true` | Run in restricted subprocess |
| `timeout` | `30` | Execution timeout in seconds |
| `output_key` | `exec_output` | Shared-store key for stdout/result |

### Test Gen Node
**Base class:** `Node`

Generates test code for existing source code using an LLM. Reads source from
`code_key` and writes test code to `output_key`. Pair with Code Exec Node to run
the generated tests immediately and Judge Node to score their quality. Supports
`pytest` and `unittest` framework conventions.

| Property | Default | Description |
|---|---|---|
| `model` | `gpt-4o` | LLM model name |
| `code_key` | `generated_code` | Shared-store key for the source code |
| `output_key` | `test_code` | Shared-store key for generated test code |
| `framework` | `pytest` | Test framework: `pytest` or `unittest` |

---

## Data Processing

### Map Node
**Base class:** `Node`

Applies a Python expression to every item in a list. Reads the list from
`input_key`, evaluates `transform` with the current item bound to the name `item`,
and writes the transformed list to `output_key`. Use for lightweight per-item
transformations that do not require LLM calls. For LLM-per-item work use Batch Node
or Async Parallel Batch Node instead.

| Property | Default | Description |
|---|---|---|
| `input_key` | `items` | Shared-store key for the input list |
| `output_key` | `mapped_items` | Shared-store key for the output list |
| `transform` | _(empty)_ | Python expression applied to each item (`item` variable) |

### Reduce Node
**Base class:** `Node`

Folds a list down to a single value. Reads the list from `input_key`, applies the
`reducer` function, and writes the result to `output_key`. Built-in reducers:
`sum`, `concat` (join strings), `max`, `min`. Or supply a Python expression using
`acc` (accumulator) and `item` variables. Use after a Map Node or Batch Node to
aggregate results.

| Property | Default | Description |
|---|---|---|
| `input_key` | `mapped_items` | Shared-store key for the input list |
| `output_key` | `reduced_result` | Shared-store key for the reduced value |
| `reducer` | `sum` | Built-in name or Python expression |

### Condition Node
**Base class:** `Node`

Evaluates a Python expression and routes to `true` or `false`. The expression has
access to the shared store via the name `store`. Use this for simple boolean gates
(e.g. `"store['score'] > 0.8"` or `"len(store['results']) == 0"`). For complex
multi-way routing use Router Node instead.

| Property | Default | Description |
|---|---|---|
| `expression` | _(empty)_ | Python expression (accesses shared store as `store`) |

### Loop Counter Node
**Base class:** `Node`

Implements a fixed-count loop by tracking an iteration counter in the shared store.
Routes `continue` until `max_iterations` is reached, then routes `done`. Wire
`continue` to the loop body and back to this node; wire `done` to the exit node.
Declare `counter_key` to give the iteration number a named slot in the store.

| Property | Default | Description |
|---|---|---|
| `max_iterations` | `10` | Maximum loop iterations |
| `counter_key` | `loop_count` | Shared-store key for the iteration counter |

### Transform Node
**Base class:** `Node`

Reshapes or reformats a single value using a Jinja2 template or Python expression.
Reads from `input_key`, applies the `template`, and writes to `output_key`. Use for
struct reshaping (dict → list), format conversions (ISO date → human-readable),
or any mapping that does not require a loop or LLM call.

| Property | Default | Description |
|---|---|---|
| `input_key` | `data` | Shared-store key for input data |
| `output_key` | `transformed_data` | Shared-store key for output data |
| `template` | _(empty)_ | Jinja2 template or Python expression |

### Merge Node
**Base class:** `Node`

Combines values from several shared-store keys into a single value. Reads the keys
listed in `input_keys` (comma-separated) and writes a merged result to `output_key`.
Choose a `strategy`: `dict_update` merges dicts left-to-right, `list_concat`
concatenates lists, `string_join` joins strings with a newline. Use at the end of a
parallel fan-out to recombine results.

| Property | Default | Description |
|---|---|---|
| `input_keys` | _(empty)_ | Comma-separated list of shared-store keys to merge |
| `output_key` | `merged_data` | Shared-store key for the merged result |
| `strategy` | `dict_update` | Merge strategy: `dict_update`, `list_concat`, `string_join` |

---

## Calendar

### Calendar Read Node
**Base class:** `Node`

Reads events from a Google Calendar (or compatible CalDAV calendar). Reads a time
range dict (`{"start": ..., "end": ...}`) from `time_range_key` and writes the list
of event dicts to `output_key`. Requires OAuth credentials to be set up in the
runtime environment. Routes `error` on authentication or API failure.

| Property | Default | Description |
|---|---|---|
| `calendar_id` | `primary` | Calendar ID or `primary` |
| `time_range_key` | `time_range` | Shared-store key for the time range dict |
| `output_key` | `calendar_events` | Shared-store key for the events list |

### Calendar Write Node
**Base class:** `Node`

Creates an event in a Google Calendar. Reads event data (title, start, end,
description, attendees) from the dict at `event_key` and writes the new event's ID
to `output_key`. Pair with Calendar Read Node to implement scheduling workflows
that check for conflicts before booking.

| Property | Default | Description |
|---|---|---|
| `calendar_id` | `primary` | Calendar ID or `primary` |
| `event_key` | `new_event` | Shared-store key for the event data dict |
| `output_key` | `created_event_id` | Shared-store key for the created event ID |

---

## MCP / Agent Protocol

### MCP Tool Node
**Base class:** `Node`

Calls a tool on an MCP (Model Context Protocol) server. Reads the tool arguments
from `args_key` and writes the tool's return value to `output_key`. Set `server_url`
and `tool_name` in the Inspector. Use to integrate any MCP-compatible tool server
(file systems, databases, browser automation, custom tools) into a flow without
writing HTTP boilerplate.

| Property | Default | Description |
|---|---|---|
| `server_url` | _(empty)_ | MCP server URL |
| `tool_name` | _(empty)_ | Tool name to invoke on the server |
| `args_key` | `tool_args` | Shared-store key for the tool arguments dict |
| `output_key` | `tool_result` | Shared-store key for the tool result |

### A2A Send Node
**Base class:** `Node`

Sends a message to another agent via the Agent-to-Agent (A2A) protocol. Reads the
outgoing message from `message_key` and posts it to the target agent's A2A endpoint.
Writes the server's acknowledgement to `output_key`. Use to build multi-agent systems
where specialised agents hand off tasks to each other.

| Property | Default | Description |
|---|---|---|
| `target_agent_url` | _(empty)_ | Target agent's A2A endpoint URL |
| `message_key` | `outgoing_message` | Shared-store key for the message to send |
| `output_key` | `send_response` | Shared-store key for the acknowledgement |

### A2A Receive Node
**Base class:** `Node`

Waits for an incoming A2A message and writes it to the shared store. Polls
`listen_key` (where the runtime places incoming messages) until a message arrives or
`timeout` seconds elapse. Routes `timeout` if no message is received; routes
`default` when a message arrives and is written to `output_key`.

| Property | Default | Description |
|---|---|---|
| `listen_key` | `a2a_inbox` | Shared-store key where incoming messages are placed |
| `timeout` | `30` | Wait timeout in seconds |
| `output_key` | `received_message` | Shared-store key for the received message |

---

## Observability / Utility

### Log Node
**Base class:** `Node`

Emits a structured log entry at the configured log level. `message_template`
supports `{{key}}` interpolation from the shared store. Optionally lists specific
shared-store key names in `keys_to_log` to append their values to the entry.
Always routes `default`. Use for debugging, audit trails, and pipeline telemetry.

| Property | Default | Description |
|---|---|---|
| `message_template` | _(empty)_ | Log message template (`{{key}}` interpolation) |
| `level` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `keys_to_log` | _(empty)_ | Comma-separated shared-store keys to include |

### Timer Node
**Base class:** `Node`

Measures elapsed wall-clock time between two points in a flow. Set `mode = start`
at the beginning of a section to record a timestamp, and `mode = stop` at the end
to write elapsed milliseconds to `output_key`. Use `label` to distinguish multiple
concurrent timers. Useful for performance profiling and SLA monitoring.

| Property | Default | Description |
|---|---|---|
| `label` | `timer` | Label for the timing measurement |
| `mode` | `start` | Operation: `start` or `stop` |
| `output_key` | `elapsed_ms` | Shared-store key for elapsed milliseconds (stop mode) |

### Cache Node
**Base class:** `Node`

Provides a simple key-value cache backed by the shared store. On first access
(`miss`) the flow continues to compute the value; on a repeat access (`hit`) the
cached value is returned without re-running the expensive downstream nodes. Build
the cache key from shared-store values using `{{key}}` interpolation in
`cache_key_template`. Set `ttl = 0` for no expiry.

| Property | Default | Description |
|---|---|---|
| `cache_key_template` | _(empty)_ | Template for the cache lookup key |
| `value_key` | `cache_value` | Shared-store key for the cached/to-cache value |
| `ttl` | `300` | Cache TTL in seconds (0 = no expiry) |

### Trace Node
**Base class:** `Node`

Emits an OpenTelemetry span around the current flow step. Set `span_name` to label
the span. List shared-store keys in `keys_to_trace` to attach their values as span
attributes. Wrap a sub-section of a flow with matching Trace Nodes (start/end) to
get fine-grained distributed tracing without modifying application code. Always
routes `default`.

| Property | Default | Description |
|---|---|---|
| `span_name` | _(empty)_ | OpenTelemetry span name |
| `keys_to_trace` | _(empty)_ | Comma-separated shared-store keys to attach as attributes |

---

## Data Structures / Memory

### Registry Node
**Base class:** `Node`

Provides named-entry storage backed by a dict in the shared store. Supports `get`,
`set`, `delete`, and `list` operations on `registry_key`. Routes `found` / `not_found`
on a `get` that finds or misses the entry. Use for configuration look-ups, object
registries, and any pattern where you need to name-and-retrieve arbitrary values.

| Property | Default | Description |
|---|---|---|
| `operation` | `get` | Operation: `get`, `set`, `delete`, `list` |
| `registry_key` | `registry` | Shared-store key for the registry dict |
| `entry_name` | _(empty)_ | Name of the entry to get/set/delete |
| `value_key` | `registry_value` | Shared-store key for the value to set or retrieved |

### Stack Push Node
**Base class:** `Node`

Pushes a value onto a list in the shared store, treating it as a LIFO stack. Reads
the value from `value_key` and appends it to the end of the list at `stack_key`
(creating the list if absent). Pair with Stack Pop Node to implement depth-first
traversal, undo stacks, or backtracking patterns.

| Property | Default | Description |
|---|---|---|
| `stack_key` | `stack` | Shared-store key for the stack list |
| `value_key` | `push_value` | Shared-store key for the value to push |

### Stack Pop Node
**Base class:** `Node`

Pops the top item from a LIFO stack list in the shared store. Reads the list at
`stack_key`, removes and returns the last element, and writes it to `output_key`.
Routes `empty` if the list is empty or absent, allowing the flow to detect
stack-underflow without crashing.

| Property | Default | Description |
|---|---|---|
| `stack_key` | `stack` | Shared-store key for the stack list |
| `output_key` | `popped_value` | Shared-store key for the popped value |

### Queue Enqueue Node
**Base class:** `Node`

Appends a value to the tail of a FIFO queue list in the shared store. Reads the
value from `value_key` and appends it to the end of the list at `queue_key`. Pair
with Queue Dequeue Node to implement first-in-first-out work queues, breadth-first
traversal, or any ordered producer/consumer pattern.

| Property | Default | Description |
|---|---|---|
| `queue_key` | `queue` | Shared-store key for the queue list |
| `value_key` | `enqueue_value` | Shared-store key for the value to enqueue |

### Queue Dequeue Node
**Base class:** `Node`

Removes and returns the head item from a FIFO queue list in the shared store. Reads
the list at `queue_key`, removes the first element, and writes it to `output_key`.
Routes `empty` if the queue is empty or absent. Use with Queue Enqueue Node for
producer/consumer patterns and breadth-first graph traversal.

| Property | Default | Description |
|---|---|---|
| `queue_key` | `queue` | Shared-store key for the queue list |
| `output_key` | `dequeued_value` | Shared-store key for the dequeued value |

### Local Memory Node
**Base class:** `Node`

Provides persistent slot-based memory backed by a dict in the shared store. Supports
`store` (write to a named slot), `recall` (read from a slot), and `clear` (delete a
slot or all slots) operations. Use for conversational memory, per-session state, or
any pattern that needs to remember a value across multiple flow runs within a session.

| Property | Default | Description |
|---|---|---|
| `operation` | `store` | Operation: `store`, `recall`, `clear` |
| `memory_key` | `local_memory` | Shared-store key for the memory dict |
| `slot` | _(empty)_ | Memory slot name |
| `value_key` | `memory_value` | Shared-store key for the value to store or retrieved |

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
| JSON LLM Node | `Node` | LLM call — structured JSON output |
| Classifier Node | `Node` | LLM-based label classification |
| Agent Node | `Node` | Autonomous tool-calling loop |
| RAG Node | `Node` | Embedding and retrieval |
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
| Chain of Thought Node | `Node` | Step-by-step LLM reasoning |
| Majority Vote Node | `Node` | Self-consistency via sampling |
| Supervisor Node | `Node` | Multi-agent orchestration |
| Debate Advocate Node | `Node` | Adversarial argument generation |
| Debate Judge Node | `Node` | Adversarial debate decision |
| Web Search Node | `Node` | Live web search |
| Web Scrape Node | `Node` | HTML → plain text extraction |
| API Call Node | `Node` | HTTP REST call |
| Text Chunk Node | `Node` | Long text → chunk list |
| Embed Node | `Node` | Text → embedding vector |
| Vector Index Node | `Node` | Build vector store index |
| Vector Retrieve Node | `Node` | Query vector store |
| DB Schema Node | `Node` | Inspect DB schema |
| NL to SQL Node | `Node` | Natural language → SQL |
| SQL Execute Node | `Node` | Run SQL query |
| Speech to Text Node | `Node` | Audio → transcript |
| Text to Speech Node | `Node` | Text → audio file |
| PDF Extract Node | `Node` | PDF → plain text |
| Image Vision Node | `Node` | Image → LLM description |
| Data Validate Node | `Node` | JSON Schema validation |
| Code Gen Node | `Node` | LLM code generation |
| Code Exec Node | `Node` | Execute code in subprocess |
| Test Gen Node | `Node` | LLM test generation |
| Map Node | `Node` | Apply expression to each item |
| Reduce Node | `Node` | Fold list to single value |
| Condition Node | `Node` | Boolean expression gate |
| Loop Counter Node | `Node` | Fixed-count loop |
| Transform Node | `Node` | Reshape / reformat data |
| Merge Node | `Node` | Combine multiple store keys |
| Calendar Read Node | `Node` | Read calendar events |
| Calendar Write Node | `Node` | Create calendar event |
| MCP Tool Node | `Node` | MCP server tool call |
| A2A Send Node | `Node` | Agent-to-agent message send |
| A2A Receive Node | `Node` | Agent-to-agent message receive |
| Log Node | `Node` | Structured log emission |
| Timer Node | `Node` | Elapsed time measurement |
| Cache Node | `Node` | Key-value cache with TTL |
| Trace Node | `Node` | OpenTelemetry span emission |
| Registry Node | `Node` | Named-entry object store |
| Stack Push Node | `Node` | LIFO stack push |
| Stack Pop Node | `Node` | LIFO stack pop |
| Queue Enqueue Node | `Node` | FIFO queue enqueue |
| Queue Dequeue Node | `Node` | FIFO queue dequeue |
| Local Memory Node | `Node` | Slot-based session memory |
| Shell Command Node | `Node` | Execute bash/sh/zsh/powershell/cmd |
| TTY Serial Node | `Node` | Serial port / Arduino / MCU I/O |
| Spreadsheet Node | `Node` | Read/write CSV, TSV, Excel |
| Socket Node | `Node` | TCP/UDP socket I/O |
| WebSocket Node | `AsyncNode` | Async WebSocket client |
| Webhook Trigger Node | `Node` | Wait for incoming HTTP POST |
| Context Compact Node | `Node` | Compact LLM context (strategy pattern) |
| Conversation History Node | `Node` | Manage multi-turn message list |
| Regex Node | `Node` | Pattern match / extract / replace |
| Template Render Node | `Node` | Jinja2 template rendering |
| JSON Parse Node | `Node` | Parse / serialize JSON |
| List Operations Node | `Node` | Filter / sort / slice / unique list |
| String Operations Node | `Node` | Split / join / strip / replace string |
| Retry Node | `Node` | Retry with exponential backoff |
| Rate Limiter Node | `Node` | Throttle call rate |
| Email Send Node | `Node` | Send email (SMTP / SendGrid) |
| Email Read Node | `Node` | Fetch email from IMAP |
| Notification Node | `Node` | Slack / Discord / Teams / Telegram |
| Secret Node | `Node` | Read secret from env / vault |

---

## System / Shell / Hardware

### Shell Command Node
**Base class:** `Node`

Executes a shell command string in a subprocess. The `shell` property selects the
interpreter: `auto` detects the platform (bash on Linux, zsh on macOS, PowerShell on
Windows), or you can pin to `bash`, `sh`, `zsh`, `powershell`, or `cmd`. Reads the
command from `command_key`, writes stdout and stderr to separate keys, and routes
`error` on non-zero exit code.

| Property | Default | Description |
|---|---|---|
| `shell` | `auto` | Shell interpreter: `auto`, `bash`, `sh`, `zsh`, `powershell`, `cmd` |
| `command_key` | `command` | Shared-store key for the command string |
| `timeout` | `30` | Execution timeout in seconds |
| `stdout_key` | `stdout` | Shared-store key for captured stdout |
| `stderr_key` | `stderr` | Shared-store key for captured stderr |
| `env_key` | _(empty)_ | Shared-store key for extra environment variables dict |

### TTY Serial Node
**Base class:** `Node`

Reads or writes data over a serial (TTY/COM) port. Use for Arduino, Raspberry Pi,
microcontrollers, instruments, and any device that communicates over a serial
connection. The port path lives in the shared store so it can be configured at
runtime. `operation: open` and `close` manage the connection; `readline` reads until
a newline (most MCU sketches send newline-terminated sensor data); `read` reads up to
a buffer; `write` sends data. Routes `timeout` on read timeout, `error` on port failure.

| Property | Default | Description |
|---|---|---|
| `operation` | `readline` | Operation: `open`, `close`, `read`, `readline`, `write` |
| `port_key` | `serial_port` | Shared-store key for port path (`/dev/ttyUSB0`, `COM3`, `/dev/tty.usbmodem1`) |
| `baud_rate` | `9600` | Serial baud rate |
| `timeout` | `1.0` | Read timeout in seconds (0 = non-blocking) |
| `encoding` | `utf-8` | Decode encoding: `utf-8`, `ascii`, `bytes` (raw bytearray) |
| `data_key` | `serial_data` | Shared-store key for data to write (`write` operation) |
| `output_key` | `serial_read` | Shared-store key for received data (`read`/`readline`) |

### Spreadsheet Node
**Base class:** `Node`

Reads or writes tabular data in CSV, TSV, or Excel (`.xlsx`/`.xls`) format. `format:
auto` detects the format from the file extension. Supports configurable delimiters and
four quoting styles that map directly to Python's `csv.QUOTE_*` constants. For Excel,
`sheet_name` selects the worksheet. Reads produce a list of dicts (header mode) or a
list of lists (no-header mode), which feeds naturally into Map Node, Reduce Node, or
any LLM Batch Node.

| Property | Default | Description |
|---|---|---|
| `operation` | `read` | Operation: `read`, `write`, `append` |
| `file_key` | `file_path` | Shared-store key for the file path |
| `format` | `auto` | Format: `auto` (from extension), `csv`, `tsv`, `excel` |
| `delimiter` | `,` | Field delimiter (CSV/TSV only) |
| `quoting` | `minimal` | Quoting: `minimal`, `all`, `non_numeric`, `none` |
| `sheet_name` | `Sheet1` | Excel sheet name (Excel only) |
| `has_header` | `true` | Treat first row as column headers |
| `encoding` | `utf-8` | File encoding (CSV/TSV only) |
| `data_key` | `table_data` | Shared-store key for data to write |
| `output_key` | `table_data` | Shared-store key for read data |

---

## Networking / Sockets

### Socket Node
**Base class:** `Node`

Low-level TCP/UDP socket operations. The socket object is created on `connect` and
stored in the shared store under `socket_key` so subsequent Send/Receive/Close calls
in the same flow can share it. Use for custom protocols, legacy system integration,
instrument control, and any scenario where HTTP is not the right transport.

| Property | Default | Description |
|---|---|---|
| `operation` | `connect` | Operation: `connect`, `send`, `receive`, `close` |
| `host_key` | `socket_host` | Shared-store key for hostname or IP |
| `port_key` | `socket_port` | Shared-store key for port number |
| `proto` | `tcp` | Protocol: `tcp` or `udp` |
| `socket_key` | `socket` | Shared-store key holding the socket object between operations |
| `data_key` | `socket_data` | Shared-store key for data to send |
| `output_key` | `socket_recv` | Shared-store key for received data |
| `timeout` | `5.0` | Operation timeout in seconds |
| `buffer_size` | `4096` | Receive buffer size in bytes |

### WebSocket Node
**Base class:** `AsyncNode`

Async WebSocket client for `ws://` and `wss://` connections. Like Socket Node but
built on `asyncio` for non-blocking I/O — use this when you need streaming LLM
responses, live data feeds, or real-time agent-to-agent communication over WebSocket.
The connection object is stored in the shared store between operations.

| Property | Default | Description |
|---|---|---|
| `operation` | `connect` | Operation: `connect`, `send`, `receive`, `close` |
| `url_key` | `ws_url` | Shared-store key for the WebSocket URL (`ws://` or `wss://`) |
| `ws_key` | `ws_conn` | Shared-store key holding the WebSocket connection object |
| `data_key` | `ws_send` | Shared-store key for message to send |
| `output_key` | `ws_recv` | Shared-store key for received message |
| `timeout` | `10.0` | Receive timeout in seconds |

### Webhook Trigger Node
**Base class:** `Node`

Starts a lightweight HTTP server on the configured `port` and `path` and blocks until
a single incoming POST request arrives. Writes the request body to `output_key` and
headers to `headers_key`, then routes `triggered`. Routes `timeout` if no request
arrives within the configured window. Use as the entry node for event-driven flows —
CI/CD hooks, payment notifications, IoT push events, or any external system that calls
back into a flow.

| Property | Default | Description |
|---|---|---|
| `port` | `8080` | HTTP port to listen on |
| `path` | `/webhook` | URL path to listen on |
| `timeout` | `60` | Maximum seconds to wait for a POST request |
| `output_key` | `webhook_payload` | Shared-store key for the received request body |
| `headers_key` | `webhook_headers` | Shared-store key for the received request headers |

---

## AI / LLM Utilities

### Context Compact Node
**Base class:** `Node`

Reduces the size of a message list or text block before sending to an LLM, preventing
context window overflow. Uses a strategy pattern — swap the algorithm by changing the
`strategy` property without rewiring the graph.

| Strategy | Description |
|---|---|
| `truncate` | Keep the first or last N tokens; fast and deterministic |
| `sliding_window` | Keep the most recent N messages; preserves recency |
| `summarize` | LLM call that distills older content into a compact summary |
| `extractive` | Key-sentence extraction via TF-IDF / KeyBERT; no LLM needed |
| `semantic_dedup` | Embed all chunks and drop near-duplicates above a cosine threshold |

| Property | Default | Description |
|---|---|---|
| `strategy` | `sliding_window` | Compaction algorithm (see table above) |
| `input_key` | `messages` | Shared-store key for the message list or text to compact |
| `output_key` | `messages` | Shared-store key to write the compacted result |
| `max_tokens` | `2000` | Target maximum tokens after compaction |
| `model` | _(empty)_ | LLM model for `summarize` strategy (empty = project default) |
| `similarity_threshold` | `0.92` | Cosine similarity cutoff for `semantic_dedup` |

### Conversation History Node
**Base class:** `Node`

Manages a `messages` list (role + content dicts) in the shared store for multi-turn
chat flows. Supports four operations: `append` adds a new message with the specified
role; `trim` enforces a maximum message count; `clear` resets the list; `format`
renders the list to a plain string for LLM APIs that take a single prompt rather than
a message list.

| Property | Default | Description |
|---|---|---|
| `operation` | `append` | Operation: `append`, `trim`, `clear`, `format` |
| `history_key` | `messages` | Shared-store key for the message list |
| `role` | `user` | Role for `append`: `user`, `assistant`, `system` |
| `content_key` | `content` | Shared-store key for the message content to append |
| `max_messages` | `20` | Maximum messages to keep on `trim` |
| `output_key` | `chat_str` | Shared-store key for formatted string output (`format` operation) |

---

## Text / Data Processing

### Regex Node
**Base class:** `Node`

Applies a regular expression to a string in the shared store. `findall` returns a
list of all matches. `match` / `search` return the first match object and route
`matched` or `no_match`. `replace` returns the substituted string. `split` returns
a list of segments. All results are written to `output_key`.

| Property | Default | Description |
|---|---|---|
| `operation` | `findall` | Operation: `match`, `search`, `findall`, `replace`, `split` |
| `pattern` | _(empty)_ | Regular expression pattern string |
| `flags` | _(empty)_ | Regex flags: `i` (ignore case), `m` (multiline), `s` (dot-all) |
| `input_key` | `text` | Shared-store key for the input string |
| `replacement` | _(empty)_ | Replacement string for `replace` (supports `\1` groups) |
| `output_key` | `regex_result` | Shared-store key for the result |

### Template Render Node
**Base class:** `Node`

Renders a Jinja2 template using shared store values as context. Set `template_type =
string` for an inline template; set `template_type = path` and provide a path to a
`.j2` or `.md` file for larger templates. Every key in the shared store is available
as a template variable. Use for generating prompts, reports, emails, and any text
that varies by run-time data.

| Property | Default | Description |
|---|---|---|
| `template_type` | `string` | Template source: `string` (inline) or `path` (file) |
| `template` | _(empty)_ | Inline Jinja2 template or path to `.j2`/`.md` file |
| `output_key` | `rendered` | Shared-store key to write the rendered string |

### JSON Parse Node
**Base class:** `Node`

Parses a JSON string to a Python dict/list, or serializes a dict/list back to a JSON
string. Routes `error` on malformed input. Use after API Call Node (response body is
a JSON string) or before a node that needs a structured object. `indent > 0` produces
pretty-printed output; `indent = 0` produces compact output.

| Property | Default | Description |
|---|---|---|
| `operation` | `parse` | Operation: `parse` (string→dict) or `serialize` (dict→string) |
| `input_key` | `json_str` | Shared-store key for JSON string (parse) or object (serialize) |
| `output_key` | `json_obj` | Shared-store key for the result |
| `indent` | `0` | JSON indentation for `serialize` (0 = compact) |

### List Operations Node
**Base class:** `Node`

Performs collection operations on a list in the shared store. `filter` and `sort`
accept a Python expression with an `item` variable. `slice` uses `start`/`stop`
indices. `unique` removes duplicates (preserves order). `flatten` unpacks nested lists
one level deep. `reverse` reverses in place. `count` writes the list length to
`output_key`. Routes `empty` when the result is an empty list.

| Property | Default | Description |
|---|---|---|
| `operation` | `filter` | Operation: `filter`, `sort`, `slice`, `unique`, `flatten`, `reverse`, `count` |
| `input_key` | `items` | Shared-store key for the input list |
| `output_key` | `items` | Shared-store key for the result |
| `expression` | _(empty)_ | Python expression for `filter`/`sort` (`item` variable) |
| `start` | `0` | Start index for `slice` |
| `stop` | `-1` | Stop index for `slice` (-1 = end) |

### String Operations Node
**Base class:** `Node`

Applies string transformations to a value in the shared store. All operations read
from `input_key` and write to `output_key`. `split` produces a list; `join` expects
a list as input and produces a string. `format` uses `{key}` placeholders resolved
from the shared store. `truncate` appends `…` if the string exceeds `max_length`.

| Property | Default | Description |
|---|---|---|
| `operation` | `strip` | Operation: `split`, `join`, `strip`, `upper`, `lower`, `replace`, `format`, `truncate` |
| `input_key` | `text` | Shared-store key for the input string (or list for `join`) |
| `output_key` | `text` | Shared-store key for the result |
| `separator` | ` ` | Separator for `split` and `join` |
| `find` | _(empty)_ | Find string for `replace` |
| `replacement` | _(empty)_ | Replacement string for `replace` |
| `max_length` | `200` | Maximum length for `truncate` |
| `template` | _(empty)_ | Format template string (`{key}` placeholders) for `format` |

---

## Resilience / Flow Utilities

### Retry Node
**Base class:** `Node`

Implements retry-with-exponential-backoff for a section of the flow. Place this node
before the operation that might fail; wire its `retry` action back to the start of the
fallible section and its `done` action to the success path. The node reads a status
key to decide whether to retry or declare success; `status_key = "ok"` signals done.
Routes `give_up` when `max_attempts` is exhausted.

| Property | Default | Description |
|---|---|---|
| `max_attempts` | `3` | Maximum retry attempts before routing `give_up` |
| `backoff_base` | `1.0` | Base delay in seconds (doubles each retry) |
| `jitter` | `true` | Add random jitter to backoff delay |
| `attempt_key` | `retry_attempt` | Shared-store key for the current attempt counter |
| `status_key` | `retry_status` | Shared-store key read to decide `retry` vs `done` (`ok` = done) |

### Rate Limiter Node
**Base class:** `Node`

Enforces a per-minute rate limit by sleeping between calls when the last call was too
recent. Reads a timestamp from `timestamp_key`, computes the required sleep duration,
and writes the updated timestamp before routing `default`. Use `label` to maintain
independent rate limiters for different API endpoints in the same flow.

| Property | Default | Description |
|---|---|---|
| `calls_per_min` | `60` | Maximum calls allowed per minute |
| `timestamp_key` | `last_call_time` | Shared-store key for the last-call Unix timestamp |
| `label` | `default` | Rate limiter label (allows multiple independent limiters) |

---

## Messaging / Notifications

### Email Send Node
**Base class:** `Node`

Sends an email via SMTP or a transactional email API (SendGrid, Mailgun). Reads
subject, body, and recipients from the shared store. Set `html = true` to send HTML
email. The `output_key` receives the server's message ID or delivery receipt on
`sent`, or an error description on `error`.

| Property | Default | Description |
|---|---|---|
| `provider` | `smtp` | Email provider: `smtp`, `sendgrid`, `mailgun` |
| `to_key` | `email_to` | Shared-store key for recipient address(es) (string or list) |
| `subject_key` | `email_subject` | Shared-store key for the email subject |
| `body_key` | `email_body` | Shared-store key for the email body (plain text or HTML) |
| `html` | `false` | Treat body as HTML |
| `output_key` | `email_result` | Shared-store key for send result / message ID |

### Email Read Node
**Base class:** `Node`

Fetches emails from an IMAP mailbox (or Gmail via Gmail API) and writes a list of
message dicts to the shared store. Each dict contains `subject`, `from`, `body`,
`date`, and `message_id` fields. Routes `no_mail` when the inbox is empty. Use to
build flows that process inbound email — automated replies, ticket routing, data
extraction from email reports.

| Property | Default | Description |
|---|---|---|
| `provider` | `imap` | Mail provider: `imap`, `gmail` |
| `folder` | `INBOX` | Mailbox folder to check |
| `max_messages` | `10` | Maximum messages to fetch |
| `unread_only` | `true` | Fetch only unread messages |
| `output_key` | `emails` | Shared-store key for the list of message dicts |

### Notification Node
**Base class:** `Node`

Sends a notification to a messaging platform via webhook. Supports Slack (Incoming
Webhooks), Discord (Webhook URLs), Microsoft Teams (Connector cards), and Telegram
(Bot API). Reads the platform webhook URL from the shared store. Set `title` for
platforms that support rich message formatting (Slack blocks, Teams cards).

| Property | Default | Description |
|---|---|---|
| `channel` | `slack` | Platform: `slack`, `discord`, `teams`, `telegram` |
| `webhook_url_key` | `webhook_url` | Shared-store key for the platform webhook URL |
| `message_key` | `notification` | Shared-store key for the message text |
| `title` | _(empty)_ | Optional title / header for rich message formats |

---

## Security / Configuration

### Secret Node
**Base class:** `Node`

Reads a secret or configuration value from an environment variable, `.env` file,
AWS Secrets Manager, or HashiCorp Vault, and writes it to the shared store. Use this
at the start of a flow to load credentials that should not be hard-coded in the
Inspector or exported code. Routes `not_found` when `required = true` and the secret
is missing; writes `None` when `required = false`.

| Property | Default | Description |
|---|---|---|
| `source` | `env` | Secret source: `env`, `dotenv`, `aws_secrets`, `vault` |
| `secret_name` | _(empty)_ | Environment variable name or secret path/name |
| `output_key` | `secret` | Shared-store key to write the retrieved secret value |
| `required` | `true` | Route `not_found` when missing; write `None` when false |

---

## Addon Nodes — Geospatial

> Addon nodes ship in `addon_nodes/` and appear under the **Scientific & Engineering**
> divider in the palette. Install them via **Tools → Node Type Library** if they are not
> already visible.

### USGS Elevation Point Node
**Base class:** `Node` · **Actions:** `default`, `error`

Returns ground elevation (metres or feet) for a single latitude/longitude point via the
USGS Elevation Point Query Service (EPQS). No API key required.

| Property | Default | Description |
|---|---|---|
| `lat_key` | `lat` | Shared-store key holding latitude (decimal degrees) |
| `lon_key` | `lon` | Shared-store key holding longitude (decimal degrees) |
| `units` | `Meters` | Elevation units: `Meters` or `Feet` |
| `result_key` | `elevation_result` | Key to write the result dict (`lat`, `lon`, `elevation`, `units`) |

### USGS 3DEP Elevation Node
**Base class:** `Node` · **Actions:** `default`, `error`

Downloads a 3DEP Digital Elevation Model raster for a bounding box via the USGS WCS
service and saves it as a GeoTIFF. Resolutions: 1/3, 1, or 2 arc-second.

| Property | Default | Description |
|---|---|---|
| `bbox_key` | `bbox` | Key holding `[west, south, east, north]` in decimal degrees |
| `resolution` | `1/3` | DEM resolution: `1/3`, `1`, or `2` arc-second |
| `output_dir_key` | `dem_output_dir` | Key holding the output directory path |
| `result_key` | `dem_result` | Key for result dict (`output_path`, `crs`, `bbox`) |

### National Map Download Node
**Base class:** `Node` · **Actions:** `default`, `error`

Searches The National Map (TNM) API for available USGS datasets within a bounding box.
Can optionally download the discovered files. Supports NED, NHD, NAIP, Topo, and more.

| Property | Default | Description |
|---|---|---|
| `bbox_key` | `bbox` | Key holding `[west, south, east, north]` |
| `dataset` | `National Elevation Dataset (NED) 1/3 arc-second` | TNM dataset product type |
| `max_items` | `10` | Maximum dataset records to return |
| `download` | `false` | If `true`, download files to `output_dir_key` |
| `output_dir_key` | `tnm_output_dir` | Directory for downloaded files |
| `result_key` | `tnm_result` | Key for result dict (`items` list, each with `title`, `downloadURL`, `sizeInBytes`) |

### Earthquake Catalog Node
**Base class:** `Node` · **Actions:** `default`, `error`

Fetches earthquake events from the USGS FDSN/ComCat API filtered by bounding box, time
range, and minimum magnitude. Returns a list of event dicts. No API key required.

| Property | Default | Description |
|---|---|---|
| `bbox_key` | `bbox` | Key holding `[west, south, east, north]` |
| `start_time` | `2024-01-01` | Start date (YYYY-MM-DD) |
| `end_time` | _(empty = now)_ | End date; leave blank for the current time |
| `min_mag` | `2.5` | Minimum earthquake magnitude |
| `max_results` | `100` | Maximum events to return |
| `result_key` | `eq_events` | Key for list of event dicts (`magnitude`, `depth_km`, `time`, `place`, `id`) |

### Landsat Search & Download Node
**Base class:** `Node` · **Actions:** `default`, `error`

Searches and optionally downloads Landsat Collection 2 Level-2 scenes from the USGS M2M
API. Requires a free USGS EarthExplorer account.

| Property | Default | Description |
|---|---|---|
| `username_key` | `usgs_username` | Key holding USGS EarthExplorer username |
| `token_key` | `usgs_token` | Key holding USGS API token |
| `bbox_key` | `bbox` | Key holding `[west, south, east, north]` |
| `dataset` | `landsat_ot_c2_l2` | Landsat dataset identifier |
| `start_date` | _(empty)_ | Search start date (YYYY-MM-DD) |
| `max_cloud_pct` | `20` | Maximum cloud cover percentage |
| `max_results` | `10` | Maximum scenes to return |
| `download` | `false` | If `true`, download scene data |
| `output_dir_key` | `landsat_output_dir` | Directory for downloaded scenes |
| `result_key` | `landsat_scenes` | Key for list of scene dicts |

### ShakeMap Fetch Node
**Base class:** `Node` · **Actions:** `default`, `error`

Downloads ShakeMap ground-motion products for a USGS earthquake event ID from
`earthquake.usgs.gov`. No API key required.

| Property | Default | Description |
|---|---|---|
| `event_id_key` | `eq_event_id` | Key holding the USGS event ID (e.g. `us7000n7n5`) |
| `product_type` | `download/grid.xml` | ShakeMap product to fetch |
| `output_dir_key` | `shakemap_output_dir` | Directory for downloaded files |
| `result_key` | `shakemap_fetch_result` | Key for result dict (`event_id`, `status`, `downloaded_files`) |

### ShakeMap Scenario Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs USGS ShakeMap v4 locally to generate a ground-motion scenario for a user-supplied
`event.xml` fault-rupture definition. Requires a local ShakeMap v4 installation.

| Property | Default | Description |
|---|---|---|
| `event_dir_key` | `shakemap_event_dir` | Key holding path to the event directory (contains `event.xml`) |
| `commands` | `assemble, model, contour` | Comma-separated ShakeMap pipeline steps |
| `result_key` | `shakemap_scenario_result` | Key for result dict (`status`, `grid_path`, `commands_run`) |

---

## Addon Nodes — Hydrology / Water

### USGS Water Data Node
**Base class:** `Node` · **Actions:** `default`, `error`

Fetches instantaneous or daily time-series data from the USGS National Water Information
System (NWIS) REST API for a specified gauge site and parameter. No API key required.

| Property | Default | Description |
|---|---|---|
| `site_key` | `usgs_site` | Key holding the USGS site number (e.g. `01638500`) |
| `param_cd` | `00060` | Parameter code: `00060` = discharge (cfs), `00065` = gage height (ft) |
| `period` | `P7D` | ISO 8601 period string (e.g. `P7D`, `P1Y`) |
| `stat_cd` | `00003` | Statistic code: `00003` = daily mean; blank = instantaneous |
| `result_key` | `water_data` | Key for result dict (`site_name`, `param_name`, `values` list) |

### NWIS Query Node
**Base class:** `Node` · **Actions:** `default`, `error`

Queries USGS NWIS in one of three modes: `site` (station metadata), `peak` (annual peak
flow record), or `stat` (long-term monthly statistics).

| Property | Default | Description |
|---|---|---|
| `query_type` | `site` | Query mode: `site`, `peak`, or `stat` |
| `site_key` | `usgs_site` | Key holding USGS site number |
| `state_cd` | _(empty)_ | Two-letter state code for `site` mode searches |
| `result_key` | `nwis_result` | Key for result dict (contents depend on `query_type`) |

### StreamStats Basin Node
**Base class:** `Node` · **Actions:** `default`, `error`

Delineates a watershed and computes basin characteristics (drainage area, mean elevation,
mean annual precipitation, etc.) via the USGS StreamStats REST API.

| Property | Default | Description |
|---|---|---|
| `lat_key` | `lat` | Key holding pour-point latitude |
| `lon_key` | `lon` | Key holding pour-point longitude |
| `state_cd` | `VA` | Two-letter US state code (upper-case) |
| `result_key` | `basin_result` | Key for result dict (`basin_characteristics` dict, `workspace_id`) |

### SWMM Run Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs an EPA SWMM 5 stormwater simulation from a `.inp` file. Returns peak conduit flows,
junction flooding volumes, and subcatchment runoff. Requires `swmm5` on the PATH.

| Property | Default | Description |
|---|---|---|
| `inp_path_key` | `swmm_inp_path` | Key holding path to the SWMM `.inp` file |
| `report_key` | `swmm_rpt_path` | Key holding path for the output `.rpt` report |
| `result_key` | `swmm_result` | Key for result dict (`conduit_peak_flows`, `junction_flooding`, `status`) |

### EPANET Run Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs an EPA EPANET 2 water distribution network simulation from a `.inp` file. Returns
nodal pressures (psi), pipe flows, and velocities. Requires EPANET installed.

| Property | Default | Description |
|---|---|---|
| `inp_path_key` | `epanet_inp_path` | Key holding path to the EPANET `.inp` file |
| `result_key` | `epanet_result` | Key for result dict (`node_pressures`, `pipe_flows`, `pipe_velocities`) |

### MODFLOW 6 Run Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs a USGS MODFLOW 6 groundwater simulation from a pre-configured simulation directory
containing `mfsim.nam`. Returns convergence status and head statistics. Requires `mf6`.

| Property | Default | Description |
|---|---|---|
| `sim_dir_key` | `mf6_sim_dir` | Key holding path to the MODFLOW 6 simulation directory |
| `result_key` | `mf6_result` | Key for result dict (`status`, `converged`, `iterations`, `head_stats`) |

### FloPy Model Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs a MODFLOW simulation managed by a FloPy `MFSimulation` (or `Modflow`) object that
you construct in Python and pass via the shared store. Returns head statistics.

| Property | Default | Description |
|---|---|---|
| `model_key` | `flopy_model` | Key holding a configured FloPy model/simulation instance |
| `exe_name` | `mf6` | MODFLOW executable name (`mf6`, `mf2005`, `mfnwt`, etc.) |
| `result_key` | `flopy_result` | Key for result dict (`success`, `head_stats`, head file path) |

### pyWatershed Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs a USGS National Hydrologic Model (NHM) simulation via the `pywatershed` Python
package. Returns streamflow and storage statistics for the simulated period.

| Property | Default | Description |
|---|---|---|
| `domain_dir_key` | `pws_domain_dir` | Key holding path to the NHM domain directory |
| `control_file_key` | `pws_control_file` | Key holding the control file path (blank = `control.yml` in domain dir) |
| `result_key` | `pws_result` | Key for result dict (`status`, `n_hru`, `n_days`, `streamflow_stats`) |

---

## Addon Nodes — Weather / Atmosphere

### NOAA Weather Node
**Base class:** `Node` · **Actions:** `default`, `error`

Fetches current NWS surface observations and the 7-day forecast for any US latitude/
longitude point via `api.weather.gov`. No API key required. US locations only.

| Property | Default | Description |
|---|---|---|
| `lat_key` | `lat` | Key holding latitude (decimal degrees) |
| `lon_key` | `lon` | Key holding longitude (decimal degrees) |
| `result_key` | `noaa_weather` | Key for result dict (`current_observation`, `forecast_periods` list) |

### WRF Model Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs WRF-ARW (`real.exe` + `wrf.exe`) in a pre-configured WRF run directory.
Returns wrfout file paths and run status. Requires a compiled WRF installation with MPI.

| Property | Default | Description |
|---|---|---|
| `run_dir_key` | `wrf_run_dir` | Key holding absolute path to the WRF run directory |
| `nprocs` | `4` | Number of MPI processes |
| `skip_real` | `false` | Skip `real.exe` if `wrfinput_d01` already exists |
| `result_key` | `wrf_result` | Key for result dict (`status`, `real_status`, `wrf_status`, `elapsed_seconds`, `wrfout_files`) |

---

## Addon Nodes — Building Energy

### EnergyPlus Run Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs a DOE EnergyPlus building energy simulation from an IDF (or epJSON) input file and
EPW weather file. Returns annual energy use and end-use breakdown. Requires `energyplus`.

| Property | Default | Description |
|---|---|---|
| `idf_path_key` | `eplus_idf_path` | Key holding path to the `.idf` or `.epJSON` input file |
| `weather_path_key` | `eplus_weather_path` | Key holding path to the `.epw` weather file |
| `output_dir_key` | `eplus_output_dir` | Key holding the output directory path |
| `result_key` | `eplus_result` | Key for result dict (`total_site_energy_kwh`, `peak_electricity_kw`, `end_uses`, `idf_name`) |

---

## Addon Nodes — Aerospace

### Open VSP Geometry Node
**Base class:** `Node` · **Actions:** `default`, `error`

Loads a `.vsp3` OpenVSP parametric geometry model, optionally applies design variable
overrides, and exports the geometry in a selected format. Uses the `openvsp` Python API.

| Property | Default | Description |
|---|---|---|
| `vsp3_path_key` | `vsp3_path` | Key holding path to the `.vsp3` model file |
| `export_format` | `stl` | Export format: `stl`, `degen_geom`, `stp`, `iges`, `obj` |
| `design_vars_key` | `vsp_design_vars` | Key holding design variable override dict (nested: container→group→param→value) |
| `output_path_key` | `vsp_output_path` | Key written with the exported file path |

### VSPAERO Analysis Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs the VSPAERO vortex-lattice / panel method aerodynamic solver on a DegenGeom CSV
file (exported by the Open VSP Geometry Node) and returns CL, CD, CMy, and span efficiency.

| Property | Default | Description |
|---|---|---|
| `degen_geom_key` | `vsp_output_path` | Key holding path to the DegenGeom CSV file |
| `alpha` | `0.0` | Angle of attack in degrees |
| `mach` | `0.1` | Freestream Mach number |
| `result_key` | `vspaero_result` | Key for result dict (`CL`, `CD`, `CMy`, `e`, `alpha`, `mach`) |

### SU2 CFD Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs SU2_CFD (the Stanford open-source CFD solver) with a user-supplied `.cfg`
configuration file. Supports Euler, RANS, and other PDE systems.

| Property | Default | Description |
|---|---|---|
| `config_path_key` | `su2_config_path` | Key holding path to the SU2 `.cfg` file |
| `nprocs` | `1` | Number of MPI processes (`1` = serial) |
| `result_key` | `su2_result` | Key for result dict (`CL`, `CD`, `CMy`, `iterations`, `converged`, `final_residual`) |

### Cart3D Analysis Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs a NASA Cart3D inviscid Euler CFD analysis. Cart3D auto-generates a Cartesian mesh
from a closed triangulated surface — no manual meshing required.

| Property | Default | Description |
|---|---|---|
| `case_dir_key` | `cart3d_case_dir` | Key holding path to the Cart3D case directory |
| `aoa` | `0.0` | Angle of attack in degrees |
| `mach` | `0.5` | Freestream Mach number |
| `result_key` | `cart3d_result` | Key for result dict (`CL`, `CD`, `CM`, `alpha`) |

### FUN3D Run Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs NASA FUN3D (`nodet_mpi`) for high-fidelity RANS or LES CFD in a pre-configured
case directory containing `fun3d.nml` and an unstructured grid.

| Property | Default | Description |
|---|---|---|
| `case_dir_key` | `fun3d_case_dir` | Key holding path to the FUN3D case directory |
| `nprocs` | `4` | Number of MPI processes |
| `result_key` | `fun3d_result` | Key for result dict (`CL`, `CD`, `CM`, `iterations`, `converged`, `residual_history`) |

### NASA CEA Node
**Base class:** `Node` · **Actions:** `default`, `error`

Computes rocket combustion thermochemical properties (Isp, Tc, γ, MW, C\*) using the
NASA CEA code via the `rocketcea` Python wrapper. No separate CEA installation needed.

| Property | Default | Description |
|---|---|---|
| `oxid` | `LOX` | Oxidiser name (e.g. `LOX`, `N2O4`, `IRFNA`) |
| `fuel` | `LH2` | Fuel name (e.g. `LH2`, `RP1`, `MMH`, `Methane`) |
| `pc_psia` | `1000` | Chamber pressure in psia |
| `eps` | `40` | Nozzle expansion ratio (exit/throat area) |
| `of_ratio` | `6.0` | Oxidiser-to-fuel mass ratio |
| `result_key` | `cea_result` | Key for result dict (`Isp_vac`, `Isp_del`, `T_chamber_K`, `gamma`, `MW`, `cstar`) |

### RocketPy Flight Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs a RocketPy 6-DOF rocket flight simulation. You construct the `rocketpy.Flight`
object in a preceding Basic Node and pass it via the shared store.

| Property | Default | Description |
|---|---|---|
| `flight_key` | `rocketpy_flight` | Key holding a configured `rocketpy.Flight` instance |
| `result_key` | `rocketpy_result` | Key for result dict (`apogee_m`, `max_speed_ms`, `max_mach`, `max_accel_ms2`, `flight_time_s`, `apogee_time_s`) |

### GMAT Script Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs a GMAT orbital mechanics script in batch (headless) mode and optionally parses a
GMAT report file to return numerical results. Requires a GMAT installation.

| Property | Default | Description |
|---|---|---|
| `script_path_key` | `gmat_script_path` | Key holding path to the `.script` file |
| `report_path_key` | `gmat_report_path` | Key holding path to the expected report file |
| `result_key` | `gmat_result` | Key for result dict (`status`, `script_path`, `report_data` list of row dicts) |

### OpenMDAO Model Node
**Base class:** `Node` · **Actions:** `default`, `error`

Executes an OpenMDAO multidisciplinary analysis or optimisation problem. Accepts a
configured `openmdao.api.Problem` object built in a preceding Basic Node.

| Property | Default | Description |
|---|---|---|
| `problem_key` | `openmdao_problem` | Key holding a configured `openmdao.api.Problem` instance |
| `driver` | `run_model` | `run_model` = MDA analysis only; `run_driver` = full optimisation |
| `result_key` | `openmdao_result` | Key for result dict (`design_variables`, `objectives`, `constraints`, `converged`) |

### Optimization Node
**Base class:** `Node` · **Actions:** `default`, `error`

Minimises a scalar objective function using `scipy.optimize.minimize`. You supply a
Python callable and an initial guess vector via the shared store.

| Property | Default | Description |
|---|---|---|
| `objective_key` | `objective_fn` | Key holding a callable `f(x) → float` |
| `x0_key` | `x0` | Key holding the initial guess (list or ndarray) |
| `method` | `SLSQP` | SciPy optimisation method: `SLSQP`, `Nelder-Mead`, `BFGS`, `L-BFGS-B`, etc. |
| `bounds_key` | _(empty)_ | Key holding a list of `(min, max)` tuples |
| `constraints_key` | _(empty)_ | Key holding a list of SciPy constraint dicts |
| `result_key` | `opt_result` | Key for result dict (`x_optimal`, `f_optimal`, `success`, `nfev`, `message`) |

### NASA Trick Simulation Node
**Base class:** `Node` · **Actions:** `default`, `error`

Builds (optionally) and runs a NASA Trick simulation. Reads Trick log files after the
run and returns extracted variable time-series arrays.

| Property | Default | Description |
|---|---|---|
| `sim_dir_key` | `trick_sim_dir` | Key holding path to the Trick simulation directory |
| `input_file_key` | `trick_input_file` | Key holding the Python input file path (relative to sim dir) |
| `build` | `true` | If `true`, run `trick-CP` to compile before executing |
| `log_vars_key` | `trick_log_vars` | Key holding a list of Trick variable names to extract from log files |
| `result_key` | `trick_result` | Key for result dict (`build_status`, `run_status`, `sim_time_s`, `log_data`) |

---

## Addon Nodes — Wind Energy

### OpenFAST Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs an NREL OpenFAST aero-elastic wind turbine simulation from a `.fst` primary input
file and returns rotor performance summary statistics. Requires `openfast` on the PATH.

| Property | Default | Description |
|---|---|---|
| `fst_path_key` | `openfast_fst_path` | Key holding path to the primary `.fst` input file |
| `result_key` | `openfast_result` | Key for result dict (`status`, `sim_time_s`, `elapsed_wall_s`, `performance_summary`) |

The `performance_summary` dict includes `GenPwr_mean_kW`, `RtAeroFxh_mean_kN`, `RtTSR_mean`, and `RotSpeed_mean_rpm`.

### KiteFAST Node
**Base class:** `Node` · **Actions:** `default`, `error`

Runs an NREL KiteFAST airborne-wind-energy (AWE) simulation and returns tether tension,
electrical power, and flight cycle statistics. Requires the `kitefast` executable.

| Property | Default | Description |
|---|---|---|
| `input_path_key` | `kitefast_input_path` | Key holding path to the KiteFAST primary input file |
| `result_key` | `kitefast_result` | Key for result dict (`status`, `sim_time_s`, `summary`) |

The `summary` dict includes `mean_tether_tension_kN`, `mean_electrical_power_kW`, `flight_cycles`, and `mean_altitude_m`.

---

## Addon Nodes — Scientific Computing

### MATLAB Engine Node
**Base class:** `Node` · **Actions:** `default`, `error`

Calls a MATLAB function or script via the `matlab.engine` Python interface and returns
the first output argument. Requires a licensed MATLAB installation with the Python engine.

| Property | Default | Description |
|---|---|---|
| `script_key` | `matlab_script` | Key holding the MATLAB function/script name to call |
| `args_key` | `matlab_args` | Key holding a list of positional arguments |
| `result_key` | `matlab_result` | Key for result dict (`output`, `matlab_version`, `status`) |

### Octave Script Node
**Base class:** `Node` · **Actions:** `default`, `error`

Executes a GNU Octave script file or inline Octave expression in batch mode and returns
a named workspace variable. Only requires `octave` on the PATH — no Python interface.

| Property | Default | Description |
|---|---|---|
| `script_path_key` | `octave_script_path` | Key holding path to a `.m` script file (blank = use inline code) |
| `inline_code_key` | `octave_code` | Key holding an inline Octave expression or script body |
| `result_var` | `result` | Name of the Octave workspace variable to extract and return |
| `result_key` | `octave_result` | Key for result dict (`stdout`, `status`, `result_var_value`) |

---

## Addon Nodes — Data Catalog

### USGS Data Catalog Search Node
**Base class:** `Node` · **Actions:** `default`, `error`

Searches the USGS ScienceBase Catalog by keyword and returns a list of dataset records
with titles, summaries, DOIs, and download links. No API key required.

| Property | Default | Description |
|---|---|---|
| `query_key` | `sciencebase_query` | Key holding the keyword search string |
| `max_results` | `20` | Maximum catalog items to return |
| `fields` | `id,title,summary,link` | Comma-separated ScienceBase metadata fields to include |
| `result_key` | `sb_results` | Key for result dict (`items` list, `total_count`) |

---

- [Getting to Know Nodes — Series Index](tutorials/gtkn_index.md)
- [Tutorials](tutorials/index.md)
- [About PocketFlow](about_pocketflow.md)
- [Help Home](index.md)
