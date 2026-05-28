# Part 15 — Observability and Data Structure Nodes

This part covers ten nodes: four for instrumenting and observing flows (Log, Timer,
Cache, Trace), and six for managing in-flow data structures (Registry, Stack Push/Pop,
Queue Enqueue/Dequeue, Local Memory).

**Prerequisite:** Complete Part 1 (Start / Stop / Basic) before this part.

---

## Tutorial T-N55: Log Node

### What it does

The **Log Node** writes a formatted message to the Run Log (and optionally to a file
or external logging service). It does not modify the shared store or change control
flow — it is a pure side-effect node you insert anywhere in a flow for observability.

### Use cases

- Marking the start and end of critical pipeline stages
- Logging intermediate shared-store values without using the Shared Store tab
- Writing audit trails that persist after the run

### What you'll build

A flow with Log Nodes at the start and end of a processing step.

### Step-by-step

**Step 1: Create project `gtkn_part15`.**

**Step 2: Add two Log Nodes** named `LogStart` and `LogEnd`, with a Basic Node
`Worker` between them.

**Step 3: Wire: Start → LogStart → Worker → LogEnd → Stop.**

**Step 4: Set `message` properties:**
- `LogStart.message` = `"Pipeline starting — input: {{input_value}}"`
- `LogEnd.message` = `"Pipeline complete — result: {{result_value}}"`

**Step 5: Paste the code:**

```python
# LogStart
from pocketflow import Node

class LogStart(Node):
    def prep(self, shared):
        return shared.get("input_value", "hello")

    def exec(self, prep_res):
        return f"Pipeline starting — input: {prep_res}"

    def post(self, shared, prep_res, exec_res):
        print(exec_res)   # appears in Run Log
        return "default"
```

```python
# Worker
from pocketflow import Node

class Worker(Node):
    def prep(self, shared):
        return shared.get("input_value", "hello")

    def exec(self, prep_res):
        return prep_res.upper()

    def post(self, shared, prep_res, exec_res):
        shared["result_value"] = exec_res
        return "default"
```

```python
# LogEnd — same pattern, reads result_value
from pocketflow import Node

class LogEnd(Node):
    def prep(self, shared):
        return shared.get("result_value", "")

    def exec(self, prep_res):
        return f"Pipeline complete — result: {prep_res}"

    def post(self, shared, prep_res, exec_res):
        print(exec_res)
        return "default"
```

**Step 6: Run and view the Run Log tab.**

### What you learned

- Log Nodes are zero-logic nodes — they exist solely to emit observability data
- Insert them at any point without altering data flow; they pass control straight through
- The `message` template uses `{{key}}` interpolation to include live shared-store values

---

## Tutorial T-N56: Timer Node

### What it does

The **Timer Node** records timestamps and optionally introduces a `sleep` delay. A
`start` operation stores the current time; a `stop` operation computes elapsed
milliseconds. Use it to measure how long a pipeline stage takes.

### Use cases

- Benchmarking which node is the bottleneck in a flow
- Enforcing minimum delays between API calls (rate-limit courtesy)
- Logging SLA compliance: flag runs that exceed a duration threshold

### What you'll build

A timed processing flow that measures how long a simulated LLM call takes.

### Step-by-step

**Step 1: Add two Timer Nodes** named `TimerStart` and `TimerStop`, with a Basic Node
`SlowWorker` between them.

**Step 2: Wire: Start → TimerStart → SlowWorker → TimerStop → Stop.**

**Step 3: Set `operation`:**
- `TimerStart.operation` = `start`, `TimerStart.label` = `llm_call`
- `TimerStop.operation` = `stop`, `TimerStop.label` = `llm_call`

**Step 4: Paste the code:**

```python
# TimerStart
import time
from pocketflow import Node

class TimerStart(Node):
    LABEL = "llm_call"

    def prep(self, shared):
        return self.LABEL

    def exec(self, prep_res):
        return time.monotonic()

    def post(self, shared, prep_res, exec_res):
        shared[f"timer_{prep_res}_start"] = exec_res
        return "default"
```

