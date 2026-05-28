# PocketFlow Creator — Node Type Catalog

Candidate node types discovered from the PocketFlow official cookbook
(https://github.com/The-Pocket/PocketFlow/tree/main/cookbook) and related
community projects.  Mark each entry with one of:

- `[ ]` — not reviewed yet  
- `[x]` — **include**: add to Creator palette and toolbar  
- `[~]` — **maybe**: discuss further  
- `[-]` — **skip**: not needed  

---

## How to use this file

1. Work through each section and mark each row.
2. Hand the file back to Claude — it will implement all `[x]` entries
   (node type definition, `builtin_node_types.py`, QPainter icon, and
   help/quick-ref entries).

---

## Currently in Creator (reference — do not re-add)

| node_type_id              | Display Name              | Category          |
| ------------------------- | ------------------------- | ----------------- |
| start_node                | Start Node                | Flow Control      |
| stop_node                 | Stop Node                 | Flow Control      |
| basic_node                | Basic Node                | Core              |
| router_node               | Router Node               | Flow Control      |
| subflow_node              | Subflow Node              | Flow Control      |
| llm_prompt_node           | LLM Prompt Node           | AI                |
| json_llm_node             | JSON LLM Node             | AI                |
| classifier_node           | Classifier Node           | AI                |
| agent_node                | Agent Node                | AI                |
| judge_node                | Judge Node                | AI                |
| rag_node                  | RAG Node                  | AI                |
| python_tool_node          | Python Tool Node          | Code              |
| file_reader_node          | File Reader Node          | Data/IO           |
| file_writer_node          | File Writer Node          | Data/IO           |
| human_review_node         | Human Review Node         | Human-in-the-Loop |
| human_input_node          | Human Input Node          | Human-in-the-Loop |
| batch_node                | Batch Node                | Processing        |
| async_node                | Async Node                | Async             |
| async_batch_node          | Async Batch Node          | Async             |
| async_parallel_batch_node | Async Parallel Batch Node | Async             |

---

## Candidate Node Types

---

### Category: AI / Reasoning

| Status | node_type_id          | Display Name          | Base Class | Description                                                                                                                                                                 | Source                                                                                                           |
| ------ | --------------------- | --------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `[X]`  | chain_of_thought_node | Chain-of-Thought Node | Node       | Iterative multi-step reasoning: the LLM produces a sequence of "thoughts" (with optional sub-steps), continuing until it reaches a conclusion. Returns `continue` or `end`. | [pocketflow-thinking](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-thinking)           |
| `[X]`  | majority_vote_node    | Majority Vote Node    | BatchNode  | Calls the LLM N times with the same prompt and picks the most common answer via majority vote — improves reliability for reasoning tasks. Returns `default`.                | [pocketflow-majority-vote](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-majority-vote) |
| `[X]`  | supervisor_node       | Supervisor Node       | Node       | Evaluates the output of a previous node against configurable criteria and routes to `approved` or `retry`. Used to add an oversight loop around unreliable nodes.           | [pocketflow-supervisor](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-supervisor)       |
| `[X]`  | debate_advocate_node  | Debate Advocate Node  | Node       | Generates a structured argument for or against a claim (controlled by the `stance` property: `for` or `against`). Writes key points as a list. Returns `default`.           | [pocketflow-debate](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-debate)               |
| `[X]`  | debate_judge_node     | Debate Judge Node     | Node       | Reads two sides of an argument from the shared store and scores them 1–10, returning `for_wins` or `against_wins`.                                                          | [pocketflow-debate](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-debate)               |

**Suggested properties for `chain_of_thought_node`:**

| Property     | Type    | Default    | Description                                             |
| ------------ | ------- | ---------- | ------------------------------------------------------- |
| model        | string  | ``         | LLM model (blank = project default)                     |
| max_steps    | integer | 10         | Max reasoning steps before forcing conclusion           |
| problem_key  | string  | `problem`  | Shared store key containing the problem to reason about |
| thoughts_key | string  | `thoughts` | Shared store key for the accumulated thought list       |
| solution_key | string  | `solution` | Shared store key for the final answer                   |

**Suggested properties for `majority_vote_node`:**

| Property   | Type    | Default  | Description                             |
| ---------- | ------- | -------- | --------------------------------------- |
| model      | string  | ``       | LLM model                               |
| num_votes  | integer | 5        | Number of independent LLM calls to make |
| prompt_key | string  | `prompt` | Shared store key for the prompt text    |
| output_key | string  | `answer` | Shared store key for the winning answer |

**Suggested properties for `supervisor_node`:**

| Property     | Type    | Default    | Description                                         |
| ------------ | ------- | ---------- | --------------------------------------------------- |
| model        | string  | ``         | LLM model                                           |
| criteria     | string  | ``         | Plain-text quality criteria to check against        |
| input_key    | string  | `answer`   | Shared store key of the value to evaluate           |
| feedback_key | string  | `feedback` | Shared store key to write corrective feedback to    |
| max_retries  | integer | 3          | Maximum approval attempts before forcing `approved` |

---

### Category: Web / Search

| Status | node_type_id    | Display Name    | Base Class | Description                                                                                                                                                    | Source                                                                                                         |
| ------ | --------------- | --------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `[X]`  | web_search_node | Web Search Node | Node       | Executes a web search (DuckDuckGo by default; configurable) using a query from the shared store and writes a list of result snippets. Returns `default`.       | [pocketflow-agent](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-agent)               |
| `[X]`  | web_scrape_node | Web Scrape Node | Node       | Fetches and cleans the text content of a URL from the shared store. Returns `default` or `error`.                                                              | [pocketflow-tool-crawler](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-tool-crawler) |
| `[X]`  | api_call_node   | API Call Node   | Node       | Makes a configurable HTTP request (method, URL, headers, body all from properties or shared store) and writes the response JSON/text. Returns `ok` or `error`. | General pattern / multiple cookbooks                                                                           |

**Suggested properties for `web_search_node`:**

| Property    | Type    | Default          | Description                                    |
| ----------- | ------- | ---------------- | ---------------------------------------------- |
| engine      | string  | `duckduckgo`     | Search engine (`duckduckgo`, `google`, `bing`) |
| num_results | integer | 5                | Maximum results to return                      |
| query_key   | string  | `search_query`   | Shared store key containing the query string   |
| results_key | string  | `search_results` | Shared store key to write results list to      |

**Suggested properties for `api_call_node`:**

| Property   | Type   | Default    | Description                                                                |
| ---------- | ------ | ---------- | -------------------------------------------------------------------------- |
| url        | string | ``         | Endpoint URL (may contain `{key}` placeholders resolved from shared store) |
| method     | string | `GET`      | HTTP method: GET, POST, PUT, PATCH, DELETE                                 |
| headers    | string | ``         | JSON object of request headers                                             |
| body_key   | string | ``         | Shared store key whose value is sent as request body (blank = no body)     |
| output_key | string | `response` | Shared store key to write the response to                                  |
| timeout    | number | 30.0       | Request timeout in seconds                                                 |

---

### Category: Data / Vector / Embeddings

| Status | node_type_id         | Display Name         | Base Class | Description                                                                                                                                              | Source                                                                                                                                                                                                      |
| ------ | -------------------- | -------------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `[X]`  | text_chunk_node      | Text Chunk Node      | BatchNode  | Splits a long text from the shared store into overlapping chunks of configurable size. Writes a list of chunk strings. Returns `default`.                | [pocketflow-rag](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-rag)                                                                                                                |
| `[X]`  | embed_node           | Embed Node           | BatchNode  | Generates vector embeddings for a list of text chunks using a configurable embedding model. Writes a list/array of embedding vectors. Returns `default`. | [pocketflow-rag](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-rag) / [pocketflow-chat-memory](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-chat-memory) |
| `[X]`  | vector_index_node    | Vector Index Node    | Node       | Builds or updates a FAISS / in-memory vector index from a list of embeddings. Returns `default`.                                                         | [pocketflow-rag](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-rag)                                                                                                                |
| `[X]`  | vector_retrieve_node | Vector Retrieve Node | Node       | Embeds a query and searches a vector index for the top-K nearest chunks. Writes a list of retrieved texts. Returns `default`.                            | [pocketflow-rag](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-rag)                                                                                                                |

**Suggested properties for `text_chunk_node`:**

| Property   | Type    | Default  | Description                                             |
| ---------- | ------- | -------- | ------------------------------------------------------- |
| chunk_size | integer | 512      | Maximum tokens/characters per chunk                     |
| overlap    | integer | 64       | Overlap in tokens/characters between consecutive chunks |
| input_key  | string  | `text`   | Shared store key of the input document string           |
| output_key | string  | `chunks` | Shared store key to write the chunk list to             |

**Suggested properties for `embed_node`:**

| Property   | Type   | Default            | Description                                 |
| ---------- | ------ | ------------------ | ------------------------------------------- |
| model      | string | `nomic-embed-text` | Embedding model name                        |
| input_key  | string | `chunks`           | Shared store key of the text list to embed  |
| output_key | string | `embeddings`       | Shared store key for output embedding array |

**Suggested properties for `vector_retrieve_node`:**

| Property    | Type    | Default            | Description                                      |
| ----------- | ------- | ------------------ | ------------------------------------------------ |
| top_k       | integer | 5                  | Number of nearest neighbours to retrieve         |
| embed_model | string  | `nomic-embed-text` | Embedding model for query vectorisation          |
| query_key   | string  | `query`            | Shared store key of the query string             |
| index_key   | string  | `index`            | Shared store key of the vector index object      |
| texts_key   | string  | `chunks`           | Shared store key of the original texts list      |
| output_key  | string  | `retrieved`        | Shared store key to write retrieved text list to |

---

### Category: Database / SQL

| Status | node_type_id     | Display Name     | Base Class | Description                                                                                                                                      | Source                                                                                                 |
| ------ | ---------------- | ---------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| `[X]`  | db_schema_node   | DB Schema Node   | Node       | Connects to a SQLite (or generic SQL) database and reads its schema (table names, column names, types) into the shared store. Returns `default`. | [pocketflow-text2sql](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-text2sql) |
| `[X]`  | nl_to_sql_node   | NL→SQL Node      | Node       | Uses an LLM to translate a natural-language question and a DB schema into a SQL query string. Returns `default`.                                 | [pocketflow-text2sql](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-text2sql) |
| `[X]`  | sql_execute_node | SQL Execute Node | Node       | Runs a SQL query string against a configured database and writes results as a list of dicts. Returns `ok` or `error`.                            | [pocketflow-text2sql](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-text2sql) |

**Suggested properties for `sql_execute_node`:**

| Property       | Type   | Default        | Description                                            |
| -------------- | ------ | -------------- | ------------------------------------------------------ |
| db_type        | string | `sqlite`       | Database type: `sqlite`, `postgres`, `mysql`           |
| connection_key | string | `db_path`      | Shared store key for the connection string / file path |
| query_key      | string | `sql_query`    | Shared store key containing the SQL to execute         |
| output_key     | string | `query_result` | Shared store key to write row results to               |
| error_key      | string | `sql_error`    | Shared store key to write any error message to         |

---

### Category: Voice / Audio

| Status | node_type_id        | Display Name        | Base Class | Description                                                                                                                                                                      | Source                                                                                                     |
| ------ | ------------------- | ------------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `[X]`  | speech_to_text_node | Speech-to-Text Node | Node       | Transcribes an audio clip (file path or raw data from shared store) to text using a configurable STT service, or local STT service (Whisper, Deepgram, etc.). Returns `default`. | [pocketflow-voice-chat](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-voice-chat) |
| `[X]`  | text_to_speech_node | Text-to-Speech Node | Node       | Converts a text string from the shared store to audio and writes the audio file path or base64 data. Returns `default`.                                                          | [pocketflow-voice-chat](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-voice-chat) |

**Suggested properties for `speech_to_text_node`:**

| Property   | Type   | Default      | Description                                           |
| ---------- | ------ | ------------ | ----------------------------------------------------- |
| model      | string | `whisper`    | STT model / service (`whisper`, `deepgram`, `google`) |
| input_key  | string | `audio_path` | Shared store key for audio file path                  |
| output_key | string | `transcript` | Shared store key for transcribed text                 |
| language   | string | ``           | Language hint (blank = auto-detect)                   |

---

### Category: Document / Vision

| Status | node_type_id       | Display Name       | Base Class | Description                                                                                                                                              | Source                                                                                               |
| ------ | ------------------ | ------------------ | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `[X]`  | pdf_extract_node   | PDF Extract Node   | Node       | Converts a PDF to images and uses a vision LLM to extract structured data (fields, tables, text). Returns `default`.                                     | [pocketflow-invoice](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-invoice) |
| `[X]`  | image_vision_node  | Image Vision Node  | Node       | Sends an image (file path or URL from shared store) to a vision-capable LLM with a configurable prompt and writes the response text. Returns `default`.  | [pocketflow-invoice](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-invoice) |
| `[X]`  | data_validate_node | Data Validate Node | Node       | Checks structured data from the shared store against configurable rules (required fields, numeric ranges, regex patterns). Returns `valid` or `invalid`. | [pocketflow-invoice](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-invoice) |

**Suggested properties for `pdf_extract_node`:**

| Property   | Type   | Default     | Description                                 |
| ---------- | ------ | ----------- | ------------------------------------------- |
| model      | string | ``          | Vision LLM model (blank = project default)  |
| fields     | string | ``          | Comma-separated field names to extract      |
| input_key  | string | `pdf_path`  | Shared store key for the PDF file path      |
| output_key | string | `extracted` | Shared store key to write extracted dict to |

---

### Category: Code / Execution

| Status | node_type_id   | Display Name   | Base Class | Description                                                                                                                             | Source                                                                                                             |
| ------ | -------------- | -------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `[X]`  | code_gen_node  | Code Gen Node  | Node       | Uses an LLM to generate Python (or other language) code from a natural-language specification. Returns `default`.                       | [pocketflow-code-generator](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-code-generator) |
| `[X]`  | code_exec_node | Code Exec Node | Node       | Executes a Python code string from the shared store in a subprocess sandbox and writes stdout/stderr. Returns `ok` or `error`.          | [pocketflow-code-generator](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-code-generator) |
| `[X]`  | test_gen_node  | Test Gen Node  | Node       | Uses an LLM to generate a suite of test cases (unit tests or input/output pairs) for a given function specification. Returns `default`. | [pocketflow-code-generator](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-code-generator) |

**Suggested properties for `code_exec_node`:**

| Property   | Type   | Default  | Description                                        |
| ---------- | ------ | -------- | -------------------------------------------------- |
| language   | string | `python` | Execution language (`python`, `bash`)              |
| timeout    | number | 10.0     | Execution timeout in seconds                       |
| code_key   | string | `code`   | Shared store key containing the code string to run |
| stdout_key | string | `stdout` | Shared store key to write stdout to                |
| stderr_key | string | `stderr` | Shared store key to write stderr to                |

---

### Category: Data Processing / Flow Control

| Status | node_type_id      | Display Name      | Base Class | Description                                                                                                                                                        | Source                                                                                                       |
| ------ | ----------------- | ----------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| `[X]`  | map_node          | Map Node          | Node       | Reads a list from the shared store, applies a configurable transformation (via a template expression or tool name), and writes the result list. Returns `default`. | [pocketflow-map-reduce](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-map-reduce)   |
| `[X]`  | reduce_node       | Reduce Node       | Node       | Aggregates a list (sum, count, concatenate, or LLM summarise) from the shared store into a single value. Returns `default`.                                        | [pocketflow-map-reduce](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-map-reduce)   |
| `[X]`  | condition_node    | Condition Node    | Node       | Evaluates a Python expression against the shared store values and returns `true` or `false` to route the flow.                                                     | General pattern                                                                                              |
| `[X]`  | loop_counter_node | Loop Counter Node | Node       | Increments a counter in the shared store and returns `continue` until `max_iterations` is reached, then returns `done`. Used to cap retry loops.                   | General pattern                                                                                              |
| `[X]`  | transform_node    | Transform Node    | Node       | Applies a configurable Jinja2 template to shared store values and writes the rendered result to an output key. Returns `default`.                                  | General pattern                                                                                              |
| `[X]`  | merge_node        | Merge Node        | Node       | Waits for and merges outputs from parallel branches into a single dict in the shared store. Returns `default`.                                                     | [pocketflow-multi-agent](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-multi-agent) |

**Suggested properties for `condition_node`:**

| Property   | Type   | Default | Description                                                                  |
| ---------- | ------ | ------- | ---------------------------------------------------------------------------- |
| expression | string | ``      | Python expression evaluated with shared store as locals (e.g. `score > 0.8`) |

**Suggested properties for `loop_counter_node`:**

| Property       | Type    | Default     | Description                                |
| -------------- | ------- | ----------- | ------------------------------------------ |
| counter_key    | string  | `iteration` | Shared store key for the loop counter      |
| max_iterations | integer | 5           | Maximum iterations before returning `done` |

---

### Category: Calendar / Scheduling

| Status | node_type_id        | Display Name        | Base Class | Description                                                                                                                     | Source                                                                                                               |
| ------ | ------------------- | ------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `[X]`  | calendar_read_node  | Calendar Read Node  | Node       | Lists upcoming calendar events for a configurable number of days using Google Calendar or CalDAV. Returns `default` or `error`. | [pocketflow-google-calendar](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-google-calendar) |
| `[X]`  | calendar_write_node | Calendar Write Node | Node       | Creates a new calendar event from properties / shared store values. Returns `created` or `error`.                               | [pocketflow-google-calendar](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-google-calendar) |

---

### Category: MCP / Agent Protocol

| Status | node_type_id     | Display Name     | Base Class | Description                                                                                                                                                             | Source                                                                                       |
| ------ | ---------------- | ---------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `[X]`  | mcp_tool_node    | MCP Tool Node    | Node       | Calls a tool exposed via the Model Context Protocol (MCP). Sends a tool name and arguments from the shared store; writes the tool result. Returns `default` or `error`. | [pocketflow-mcp](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-mcp) |
| `[X]`  | a2a_send_node    | A2A Send Node    | AsyncNode  | Sends a task to a remote Agent-to-Agent (A2A) endpoint and writes the task ID. Returns `default`.                                                                       | [pocketflow-a2a](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-a2a) |
| `[X]`  | a2a_receive_node | A2A Receive Node | AsyncNode  | Polls an A2A endpoint for the result of a previously submitted task. Returns `ready` or `waiting`.                                                                      | [pocketflow-a2a](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-a2a) |

**Suggested properties for `mcp_tool_node`:**

| Property   | Type   | Default       | Description                                        |
| ---------- | ------ | ------------- | -------------------------------------------------- |
| server_url | string | ``            | MCP server URL                                     |
| tool_name  | string | ``            | Name of the MCP tool to call                       |
| args_key   | string | `tool_args`   | Shared store key containing the tool argument dict |
| output_key | string | `tool_result` | Shared store key to write the tool response to     |

---

### Category: Observability / Utility

| Status | node_type_id | Display Name | Base Class | Description                                                                                                                                         | Source                                                                                               |
| ------ | ------------ | ------------ | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `[X]`  | log_node     | Log Node     | Node       | Writes a formatted message (combining a template with shared store values) to the run log and optionally to a file. Always returns `default`.       | General pattern                                                                                      |
| `[X]`  | timer_node   | Timer Node   | AsyncNode  | Waits for a configurable delay (seconds) before passing through. Returns `default`. Useful for rate-limit back-off or scheduled polling.            | General pattern                                                                                      |
| `[X]`  | cache_node   | Cache Node   | Node       | Checks a file or in-memory cache for a result keyed by a shared store value; returns `hit` or `miss`. A downstream node writes the cache on `miss`. | [pocketflow-tracing](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-tracing) |
| `[X]`  | trace_node   | Trace Node   | Node       | Records a snapshot of selected shared store keys to a trace file (JSONL). Always returns `default`. Useful for debugging data flow.                 | [pocketflow-tracing](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-tracing) |

---

### Category: Data Structures / Memory

These nodes operate on named lists and persistent stores *within* or *alongside* the shared
store.  Stack and Queue nodes manipulate in-run data structures (the underlying value is a
plain list in the shared store).  Registry and Local Memory nodes provide **cross-run
persistence** backed by a JSON file — unlike the shared store, their data survives between
flow executions.

| Status | node_type_id        | Display Name        | Base Class | Description                                                                                                                                                                                    | Source          |
| ------ | ------------------- | ------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| `[x]`  | registry_node       | Registry Node       | Node       | Reads or writes named objects/values in a persistent JSON registry file.  Mode property selects `get`, `set`, `delete`, or `list`.  Returns `default` (or `not_found` on a missing `get`).    | Original design |
| `[x]`  | stack_push_node     | Stack Push Node     | Node       | Pushes a value from the shared store onto a named LIFO stack (a list in the shared store).  Returns `default`.  Useful for saving context before entering a subflow or recursive agent loop.   | Original design |
| `[x]`  | stack_pop_node      | Stack Pop Node      | Node       | Pops the top value off a named stack in the shared store and writes it to an output key.  Returns `popped` on success or `empty` when the stack is exhausted.                                  | Original design |
| `[x]`  | queue_enqueue_node  | Queue Enqueue Node  | Node       | Appends a value from the shared store to the tail of a named FIFO queue (a list in the shared store).  Returns `default`.  Useful for ordered task lists and producer-consumer patterns.       | Original design |
| `[x]`  | queue_dequeue_node  | Queue Dequeue Node  | Node       | Removes and returns the head item of a named FIFO queue in the shared store, writing it to an output key.  Returns `dequeued` on success or `empty` when the queue is exhausted.               | Original design |
| `[x]`  | local_memory_node   | Local Memory Node   | Node       | Reads, writes, appends to, or clears a persistent JSON memory file on disk.  Survives between flow runs — suitable for conversation history, learned preferences, and cross-run caching.       | Original design |

---

**Suggested properties for `registry_node`:**

| Property        | Type   | Default            | Description                                                                    |
| --------------- | ------ | ------------------ | ------------------------------------------------------------------------------ |
| mode            | string | `get`              | Operation: `get`, `set`, `delete`, `list`                                      |
| registry_file   | string | `.pfc_registry.json` | Path to the JSON registry file (relative to project root)                    |
| namespace       | string | `default`          | Registry namespace — keeps keys from different uses from colliding             |
| key             | string | ``                 | Registry key to get/set/delete (ignored for `list`)                            |
| value_store_key | string | `value`            | Shared store key whose value is written on `set`; receives the result on `get` |

**Suggested properties for `stack_push_node`:**

| Property  | Type   | Default   | Description                                               |
| --------- | ------ | --------- | --------------------------------------------------------- |
| stack_key | string | `stack`   | Shared store key for the stack list                       |
| value_key | string | `value`   | Shared store key of the value to push onto the stack      |

**Suggested properties for `stack_pop_node`:**

| Property   | Type   | Default   | Description                                               |
| ---------- | ------ | --------- | --------------------------------------------------------- |
| stack_key  | string | `stack`   | Shared store key for the stack list                       |
| output_key | string | `value`   | Shared store key to write the popped value to             |

**Suggested properties for `queue_enqueue_node`:**

| Property  | Type   | Default   | Description                                               |
| --------- | ------ | --------- | --------------------------------------------------------- |
| queue_key | string | `queue`   | Shared store key for the queue list                       |
| value_key | string | `value`   | Shared store key of the value to append to the queue      |

**Suggested properties for `queue_dequeue_node`:**

| Property   | Type   | Default   | Description                                               |
| ---------- | ------ | --------- | --------------------------------------------------------- |
| queue_key  | string | `queue`   | Shared store key for the queue list                       |
| output_key | string | `value`   | Shared store key to write the dequeued value to           |

**Suggested properties for `local_memory_node`:**

| Property     | Type   | Default             | Description                                                                  |
| ------------ | ------ | ------------------- | ---------------------------------------------------------------------------- |
| mode         | string | `read`              | Operation: `read`, `write`, `append`, `clear`                                |
| memory_file  | string | `.pfc_memory.json`  | Path to the memory JSON file (relative to project root)                      |
| namespace    | string | `default`           | Namespace / top-level key within the memory file                             |
| key          | string | ``                  | Specific key to read/write within the namespace (blank = entire namespace)   |
| value_key    | string | `value`             | Shared store key to read from on `write`/`append`; written to on `read`      |

---

## Summary counts

| Category                       | Candidates |
| ------------------------------ | ---------- |
| AI / Reasoning                 | 5          |
| Web / Search                   | 3          |
| Data / Vector / Embeddings     | 4          |
| Database / SQL                 | 3          |
| Voice / Audio                  | 2          |
| Document / Vision              | 3          |
| Code / Execution               | 3          |
| Data Processing / Flow Control | 6          |
| Calendar / Scheduling          | 2          |
| MCP / Agent Protocol           | 3          |
| Observability / Utility        | 4          |
| Data Structures / Memory       | 6          |
| **Total**                      | **44**     |

---

## Sources

- [PocketFlow cookbook](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook) — 57 examples
- [pocketflow-rag/nodes.py](https://github.com/The-Pocket/PocketFlow/blob/main/cookbook/pocketflow-rag/nodes.py)
- [pocketflow-text2sql](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-text2sql)
- [pocketflow-chat-memory](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-chat-memory)
- [pocketflow-agent](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-agent)
- [pocketflow-map-reduce](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-map-reduce)
- [pocketflow-supervisor](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-supervisor)
- [pocketflow-code-generator](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-code-generator)
- [pocketflow-debate](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-debate)
- [pocketflow-voice-chat](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-voice-chat)
- [pocketflow-invoice](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-invoice)
- [pocketflow-thinking](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-thinking)
- [pocketflow-google-calendar](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-google-calendar)
- [pocketflow-a2a](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-a2a)
- [PocketFlow-Tutorial-Codebase-Knowledge](https://github.com/The-Pocket/PocketFlow-Tutorial-Codebase-Knowledge)
- [GitHub pocketflow topic](https://github.com/topics/pocketflow) — 22 community repos
