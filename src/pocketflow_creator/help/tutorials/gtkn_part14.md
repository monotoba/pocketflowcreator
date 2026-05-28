# Part 14 — Calendar and Agent Protocol Nodes

This part covers five nodes: two for reading and writing calendar events, and three
for the emerging agent-protocol layer — MCP Tool calls, and agent-to-agent (A2A)
message passing.

**Prerequisite:** Complete Part 1 (Start / Stop / Basic) before this part.

---

## Tutorial T-N50: Calendar Read Node

### What it does

The **Calendar Read Node** fetches calendar events from Google Calendar, Outlook, or
an iCal feed and stores them as a list of event dicts in the shared store. A date
range (start/end) filters which events are returned.

### Use cases

- Reading today's meetings before an LLM writes a daily briefing
- Checking for scheduling conflicts before a Calendar Write Node creates a new event
- Aggregating cross-calendar availability for scheduling flows

### What you'll build

A flow — **Start → MeetingReader → Stop** — that reads today's events and stores
them in `calendar_events`.

### Step-by-step

**Step 1: Create project `gtkn_part14`.**

**Step 2: Drag a Calendar Read Node** named `MeetingReader`.

**Step 3: Set Inspector properties:**

| Property | Value |
|---|---|
| `calendar_id` | `primary` |
| `start_key` | `cal_start` |
| `end_key` | `cal_end` |
| `output_key` | `calendar_events` |
| `provider` | `google` |

**Step 4: Wire Start → MeetingReader → Stop.**

**Step 5: Paste the code:**

```python
from datetime import date
from pocketflow import Node

class MeetingReader(Node):
    def prep(self, shared):
        return {
            "start": shared.get("cal_start", str(date.today())),
            "end": shared.get("cal_end", str(date.today())),
        }

    def exec(self, prep_res):
        # Production: call Google Calendar API or MSAL for Outlook.
        # Simulation: return two plausible events.
        day = prep_res["start"]
        return [
            {
                "id": "evt_001",
                "title": "Standup",
                "start": f"{day}T09:00:00",
                "end": f"{day}T09:15:00",
                "attendees": ["alice@example.com", "bob@example.com"],
            },
            {
                "id": "evt_002",
                "title": "Sprint Planning",
                "start": f"{day}T14:00:00",
                "end": f"{day}T15:00:00",
                "attendees": ["alice@example.com"],
            },
        ]

    def post(self, shared, prep_res, exec_res):
        shared["calendar_events"] = exec_res
        return "default"
```

**Step 6: Run and inspect `calendar_events`.**

### What you learned

- Calendar Read Nodes abstract provider differences — switch `provider` from `google` to `outlook` without changing logic
- The date range is sourced from the shared store, making it easy to parameterise (e.g. set by a Human Input Node)
- Events are dicts with consistent fields regardless of provider

---

## Tutorial T-N51: Calendar Write Node

### What it does

The **Calendar Write Node** creates, updates, or deletes a calendar event. The event
details (title, start, end, attendees, description) are sourced from the shared store.
On success it writes the created event's ID back for downstream reference.

### Use cases

- Booking a meeting suggested by an LLM scheduling assistant
- Automatically creating reminder events from a task list
- Rescheduling or cancelling events as part of a conflict-resolution flow

### What you'll build

Extend the flow from T-N50: add a Calendar Write Node that creates a new
"Team Retrospective" event after reading existing events.

### Step-by-step

**Step 1: Add a Calendar Write Node** named `EventCreator` after `MeetingReader`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `event_key` | `new_event` |
| `output_key` | `created_event_id` |
| `provider` | `google` |
| `operation` | `create` |

**Step 3: Wire MeetingReader → EventCreator → Stop.**

**Step 4: Update `MeetingReader.post()`** to seed the event to create:

```python
def post(self, shared, prep_res, exec_res):
    shared["calendar_events"] = exec_res
    from datetime import date
    day = prep_res["start"]
    shared["new_event"] = {
        "title": "Team Retrospective",
        "start": f"{day}T16:00:00",
        "end": f"{day}T17:00:00",
        "attendees": ["alice@example.com", "bob@example.com"],
        "description": "End-of-sprint retrospective",
    }
    return "default"
```

**Step 5: Paste the EventCreator code:**

```python
from pocketflow import Node

class EventCreator(Node):
    def prep(self, shared):
        return shared.get("new_event", {})

    def exec(self, prep_res):
        event = prep_res
        if not event.get("title"):
            return None
        # Production: call calendar API to create the event.
        return f"created_evt_{abs(hash(event['title'])) % 10000:04d}"

    def post(self, shared, prep_res, exec_res):
        shared["created_event_id"] = exec_res
        return "default"
```

**Step 6: Run:**

```
created_event_id: "created_evt_7482"
```

### What you learned

- Calendar Write Nodes accept a full event dict from the shared store — build it in a preceding LLM or Basic Node
- `operation: create` returns a new event ID; `operation: update` and `operation: delete` use an existing ID from `event_key`
- Chain Calendar Read → Condition (conflict check) → Calendar Write for a conflict-aware scheduler

