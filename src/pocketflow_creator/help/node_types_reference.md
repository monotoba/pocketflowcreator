# Node Types Reference — Complete Catalog

**91 built-in node types** organized by category. Each entry shows what the node does, its properties, and example usage.

---

## Quick Navigation

| Category | Count |
|----------|-------|
| [Flow Control](#flow-control) | 5 |
| [AI / LLM](#ai--llm) | 6 |
| [AI / Reasoning](#ai--reasoning) | 5 |
| [Web / Search](#web--search) | 3 |
| [Data / Vector](#data--vector) | 4 |
| [Database / SQL](#database--sql) | 3 |
| [Voice / Audio](#voice--audio) | 2 |
| [Hardware I/O](#hardware-io) | 7 |
| [Document / Vision](#document--vision) | 3 |
| [Code / Execution](#code--execution) | 3 |
| [Data Processing](#data-processing) | 6 |
| [Calendar](#calendar) | 2 |
| [MCP / Agent Protocol](#mcp--agent-protocol) | 3 |
| [Observability / Utility](#observability--utility) | 4 |
| [Data Structures / Memory](#data-structures--memory) | 6 |
| [Security](#security) | 1 |
| [Human-in-the-Loop](#human-in-the-loop) | 2 |
| [Batch / Async](#batch--async) | 5 |
| [I/O](#io) | 3 |
| [System / Shell](#system--shell) | 3 |
| [Networking](#networking) | 3 |
| [Text / Data Processing](#text--data-processing) | 5 |
| [Resilience](#resilience) | 3 |
| [Messaging](#messaging) | 3 |
| **TOTAL** | **91** |

---

## Flow Control

### Start Node
**Purpose:** Entry point of a flow. Always executes first.
- **Actions:** `default`
- **Properties:** None
- **Shared Store:** None
- **Example:**
  ```
  Start → [other nodes]
  ```

### Stop Node
**Purpose:** Exit point of a flow. Flow terminates here.
- **Actions:** None
- **Properties:** None
- **Shared Store:** None

### Basic Node
**Purpose:** No-op passthrough node. Used for organization or as a placeholder.
- **Actions:** `default`
- **Properties:** None
- **Shared Store:** None

### Router Node
**Purpose:** Routes to different actions based on shared store value.
- **Actions:** Configurable (comma-separated)
- **Properties:**
  - `routes`: string — action names (e.g., `"yes,no,maybe"`)
- **Shared Store:** Read from shared store to determine which route

### Subflow Node
**Purpose:** Execute a nested graph referenced by ID.
- **Actions:** Configurable per subflow
- **Properties:**
  - `subflow_id`: string — ID of the graph to execute
- **Shared Store:** Passes through to subflow; propagates results back

---

## AI / LLM

### LLM Prompt Node
**Purpose:** Send a prompt to an LLM and receive text completion.
- **Actions:** `default`
- **Properties:**
  - `prompt_file`: string — prompt text or path to `.md` file
  - `prompt_type`: string — `"string"` or `"path"`
  - `input_key`: string — read input from this shared store key
  - `output_key`: string — write result to this key
  - `model`: string — LLM model name (blank = project default)
  - `temperature`: float — 0–1 (lower = more deterministic)
  - `max_tokens`: integer — max response length
  - `system_prompt`: string — system context override
- **Shared Store:** Reads `input_key`, writes `output_key`
- **Example:** Sentiment analysis, summarization, translation

### JSON LLM Node
**Purpose:** Prompt LLM with JSON schema; parse response as JSON.
- **Actions:** `default` (valid JSON), `invalid` (parse error)
- **Properties:** Similar to LLM Prompt Node
- **Shared Store:** Writes parsed JSON object to `output_key`

### Classifier Node
**Purpose:** Classify input into predefined categories using LLM.
- **Actions:** Dynamic (one per category)
- **Properties:**
  - `prompt_file`: string — classification prompt
  - `categories`: string — comma-separated category names
  - `input_key`: string — text to classify
  - `output_key`: string — winning category
- **Shared Store:** Reads input, writes winning category
- **Example:** Spam detection, sentiment, topic classification

### Judge Node
**Purpose:** LLM evaluates text and routes based on criteria (e.g., "pass" vs. "fail").
- **Actions:** Configurable (typically `pass`, `fail`)
- **Properties:**
  - `prompt_file`: string — evaluation prompt
  - `input_key`: string — content to judge
  - `output_key`: string — judgment result
- **Shared Store:** Reads input, writes judgment

### Agent Node
**Purpose:** Multi-turn LLM agent that can reason or take actions.
- **Actions:** `continue` (agent wants more steps), `done` (agent finished)
- **Properties:**
  - `input_key`: string — user message or task
  - `output_key`: string — final agent result
  - `model`: string — LLM model
  - `max_iterations`: integer — max reasoning steps (default 10)
- **Shared Store:** Reads input, writes result

### RAG Node
**Purpose:** Retrieval-Augmented Generation — fetch context from vector DB, pass to LLM.
- **Actions:** `default`, `no_context`
- **Properties:**
  - `query_key`: string — user question
  - `vector_index_key`: string — vector index reference
  - `context_key`: string — write retrieved context
  - `output_key`: string — write LLM response
- **Shared Store:** Reads query, writes context and response

---

## AI / Reasoning

### Chain of Thought Node
**Purpose:** Multi-step reasoning with explicit step tracking.
- **Actions:** `default`
- **Properties:**
  - `problem_key`: string — input problem
  - `thoughts_key`: string — write accumulated thoughts
  - `solution_key`: string — write final answer
  - `max_steps`: integer — max reasoning steps
  - `model`: string — LLM model
- **Shared Store:** Reads problem, writes thoughts and solution

### Majority Vote Node
**Purpose:** Call LLM N times, pick most common answer.
- **Actions:** `default`
- **Properties:**
  - `prompt_key`: string — prompt text
  - `num_votes`: integer — number of independent calls
  - `output_key`: string — winning answer
  - `model`: string — LLM model
- **Shared Store:** Reads prompt, writes majority result

### Supervisor Node
**Purpose:** Evaluate output against criteria; route to approval or retry.
- **Actions:** `approved`, `retry`, `rejected`
- **Properties:**
  - `input_key`: string — work to review
  - `criteria`: string — evaluation criteria
  - `output_key`: string — feedback
  - `model`: string — LLM model (for evaluation)
- **Shared Store:** Reads input, writes feedback

### Debate Advocate Node
**Purpose:** Generate argument for or against a claim.
- **Actions:** `default`
- **Properties:**
  - `topic_key`: string — claim to argue about
  - `position`: string — `"for"` or `"against"`
  - `output_key`: string — generated argument
  - `model`: string — LLM model
- **Shared Store:** Reads topic, writes argument

### Debate Judge Node
**Purpose:** Compare two arguments and select the stronger one.
- **Actions:** `argument_a`, `argument_b`, `tie`
- **Properties:**
  - `argument_a_key`: string — first argument
  - `argument_b_key`: string — second argument
  - `output_key`: string — verdict
  - `model`: string — LLM model
- **Shared Store:** Reads arguments, writes verdict

---

## Web / Search

### Web Search Node
**Purpose:** Query search engine (Brave, Google) and retrieve results.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `query_key`: string — search query
  - `output_key`: string — result list
- **Shared Store:** Reads query, writes results
- **Requires:** `SEARCH_API_KEY` environment variable

### Web Scrape Node
**Purpose:** Fetch URL and extract text content with BeautifulSoup.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `url_key`: string — URL to scrape
  - `output_key`: string — extracted text
- **Shared Store:** Reads URL, writes text (first 5000 chars)
- **Requires:** `beautifulsoup4` pip package

### API Call Node
**Purpose:** Make HTTP request (GET/POST/etc.) and parse JSON response.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `endpoint`: string — URL
  - `method`: string — `"GET"`, `"POST"`, etc.
  - `input_key`: string — payload (for POST)
  - `output_key`: string — response JSON
  - `headers`: dict — optional HTTP headers
- **Shared Store:** Reads payload, writes response

---

## Data / Vector

### Text Chunk Node
**Purpose:** Split long text into overlapping chunks.
- **Actions:** `default`
- **Properties:**
  - `input_key`: string — text to chunk
  - `output_key`: string — list of chunks
  - `chunk_size`: integer — chars per chunk (default 1000)
  - `overlap`: integer — overlap between chunks
- **Shared Store:** Reads text, writes chunk list

### Embed Node
**Purpose:** Convert text to embeddings vector using LLM provider.
- **Actions:** `default`
- **Properties:**
  - `input_key`: string — text to embed
  - `output_key`: string — embedding vector
- **Shared Store:** Reads text, writes vector
- **Requires:** LLM provider with embedding support

### Vector Index Node
**Purpose:** Build searchable index from vectors.
- **Actions:** `default`
- **Properties:**
  - `vectors_key`: string — input vectors
  - `output_key`: string — index reference
  - `index_type`: string — `"simple"`, `"faiss"`, etc.
- **Shared Store:** Reads vectors, writes index

### Vector Retrieve Node
**Purpose:** Search index for similar vectors (cosine similarity).
- **Actions:** `default` (found), `not_found`
- **Properties:**
  - `index_key`: string — vector index
  - `query_key`: string — query vector
  - `output_key`: string — top-K results
  - `top_k`: integer — max results (default 5)
- **Shared Store:** Reads index and query, writes results

---

## Database / SQL

### DB Schema Node
**Purpose:** Extract schema from SQLite database.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `db_path`: string — path to `.db` file
  - `output_key`: string — schema as dict
- **Shared Store:** Writes schema
- **Requires:** sqlite3 (built-in)

### NL to SQL Node
**Purpose:** Convert natural language question to SQL using LLM.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `query_key`: string — natural language question
  - `schema_key`: string — database schema
  - `output_key`: string — generated SQL
  - `model`: string — LLM model
- **Shared Store:** Reads query and schema, writes SQL

### SQL Execute Node
**Purpose:** Execute SQL query on SQLite database.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `db_path`: string — database file
  - `sql_key`: string — SQL command
  - `output_key`: string — results (list of dicts)
- **Shared Store:** Reads SQL, writes results
- **Requires:** sqlite3 (built-in)

---

## Voice / Audio

### Speech to Text Node
**Purpose:** Convert audio file to text using Google Speech API.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `audio_file_key`: string — path to WAV/MP3
  - `output_key`: string — transcribed text
- **Shared Store:** Reads file path, writes text
- **Requires:** `SpeechRecognition` pip package

### Text to Speech Node
**Purpose:** Generate audio file from text.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `input_key`: string — text to speak
  - `output_file`: string — output MP3 path
  - `output_key`: string — file path written to shared store
- **Shared Store:** Reads text, writes file path
- **Requires:** `pyttsx3` pip package

---

## Hardware I/O

### USB Serial Input
**Purpose:** Read data from serial port (Arduino, sensors, etc.).
- **Actions:** `default` (success), `timeout`
- **Properties:**
  - `port`: string — `/dev/ttyUSB0` or `COM3`
  - `baudrate`: integer — 9600, 115200, etc.
  - `output_key`: string — received data
- **Shared Store:** Writes received data
- **Requires:** `pyserial` pip package

### USB Serial Output
**Purpose:** Write data to serial port.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `port`: string — serial port path
  - `baudrate`: integer — baud rate
  - `input_key`: string — data to send
  - `output_key`: string — status
- **Shared Store:** Reads data to send, writes status
- **Requires:** `pyserial` pip package

### Audio Input
**Purpose:** Record audio from microphone.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `duration`: float — seconds to record
  - `sample_rate`: integer — Hz (default 16000)
  - `output_file`: string — output WAV path
  - `output_key`: string — file path
- **Shared Store:** Writes file path
- **Requires:** `sounddevice`, `soundfile` pip packages

### Audio Output
**Purpose:** Play audio file through speaker.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `input_key`: string — audio file path
  - `output_key`: string — status
- **Shared Store:** Reads file path, writes status
- **Requires:** `sounddevice`, `soundfile` pip packages

### Video Input
**Purpose:** Record video from camera.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `duration`: float — seconds to record
  - `output_file`: string — output MP4 path
  - `output_key`: string — file path
- **Shared Store:** Writes file path
- **Requires:** `opencv-python` pip package

### Video Output
**Purpose:** Play video file.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `input_key`: string — video file path
  - `output_key`: string — status
- **Shared Store:** Reads file path, writes status
- **Requires:** `opencv-python` pip package

### Webcam
**Purpose:** Capture frame or stream from webcam.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `operation`: string — `"capture"` (single) or `"stream"` (multiple)
  - `frame_count`: integer — frames to capture
  - `output_file`: string — output file path
  - `output_key`: string — image/frames
- **Shared Store:** Writes frame or frame list
- **Requires:** `opencv-python` pip package

---

## Document / Vision

### PDF Extract Node
**Purpose:** Extract text from PDF file.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `file_path_key`: string — PDF file path
  - `output_key`: string — extracted text
- **Shared Store:** Reads file path, writes text
- **Requires:** `PyPDF2` pip package

### Image Vision Node
**Purpose:** Analyze image with LLM vision capability.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `image_path_key`: string — image file path
  - `task`: string — what to do (e.g., `"describe"`)
  - `output_key`: string — analysis result
- **Shared Store:** Reads file path, writes analysis
- **Requires:** LLM provider with vision support

### Data Validate Node
**Purpose:** Check if data matches expected type or schema.
- **Actions:** `default` (valid), `invalid`
- **Properties:**
  - `input_key`: string — data to validate
  - `output_key`: string — boolean (valid/invalid)
  - `validation_type`: string — `"type"`, `"schema"`, etc.
  - `expected_type`: string — `"str"`, `"dict"`, `"list"`, etc.
- **Shared Store:** Reads data, writes validation result

---

## Code / Execution

### Code Gen Node
**Purpose:** Generate code using LLM.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `spec_key`: string — code specification
  - `output_key`: string — generated code
  - `language`: string — `"python"`, `"javascript"`, etc.
  - `model`: string — LLM model
- **Shared Store:** Reads spec, writes code

### Code Exec Node
**Purpose:** Execute Python code dynamically.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `code`: string — Python code to execute
  - `output_key`: string — execution result (stdout)
- **Shared Store:** Available as `shared` variable in code; writes result

### Test Gen Node
**Purpose:** Generate test cases for code using LLM.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `code_key`: string — code to test
  - `output_key`: string — generated tests
  - `test_framework`: string — `"pytest"`, `"unittest"`, etc.
  - `model`: string — LLM model
- **Shared Store:** Reads code, writes tests

---

## Data Processing

### Map Node
**Purpose:** Apply transformation to each item in a list.
- **Actions:** `default`
- **Properties:**
  - `input_key`: string — list to map
  - `output_key`: string — transformed list
  - `operation`: string — operation name
- **Shared Store:** Reads list, writes result

### Reduce Node
**Purpose:** Accumulate list to single value.
- **Actions:** `default`
- **Properties:**
  - `input_key`: string — list to reduce
  - `output_key`: string — final value
  - `operation`: string — reduce operation
  - `initial_value`: any — starting value
- **Shared Store:** Reads list, writes result

### Condition Node
**Purpose:** Branch flow based on boolean condition.
- **Actions:** `true`, `false`
- **Properties:**
  - `input_key`: string — value to test
  - `condition`: string — Python expression
- **Shared Store:** Reads value, evaluates condition

### Loop Counter Node
**Purpose:** Repeat a sub-flow N times with counter.
- **Actions:** `continue` (next iteration), `done`
- **Properties:**
  - `max_iterations`: integer — times to repeat
  - `counter_key`: string — write current counter
  - `output_key`: string — accumulated results
- **Shared Store:** Writes counter and results

### Transform Node
**Purpose:** Convert data structure (dict ↔ list, etc.).
- **Actions:** `default`
- **Properties:**
  - `input_key`: string — data to transform
  - `output_key`: string — transformed data
  - `operation`: string — transformation type
- **Shared Store:** Reads input, writes output

### Merge Node
**Purpose:** Combine multiple lists or dicts into one.
- **Actions:** `default`
- **Properties:**
  - `input_keys`: list — keys to merge
  - `output_key`: string — merged result
  - `merge_type`: string — `"list"` or `"dict"`
- **Shared Store:** Reads inputs, writes merged result

---

## Calendar

### Calendar Read Node
**Purpose:** Fetch events from Google Calendar.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `calendar_id`: string — Google Calendar ID
  - `output_key`: string — events list
  - `max_events`: integer — max to fetch (default 10)
- **Shared Store:** Writes events
- **Requires:** `GOOGLE_CALENDAR_ID` env var, Google Auth libs

### Calendar Write Node
**Purpose:** Create event on Google Calendar.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `calendar_id`: string — Google Calendar ID
  - `event_key`: string — event data (dict)
  - `output_key`: string — created event ID
- **Shared Store:** Reads event, writes event ID
- **Requires:** Google Auth libs

---

## MCP / Agent Protocol

### MCP Tool Node
**Purpose:** Call tool via Model Context Protocol (MCP) server.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `tool_name`: string — tool to invoke
  - `input_key`: string — tool arguments
  - `output_key`: string — tool result
- **Shared Store:** Reads args, writes result
- **Requires:** MCP server running, `MCP_SERVER_URL` env var

### A2A Send Node
**Purpose:** Send message to another agent.
- **Actions:** `default`
- **Properties:**
  - `recipient_key`: string — recipient ID
  - `message_key`: string — message to send
  - `output_key`: string — status
- **Shared Store:** Reads recipient and message, writes status
- **Internal:** Uses `__a2a_messages__` shared store namespace

### A2A Receive Node
**Purpose:** Receive message from another agent.
- **Actions:** `default` (message received), `empty`
- **Properties:**
  - `sender_key`: string — sender ID
  - `output_key`: string — received message
- **Shared Store:** Reads sender, writes message
- **Internal:** Uses `__a2a_messages__` namespace

---

## Observability / Utility

### Log Node
**Purpose:** Write message to console and run log.
- **Actions:** `default`
- **Properties:**
  - `input_key`: string — message to log
  - `output_key`: string — message (passthrough)
  - `log_level`: string — `"info"`, `"debug"`, `"warn"`, `"error"`
- **Shared Store:** Reads message, writes same

### Timer Node
**Purpose:** Measure execution time of sub-flow.
- **Actions:** `default`
- **Properties:**
  - `input_key`: string — operation or ID
  - `output_key`: string — elapsed time (seconds)
- **Shared Store:** Reads input, writes elapsed time

### Cache Node
**Purpose:** Cache result by key; return cached value on hit.
- **Actions:** `default` (hit), `miss`
- **Properties:**
  - `key`: string — cache key
  - `input_key`: string — value to cache
  - `output_key`: string — cached or new value
  - `ttl`: integer — cache lifetime (seconds)
- **Shared Store:** Reads/writes cache via `__cache__` namespace

### Trace Node
**Purpose:** Add structured trace/span to execution.
- **Actions:** `default`
- **Properties:**
  - `span_name`: string — span name for tracing
  - `input_key`: string — data to trace
  - `output_key`: string — trace ID
- **Shared Store:** Reads input, writes trace info

---

## Data Structures / Memory

### Registry Node
**Purpose:** Persistent key-value storage (persistent dict).
- **Actions:** `default`
- **Properties:**
  - `operation`: string — `"set"`, `"get"`, `"delete"`
  - `key`: string — registry key
  - `input_key`: string — value (for `set`)
  - `output_key`: string — retrieved value (for `get`)
- **Shared Store:** Operates on `__registry__` namespace

### Stack Push Node
**Purpose:** Push value onto a stack.
- **Actions:** `default`
- **Properties:**
  - `stack_name`: string — named stack
  - `input_key`: string — value to push
- **Shared Store:** Updates `__stack_<name>__` array

### Stack Pop Node
**Purpose:** Pop value from stack.
- **Actions:** `default` (success), `empty`
- **Properties:**
  - `stack_name`: string — named stack
  - `output_key`: string — popped value
- **Shared Store:** Reads from `__stack_<name>__` array, writes value

### Queue Enqueue Node
**Purpose:** Add item to queue (FIFO).
- **Actions:** `default`
- **Properties:**
  - `queue_name`: string — named queue
  - `input_key`: string — item to add
- **Shared Store:** Updates `__queue_<name>__` array

### Queue Dequeue Node
**Purpose:** Remove item from queue (FIFO).
- **Actions:** `default` (success), `empty`
- **Properties:**
  - `queue_name`: string — named queue
  - `output_key`: string — dequeued item
- **Shared Store:** Reads from `__queue_<name>__` array

### Local Memory Node
**Purpose:** Temporary local storage (session-scoped dict).
- **Actions:** `default`
- **Properties:**
  - `operation`: string — `"set"`, `"get"`, `"clear"`
  - `key`: string — memory key
  - `input_key`: string — value (for `set`)
  - `output_key`: string — retrieved value (for `get`)
- **Shared Store:** Operates on `__local_memory__` namespace

---

## Security

### Secret Node
**Purpose:** Load secrets from environment, dotenv, or vault.
- **Actions:** `default` (found), `not_found`
- **Properties:**
  - `key`: string — environment variable name or secret path
  - `source`: string — `"env"`, `"dotenv"`, `"aws_secrets"`, `"vault"`
  - `output_key`: string — loaded secret value
- **Shared Store:** Writes secret
- **Requires:** Appropriate env vars or libs (boto3 for AWS, hvac for Vault)

---

## Human-in-the-Loop

### Human Review Node
**Purpose:** Pause flow; user reviews content and decides pass/fail.
- **Actions:** `approved` (user enters `y`), `rejected` (user enters `n` or cancels)
- **Properties:**
  - `input_key`: string — content to review
  - `output_key`: string — review feedback
  - `instructions`: string — review instructions
- **Shared Store:** Reads content, writes feedback
- **In Creator UI:** Interactive dialog box
- **In Standalone Scripts:**
  - Displays content to stdout
  - Prompts "Approve? [y/n]: " to stdout
  - Reads response from stdin
  - Handles EOF/Ctrl+C gracefully (routes to `rejected`)
  - Works with piped input: `echo "y" | python script.py`
  - Works in CI/CD: `python script.py < approval.txt`

### Human Input Node
**Purpose:** Pause flow; user enters text.
- **Actions:** `saved` (if input provided), `cancelled` (if empty or EOF)
- **Properties:**
  - `prompt`: string — prompt text to show user
  - `output_key`: string — user's input text
- **Shared Store:** Writes user input to `output_key`
- **In Creator UI:** Interactive input dialog
- **In Standalone Scripts:**
  - Displays prompt to stdout
  - Reads input line from stdin
  - Handles EOF/Ctrl+C gracefully (routes to `cancelled`)
  - Works with piped input: `echo "Alice" | python script.py`
  - Works in shell scripts: `python script.py << EOF\nJohn\nEOF`
  - Non-interactive mode: `python script.py < /dev/null` (no crash, action = `cancelled`)

---

## Batch / Async

### Batch Node
**Purpose:** Process items in a batch.
- **Actions:** `default`
- **Properties:**
  - `items_key`: string — list of items
  - `output_key`: string — processed items
- **Shared Store:** Reads items, writes results

### Async Node
**Purpose:** Mark an operation as async (fire-and-forget).
- **Actions:** `default`
- **Properties:**
  - `input_key`: string — data to process async
  - `output_key`: string — async handle/ID
- **Shared Store:** Reads input, writes handle

### Async Batch Node
**Purpose:** Process batch items asynchronously.
- **Actions:** `default`
- **Properties:**
  - `items_key`: string — items to process
  - `output_key`: string — async handles
- **Shared Store:** Reads items, writes handles

### Async Parallel Batch Node
**Purpose:** Process batch items in parallel (max concurrency).
- **Actions:** `default`
- **Properties:**
  - `items_key`: string — items
  - `output_key`: string — results
  - `max_workers`: integer — max concurrent tasks
- **Shared Store:** Reads items, writes results

### Shell Command Node
**Purpose:** Execute shell command and capture output.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `command`: string — shell command to run
  - `output_key`: string — stdout
  - `shell_type`: string — `"bash"`, `"sh"`, `"zsh"`, `"powershell"`, `"cmd"`
  - `timeout`: integer — max seconds to wait (default 30)
- **Shared Store:** Writes stdout/stderr
- **Requires:** Shell available (bash, PowerShell, etc.)

---

## I/O

### File Reader Node
**Purpose:** Read file contents.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `file_path_key`: string — path to read
  - `output_key`: string — file contents
  - `encoding`: string — `"utf-8"` (default), `"ascii"`, etc.
- **Shared Store:** Reads path, writes contents

### File Writer Node
**Purpose:** Write data to file.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `file_path_key`: string — path to write
  - `input_key`: string — data to write
  - `output_key`: string — bytes written
  - `mode`: string — `"w"` (overwrite), `"a"` (append)
- **Shared Store:** Reads path and data, writes byte count

### Python Tool Node
**Purpose:** Load and execute Python module.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `tool_path`: string — path to `.py` file
  - `input_key`: string — input to `run()` function
  - `output_key`: string — function result
- **Shared Store:** Reads input, writes output
- **Requires:** Module has `def run(input)` function

---

## System / Shell

### TTY Serial Node
**Purpose:** Read/write from serial port (see also USB Serial Input/Output).
- **Actions:** `read` (success), `timeout`, `written`
- **Properties:**
  - `port`: string — serial port path
  - `baudrate`: integer — baud rate
  - `operation`: string — `"read"` or `"write"`
  - `input_key`: string — data to write (for `write`)
  - `output_key`: string — data read (for `read`)
- **Shared Store:** Reads/writes serial data

### Spreadsheet Node
**Purpose:** Read/write CSV, TSV, or Excel files.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `file_path_key`: string — file to read/write
  - `operation`: string — `"read"` or `"write"`
  - `sheet_name`: string — Excel sheet (if Excel)
  - `output_key`: string — data (for `read`)
  - `input_key`: string — data to write (for `write`)
- **Shared Store:** Reads/writes tabular data
- **Requires:** `openpyxl` for Excel

---

## Networking

### Socket Node
**Purpose:** TCP socket client/server communication.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `operation`: string — `"connect"` (client) or `"listen"` (server)
  - `host`: string — hostname/IP
  - `port`: integer — port number
  - `input_key`: string — data to send (for `connect`)
  - `output_key`: string — received data
- **Shared Store:** Reads/writes socket data

### WebSocket Node
**Purpose:** WebSocket communication.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `operation`: string — `"send"` or `"listen"`
  - `url`: string — WebSocket URL (e.g., `ws://localhost:8000`)
  - `input_key`: string — message to send
  - `output_key`: string — received message
- **Shared Store:** Reads/writes messages
- **Requires:** `websockets` pip package

### Webhook Trigger Node
**Purpose:** Receive and process webhook payload.
- **Actions:** `default`
- **Properties:**
  - `payload_key`: string — payload from webhook
  - `output_key`: string — parsed payload
  - `webhook_path`: string — endpoint path (e.g., `/webhook`)
- **Shared Store:** Writes parsed webhook data

---

## Text / Data Processing

### Regex Node
**Purpose:** Pattern matching and text replacement.
- **Actions:** `default` (found/replaced), `not_found`
- **Properties:**
  - `input_key`: string — text to search
  - `output_key`: string — matches or replaced text
  - `pattern`: string — regex pattern
  - `operation`: string — `"findall"`, `"sub"`, `"match"`
  - `replacement`: string — replacement text (for `sub`)
- **Shared Store:** Reads text, writes results

### Template Render Node
**Purpose:** Simple variable interpolation in text.
- **Actions:** `default`
- **Properties:**
  - `template_key`: string — template with `{{var}}` placeholders
  - `output_key`: string — rendered output
- **Shared Store:** Reads template, writes rendered text

### JSON Parse Node
**Purpose:** Parse JSON string to object.
- **Actions:** `default` (valid), `invalid`
- **Properties:**
  - `input_key`: string — JSON string
  - `output_key`: string — parsed object
- **Shared Store:** Reads JSON, writes object

### List Operations Node
**Purpose:** Transform lists (sort, reverse, unique, etc.).
- **Actions:** `default`
- **Properties:**
  - `input_key`: string — list to transform
  - `output_key`: string — result
  - `operation`: string — `"sort"`, `"reverse"`, `"unique"`, `"length"`
- **Shared Store:** Reads list, writes result

### String Operations Node
**Purpose:** Transform strings (upper, lower, capitalize, etc.).
- **Actions:** `default`
- **Properties:**
  - `input_key`: string — string to transform
  - `output_key`: string — result
  - `operation`: string — `"upper"`, `"lower"`, `"capitalize"`, `"length"`, `"trim"`
- **Shared Store:** Reads string, writes result

---

## Resilience

### Retry Node
**Purpose:** Retry failed operation with exponential backoff.
- **Actions:** `default` (success), `exhausted` (max retries reached)
- **Properties:**
  - `input_key`: string — operation/input
  - `output_key`: string — result
  - `max_retries`: integer — max attempt count (default 3)
  - `backoff_factor`: float — exponential backoff multiplier
- **Shared Store:** Reads input, writes result

### Rate Limiter Node
**Purpose:** Enforce request rate limits.
- **Actions:** `default` (allowed), `throttled`
- **Properties:**
  - `input_key`: string — request data
  - `output_key`: string — result
  - `requests_per_second`: float — rate limit
- **Shared Store:** Reads input, writes result

### Provider Failover Node
**Purpose:** Resilient LLM calls across multiple providers with error-specific retries.
- **Actions:** `success` (provider returned response), `all_failed` (all retries exhausted)
- **Properties:**
  - `providers_config`: JSON text — ordered list of providers with priorities and retry policies
    ```json
    [
      {
        "priority": 1,
        "profile_id": "uuid-of-provider",
        "model": "",
        "timeout_retries": 3,
        "network_retries": 3,
        "ratelimit_retries": 2,
        "expired_retries": 1,
        "unknown_retries": 1,
        "retry_delay": 2.0,
        "session_offset_seconds": 60
      }
    ]
    ```
  - `prompt_key`: string — shared-store key containing prompt (default `"prompt"`)
  - `output_key`: string — shared-store key for response (default `"failover_response"`)
  - `error_key`: string — shared-store key for error message on `all_failed` (default `"failover_error"`)
- **Shared Store:** Reads from `prompt_key`, writes response to `output_key` on success or error to `error_key` on failure
- **Behavior:**
  - Tries providers in priority order (lowest priority first)
  - Per-error-type retries: timeout, network, rate-limit, session-expired, unknown errors each have configurable retry count
  - Session-expired providers are marked unavailable until reinstatement time + offset
  - Sleeps between retries (configurable delay for timeout/network errors)
  - Routes `success` on any provider response, `all_failed` when all providers exhaust retries
- **Error Types:** Timeout, Network, Rate Limit (HTTP 429), Session/Token Expired (HTTP 401/403), Unknown

---

## Messaging

### Email Send Node
**Purpose:** Send email via SMTP.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `recipient_key`: string — to: email address
  - `subject_key`: string — email subject
  - `body_key`: string — email body (HTML or plain text)
  - `output_key`: string — status
- **Shared Store:** Reads email data, writes status
- **Requires:** `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `SMTP_SERVER` env vars

### Email Read Node
**Purpose:** Fetch emails from IMAP mailbox.
- **Actions:** `default` (success), `error`
- **Properties:**
  - `folder`: string — mailbox folder (default `"INBOX"`)
  - `max_emails`: integer — max to fetch
  - `output_key`: string — email list
- **Shared Store:** Writes emails
- **Requires:** `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `IMAP_SERVER` env vars

### Notification Node
**Purpose:** Send notification to Slack, Discord, Teams, or Telegram.
- **Actions:** `default` (sent), `error`
- **Properties:**
  - `channel`: string — `"slack"`, `"discord"`, `"teams"`, `"telegram"`
  - `message_key`: string — message text
  - `output_key`: string — status
- **Shared Store:** Reads message, writes status
- **Requires:** Webhook URL in appropriate env var (`SLACK_WEBHOOK`, etc.)

---

## Context Compact Node

**Purpose:** Compress context using different strategies.
- **Actions:** `default`
- **Properties:**
  - `input_key`: string — context to compress
  - `output_key`: string — compressed context
  - `strategy`: string — `"truncate"`, `"summarize"`, `"sliding_window"`
  - `max_length`: integer — max output length
- **Shared Store:** Reads context, writes compressed version

---

## Conversation History Node

**Purpose:** Maintain multi-turn conversation state.
- **Actions:** `default`
- **Properties:**
  - `input_key`: string — new user message
  - `output_key`: string — conversation history
  - `max_history`: integer — max messages to keep
- **Shared Store:** Reads message, writes history
- **Internal:** Stores history in `__conversation_history__` namespace

---

## Summary

**Total coverage: 90+ node types** across 28 categories. Each node is fully implemented in:
- ✅ Visual palette with custom icons
- ✅ Standalone Python script generation (all 90+ node types supported)
- ✅ Object Inspector property editor
- ✅ Node dispatcher with type-based execution
- ✅ Proper I/O handling in standalone scripts:
  - **stdin** for interactive nodes (Human Input, Human Review)
  - **stdout** for prompts and normal output
  - **stderr** for error messages and tracing (Trace Node)
  - Works in pipes, CI/CD, and shell scripts
  - Graceful EOF handling for non-interactive execution

For tutorials and examples, see:
- [Standalone Scripts Tutorial](standalone_scripts.md) — includes I/O and interactive examples
- [Hardware I/O Tutorial](hardware_io.md)
- [Your First Flow Tutorial](../tutorials/part1_fundamentals.md)