```python
# SlowWorker — simulates a 0.1 s LLM call
import time
from pocketflow import Node

class SlowWorker(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        time.sleep(0.1)
        return "done"

    def post(self, shared, prep_res, exec_res):
        return "default"
```

```python
# TimerStop
import time
from pocketflow import Node

class TimerStop(Node):
    LABEL = "llm_call"

    def prep(self, shared):
        return shared.get(f"timer_{self.LABEL}_start", 0.0)

    def exec(self, prep_res):
        elapsed_ms = (time.monotonic() - prep_res) * 1000
        return round(elapsed_ms, 2)

    def post(self, shared, prep_res, exec_res):
        shared[f"timer_{self.LABEL}_ms"] = exec_res
        return "default"
```

**Step 5: Run and inspect:**

```
timer_llm_call_ms: 101.4
```

### What you learned

- Timer Nodes use the shared store as a scratchpad for timing state
- `label` allows multiple independent timers in the same flow
- Add a Condition Node after `TimerStop` to alert when elapsed time exceeds a threshold

---

## Tutorial T-N57: Cache Node

### What it does

The **Cache Node** stores a value in an in-memory (or persistent) key-value cache
and, on subsequent calls with the same cache key, returns the cached value instead of
re-computing. This avoids repeating expensive LLM calls or API fetches during
development or when the same input recurs.

### Use cases

- Caching LLM responses for identical prompts during testing
- Avoiding duplicate API calls for the same URL in a web-scraping flow
- Speeding up batch flows by reusing embeddings for duplicate texts

### What you'll build

A Cache Node that skips an "expensive" computation on the second call.

### Step-by-step

**Step 1: Add a Cache Node** named `ResultCache`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `cache_key_expr` | `shared["query"]` |
| `input_key` | `query` |
| `output_key` | `cached_result` |
| `ttl_seconds` | `300` |

**Step 3: Wire Start → ResultCache → Stop.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

_CACHE: dict = {}

class ResultCache(Node):
    TTL = 300

    def prep(self, shared):
        return shared.get("query", "default_query")

    def exec(self, prep_res):
        key = prep_res
        if key in _CACHE:
            return {"cache_hit": True, "value": _CACHE[key]}
        # Simulate an expensive operation.
        result = f"Computed result for: {key}"
        _CACHE[key] = result
        return {"cache_hit": False, "value": result}

    def post(self, shared, prep_res, exec_res):
        shared["cached_result"] = exec_res["value"]
        shared["cache_hit"] = exec_res["cache_hit"]
        return "default"
```

**Step 5: Run twice with the same `query`.** On the first run `cache_hit: false`;
on the second run `cache_hit: true`.

### What you learned

- Cache Nodes are transparent — they pass the value through on miss and return it directly on hit
- `ttl_seconds` controls expiry; set to `0` for a permanent cache
- Use a Condition Node on `cache_hit` to skip downstream processing entirely on a hit

---

## Tutorial T-N58: Trace Node

### What it does

The **Trace Node** appends a snapshot of the current shared-store state (or a selected
subset of keys) to a running trace list. At the end of the flow the trace shows a
history of how the store evolved, step by step — invaluable for debugging complex
multi-branch flows.

### Use cases

- Recording state before and after each major node for post-run analysis
- Comparing shared-store evolution across two different runs
- Generating audit logs with timestamped state snapshots

### What you'll build

A trace that captures state at three points in a processing flow.

### Step-by-step

**Step 1: Insert Trace Nodes** at the start, middle, and end of any existing flow
(reuse the Worker flow from T-N55).

**Step 2: Set `trace_key`** = `"flow_trace"` on all three.

**Step 3: Paste representative code (same for all three, shown once):**

```python
import time
from pocketflow import Node

class TracePoint(Node):
    LABEL = "step_1"   # change per instance

    def prep(self, shared):
        return dict(shared)   # snapshot the full store

    def exec(self, prep_res):
        return {
            "label": self.LABEL,
            "timestamp": time.time(),
            "state": prep_res,
        }

    def post(self, shared, prep_res, exec_res):
        trace = shared.get("flow_trace", [])
        trace.append(exec_res)
        shared["flow_trace"] = trace
        return "default"
