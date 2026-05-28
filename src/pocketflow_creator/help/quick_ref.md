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

---

- [Tutorials](tutorials/index.md)
- [About PocketFlow](about_pocketflow.md)
- [Help Home](index.md)