---

## Tutorial T-N52: MCP Tool Node

### What it does

The **MCP Tool Node** invokes a registered tool in a Model Context Protocol (MCP)
server. The tool name, arguments, and server URL are configured in the Inspector.
Results are written back to the shared store for the next node to consume.

### Use cases

- Calling a code execution sandbox from an LLM agent flow
- Fetching structured data from a custom MCP data source (files, databases, APIs)
- Integrating any MCP-compatible tool without writing custom HTTP client code

### What you'll build

A flow that calls a fictional `get_weather` MCP tool and stores the result.

### Step-by-step

**Step 1: Add an MCP Tool Node** named `WeatherTool`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `server_url` | `http://localhost:3000/mcp` |
| `tool_name` | `get_weather` |
| `args_key` | `weather_args` |
| `output_key` | `weather_result` |

**Step 3: Wire Start → WeatherTool → Stop.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

class WeatherTool(Node):
    TOOL = "get_weather"

    def prep(self, shared):
        return shared.get("weather_args", {"city": "London", "units": "metric"})

    def exec(self, prep_res):
        # Production: POST to MCP server with tool name + args.
        # Simulation:
        city = prep_res.get("city", "Unknown")
        return {
            "tool": self.TOOL,
            "result": {
                "city": city,
                "temperature_c": 14,
                "condition": "Partly cloudy",
                "humidity_pct": 72,
            },
        }

    def post(self, shared, prep_res, exec_res):
        shared["weather_result"] = exec_res["result"]
        return "default"
```

**Step 5: Run and inspect `weather_result`:**

```
{"city": "London", "temperature_c": 14, "condition": "Partly cloudy", ...}
```

### What you learned

- MCP Tool Nodes standardise external tool calls — the flow logic is the same regardless of which MCP server is used
- `args_key` decouples argument preparation from the tool invocation step
- MCP results integrate naturally with downstream LLM nodes for further reasoning

---

## Tutorial T-N53 & T-N54: A2A Send and A2A Receive Nodes

### What they do

The **A2A Send Node** dispatches a message to another PocketFlow agent running at a
remote endpoint. The **A2A Receive Node** blocks until a message arrives at the
configured endpoint, then stores the payload in the shared store and resumes
execution. Together they implement asynchronous agent-to-agent (A2A) communication.

### Use cases

- Spawning a specialist sub-agent and waiting for its reply
- Building multi-agent pipelines where agents run in separate processes
- Implementing a request/response pattern between a coordinator and worker agents

### What you'll build

A single flow that demonstrates the round-trip: Send a task, then Receive the reply
(simulated inline for the tutorial).

### Step-by-step

**Step 1: Add an A2A Send Node** named `TaskDispatcher` and an A2A Receive Node named
`ReplyListener`.

**Step 2: Configure `TaskDispatcher`:**

| Property | Value |
|---|---|
| `endpoint` | `http://localhost:8001/a2a` |
| `payload_key` | `task_payload` |
| `message_id_key` | `msg_id` |

**Step 3: Configure `ReplyListener`:**

| Property | Value |
|---|---|
| `endpoint` | `http://localhost:8001/a2a/reply` |
| `output_key` | `agent_reply` |
| `timeout` | `30` |

**Step 4: Wire: Start → TaskDispatcher → ReplyListener → Stop.**

**Step 5: Paste the code:**

```python
# TaskDispatcher
import uuid
from pocketflow import Node

class TaskDispatcher(Node):
    def prep(self, shared):
        shared.setdefault(
            "task_payload",
            {"task": "summarise", "text": "PocketFlow is a minimalist LLM framework."},
        )
        return shared["task_payload"]

    def exec(self, prep_res):
        # Production: POST payload to the remote A2A endpoint.
        msg_id = str(uuid.uuid4())[:8]
        return msg_id

    def post(self, shared, prep_res, exec_res):
        shared["msg_id"] = exec_res
        return "default"
```

```python
# ReplyListener
from pocketflow import Node

class ReplyListener(Node):
    def prep(self, shared):
        return shared.get("msg_id", "")

    def exec(self, prep_res):
        # Production: poll or long-poll the A2A reply endpoint.
        return {
            "msg_id": prep_res,
            "status": "done",
            "result": "PocketFlow is a small, readable LLM framework for building agents.",
        }

    def post(self, shared, prep_res, exec_res):
        shared["agent_reply"] = exec_res
        return "default"
```

**Step 6: Run and inspect:**

```
msg_id: "a3f7c2b1"
agent_reply: {"status": "done", "result": "PocketFlow is a small, readable..."}
```

### What you learned

- A2A Send writes a message and stores a correlation ID; A2A Receive blocks on that ID
- The timeout on Receive prevents flows from hanging indefinitely when remote agents fail
- Pair with a Condition Node after Receive to handle `status: error` gracefully

---

[↑ Series Index](gtkn_index.md)
[← Part 13](gtkn_part13.md)
[→ Part 15: Observability and Data Structure Nodes](gtkn_part15.md)