```

**Step 4: Run and inspect `flow_trace`** — a list of timestamped snapshots.

### What you learned

- Trace Nodes accumulate a list rather than overwriting — the full history is preserved
- Snapshots include a label so you know which node in the flow produced each entry
- Keep Trace Nodes in debug mode and remove them (or set a flag) for production runs

---

## Tutorial T-N59: Registry Node

### What it does

The **Registry Node** maintains a persistent, named key-value store (separate from the
main shared store) that survives across flow runs. Use it to accumulate state that
must outlive a single execution — counters, accumulated metrics, or a running log.

### Use cases

- Counting how many flows have run successfully across all executions
- Storing the last-seen record ID for an incremental data-ingestion flow
- Keeping a running total of tokens consumed for budget tracking

### What you'll build

A Registry Node that increments a `run_count` across repeated runs.

### Step-by-step

**Step 1: Add a Registry Node** named `RunCounter`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `operation` | `increment` |
| `registry_key` | `run_count` |
| `output_key` | `run_count` |

**Step 3: Wire Start → RunCounter → Stop.**

**Step 4: Paste the code:**

```python
import json, os
from pocketflow import Node

_REGISTRY_FILE = ".flow_registry.json"

def _load():
    if os.path.exists(_REGISTRY_FILE):
        with open(_REGISTRY_FILE) as f:
            return json.load(f)
    return {}

def _save(data):
    with open(_REGISTRY_FILE, "w") as f:
        json.dump(data, f)

class RunCounter(Node):
    KEY = "run_count"

    def prep(self, shared):
        return _load()

    def exec(self, prep_res):
        registry = prep_res
        registry[self.KEY] = registry.get(self.KEY, 0) + 1
        _save(registry)
        return registry[self.KEY]

    def post(self, shared, prep_res, exec_res):
        shared["run_count"] = exec_res
        return "default"
```

**Step 5: Run three times** and confirm `run_count` increments: 1, 2, 3.

### What you learned

- Registry Nodes persist state in a sidecar file (or a database) — the shared store alone is ephemeral
- Use `operation: set` to overwrite, `operation: get` to read without writing, `operation: delete` to remove
- Combine with a Condition Node to trigger cleanup after N runs

---

## Tutorial T-N60 & T-N61: Stack Push and Stack Pop Nodes

### What they do

The **Stack Push Node** pushes a value onto a named LIFO stack in the shared store.
The **Stack Pop Node** removes and returns the top item. Together they implement
depth-first traversal, undo stacks, or backtracking search patterns.

### What you'll build

A stack-based flow that pushes three items and pops them in LIFO order.

### Step-by-step

**Step 1: Wire three Stack Push Nodes (`Push1`, `Push2`, `Push3`) followed by three
Stack Pop Nodes (`Pop1`, `Pop2`, `Pop3`), all on the same stack named `"my_stack"`.**

**Step 2: Representative Push code (same for all three, push different values):**

```python
from pocketflow import Node

class Push1(Node):
    VALUE = "first"
    STACK = "my_stack"

    def prep(self, shared):
        return shared.get(self.STACK, [])

    def exec(self, prep_res):
        return prep_res + [self.VALUE]

    def post(self, shared, prep_res, exec_res):
        shared[self.STACK] = exec_res
        return "default"
```

**Step 3: Representative Pop code:**

```python
from pocketflow import Node

class Pop1(Node):
    STACK = "my_stack"
    OUTPUT = "pop1_value"

    def prep(self, shared):
        return shared.get(self.STACK, [])

    def exec(self, prep_res):
        if not prep_res:
            return ([], None)
        return (prep_res[:-1], prep_res[-1])

    def post(self, shared, prep_res, exec_res):
        stack, value = exec_res
        shared[self.STACK] = stack
        shared[self.OUTPUT] = value
        return "default"
```

**Step 4: Run and inspect:**

```
my_stack: []              (empty after three pops)
pop1_value: "third"       (LIFO: last pushed is first popped)
pop2_value: "second"
pop3_value: "first"
```

### What you learned

- Stack Push/Pop Nodes implement LIFO order — Push three, Pop gets them in reverse
- The stack itself lives in the shared store as a plain list
- Use a Condition Node on stack length to loop until empty for stack-draining workflows

---

## Tutorial T-N62 & T-N63: Queue Enqueue and Queue Dequeue Nodes

### What they do

The **Queue Enqueue Node** appends a value to a named FIFO queue. The **Queue
Dequeue Node** removes and returns the front item. Use them for ordered work queues,
breadth-first traversal, or producer-consumer patterns within a single flow.

### What you'll build

A queue that processes three tasks in FIFO order.

### Step-by-step

**Step 1: Wire three Enqueue Nodes then three Dequeue Nodes on queue `"task_queue"`.**

**Step 2: Representative Enqueue code:**

```python
from pocketflow import Node

class Enqueue1(Node):
    TASK = {"id": 1, "action": "send_email"}
    QUEUE = "task_queue"

    def prep(self, shared):
        return shared.get(self.QUEUE, [])

    def exec(self, prep_res):
        return prep_res + [self.TASK]

    def post(self, shared, prep_res, exec_res):
        shared[self.QUEUE] = exec_res
        return "default"
```

**Step 3: Representative Dequeue code:**

```python
from pocketflow import Node

class Dequeue1(Node):
    QUEUE = "task_queue"
    OUTPUT = "dequeued_task_1"

    def prep(self, shared):
        return shared.get(self.QUEUE, [])

    def exec(self, prep_res):
        if not prep_res:
            return ([], None)
        return (prep_res[1:], prep_res[0])

    def post(self, shared, prep_res, exec_res):
        queue, task = exec_res
        shared[self.QUEUE] = queue
        shared[self.OUTPUT] = task
        return "default"
```

**Step 4: Run and confirm FIFO ordering:**

```
dequeued_task_1: {"id": 1, "action": "send_email"}
dequeued_task_2: {"id": 2, ...}
dequeued_task_3: {"id": 3, ...}
```

### What you learned

- Queues are FIFO; stacks are LIFO — choose based on the required traversal order
- Both Queue and Stack nodes store their data in the shared store as plain Python lists
- Combine an Enqueue phase (data collection) with a Loop Counter + Dequeue phase (processing)

---

## Tutorial T-N64: Local Memory Node

### What it does

The **Local Memory Node** manages a short-term scratchpad local to a single flow
run — separate from the main shared store. It supports `write`, `read`, `append`, and
`clear` operations. Unlike the Registry Node, it does not persist across runs.

### Use cases

- Storing intermediate results you do not want to expose in the main shared store
- Buffering a multi-step LLM context before the final prompt is assembled
- Keeping node-local state without polluting the shared namespace

### What you'll build

A Local Memory Node that builds up a context buffer across three passes.

### Step-by-step

**Step 1: Add a Local Memory Node** named `ContextBuffer`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `operation` | `append` |
| `memory_key` | `context_buffer` |
| `input_key` | `new_context` |
| `output_key` | `context_buffer` |

**Step 3: Wire Start → ContextBuffer → Stop.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

class ContextBuffer(Node):
    KEY = "context_buffer"

    def prep(self, shared):
        return {
            "existing": shared.get(self.KEY, []),
            "new": shared.get("new_context", "No new context"),
        }

    def exec(self, prep_res):
        buffer = list(prep_res["existing"])
        buffer.append(prep_res["new"])
        return buffer

    def post(self, shared, prep_res, exec_res):
        shared[self.KEY] = exec_res
        return "default"
```

**Step 5: Pre-seed `new_context`** with different values and run three times,
observing the buffer grow.

### What you learned

- Local Memory Nodes give you a named, appendable buffer distinct from individual shared-store keys
- `operation: clear` resets the buffer — useful at the start of a retry loop
- The buffer is a regular shared-store list; any node can read it with `shared.get("context_buffer")`

---

[↑ Series Index](gtkn_index.md)
[← Part 14](gtkn_part14.md)
[→ Part 16: System, Shell, and Hardware Nodes](gtkn_part16.md)
