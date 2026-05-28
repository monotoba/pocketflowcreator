# Part 18 — AI/LLM Utility and Text Processing Nodes

This part covers seven nodes that work with LLM context management and structured
text/data manipulation: Context Compact, Conversation History, Regex, Template Render,
JSON Parse, List Operations, and String Operations.

**Prerequisite:** Complete Part 4 (LLM Nodes) for context on LLM prompting patterns.

---

## Tutorial T-N71: Context Compact Node

### What it does

The **Context Compact Node** reduces a long text (typically an LLM conversation or
document) to fit within a token budget. Five strategies are available:

| Strategy | How it works |
|---|---|
| `truncate` | Keep the first N tokens |
| `sliding_window` | Keep the last N tokens (most recent context) |
| `summarize` | Call an LLM to summarise the text |
| `extractive` | Extract the top-ranked sentences by TF-IDF score |
| `semantic_dedup` | Remove near-duplicate sentences by embedding cosine similarity |

### Use cases

- Keeping a conversation history within the LLM's context window
- Compressing a large retrieved document before feeding it to a prompt
- Removing boilerplate and repeated paragraphs from scraped text

### What you'll build

A flow that uses the `sliding_window` strategy to keep only the last 200 characters
of a long conversation.

### Step-by-step

**Step 1: Create project `gtkn_part18`.**

**Step 2: Drag a Context Compact Node** named `ContextCompactor`.

**Step 3: Set Inspector properties:**

| Property | Value |
|---|---|
| `input_key` | `long_context` |
| `output_key` | `compact_context` |
| `strategy` | `sliding_window` |
| `max_tokens` | `200` |

**Step 4: Wire Start → ContextCompactor → Stop.**

**Step 5: Paste the code:**

```python
from pocketflow import Node

class ContextCompactor(Node):
    STRATEGY = "sliding_window"
    MAX_CHARS = 200   # approximate; real impl uses a tokeniser

    def prep(self, shared):
        return shared.get(
            "long_context",
            "Turn 1: User asked about PocketFlow. " * 5
            + "Turn 2: Assistant explained nodes. " * 5
            + "Turn 3: User asked about RAG. "
            + "Turn 4: Assistant explained chunking and embeddings.",
        )

    def exec(self, prep_res):
        text = prep_res
        if self.STRATEGY == "truncate":
            return text[: self.MAX_CHARS]
        if self.STRATEGY == "sliding_window":
            return text[-self.MAX_CHARS :]
        if self.STRATEGY == "extractive":
            # Keep sentences that contain key terms.
            sentences = text.split(". ")
            key = "RAG"
            return ". ".join(s for s in sentences if key in s or len(s) < 40)
        # Default: truncate
        return text[: self.MAX_CHARS]

    def post(self, shared, prep_res, exec_res):
        shared["compact_context"] = exec_res
        return "default"
```

**Step 6: Run and confirm** `compact_context` contains only the last 200 characters
of `long_context`.

### What you learned

- Swapping strategies changes behaviour without rewiring the flow — just edit the `strategy` property
- `sliding_window` preserves the most recent context, which matters for conversational flows
- `summarize` calls a secondary LLM; `extractive` and `semantic_dedup` are compute-only strategies

---

## Tutorial T-N72: Conversation History Node

### What it does

The **Conversation History Node** maintains a running list of `{"role": ..., "content": ...}`
message dicts in the shared store. Operations: `append` (add a turn), `trim` (remove
oldest turns beyond a limit), `clear` (empty the history), `format` (serialise to a
plain string for an LLM prompt).

### Use cases

- Building multi-turn chatbot flows where each response depends on prior turns
- Trimming history to stay within token limits without losing the most recent context
- Formatting message history into a prompt for an LLM that doesn't accept chat format

### What you'll build

A flow that appends three turns to a conversation and then formats the history for an
LLM prompt.

### Step-by-step

**Step 1: Add two Conversation History Nodes:** `TurnAppender` (operation `append`)
and `HistoryFormatter` (operation `format`).

**Step 2: Wire: Start → TurnAppender → HistoryFormatter → Stop.**

**Step 3: Paste the code:**

```python
# TurnAppender
from pocketflow import Node

class TurnAppender(Node):
    def prep(self, shared):
        return shared.get("conversation_history", [])

    def exec(self, prep_res):
        history = list(prep_res)
        history.append({"role": "user", "content": "What is PocketFlow?"})
        history.append({"role": "assistant", "content": "A minimalist LLM framework."})
        history.append({"role": "user", "content": "How does RAG work?"})
        return history

    def post(self, shared, prep_res, exec_res):
        shared["conversation_history"] = exec_res
        return "default"
```

```python
# HistoryFormatter
from pocketflow import Node

class HistoryFormatter(Node):
    def prep(self, shared):
        return shared.get("conversation_history", [])

    def exec(self, prep_res):
        lines = []
        for turn in prep_res:
            role = turn.get("role", "unknown").capitalize()
            content = turn.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def post(self, shared, prep_res, exec_res):
        shared["formatted_history"] = exec_res
        return "default"
```

**Step 4: Run and inspect `formatted_history`:**

```
User: What is PocketFlow?
Assistant: A minimalist LLM framework.
User: How does RAG work?
```

### What you learned

- Conversation History Nodes decouple history management from LLM calls — the history key is reused across turns
- `trim` removes the oldest turns first, preserving the system prompt (index 0) if present
- `format` converts the list to a plain string for LLMs that expect a single text input

---

## Tutorial T-N73: Regex Node

### What it does

The **Regex Node** applies a regular expression to a text value from the shared store.
Operations: `match` (anchored at start), `search` (anywhere in string), `findall`
(list of all matches), `replace` (substitute), `split` (split on pattern).

### Use cases

- Extracting email addresses or phone numbers from unstructured text
- Cleaning LLM output by removing markdown fences or special tokens
- Validating that a string matches an expected pattern

### What you'll build

A flow that extracts all email addresses from a block of text.

### Step-by-step

**Step 1: Add a Regex Node** named `EmailExtractor`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `input_key` | `raw_text` |
| `output_key` | `emails` |
| `pattern` | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` |
| `operation` | `findall` |

**Step 3: Wire Start → EmailExtractor → Stop.**

**Step 4: Paste the code:**

```python
import re
from pocketflow import Node

EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

class EmailExtractor(Node):
    def prep(self, shared):
        return shared.get(
            "raw_text",
            "Contact alice@example.com or bob@work.org for support. "
            "Spam goes to noreply@nowhere.invalid.",
        )

    def exec(self, prep_res):
        return re.findall(EMAIL_PATTERN, prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["emails"] = exec_res
        return "default"
```

**Step 5: Run:**

```
emails: ["alice@example.com", "bob@work.org", "noreply@nowhere.invalid"]
```

### What you learned

- Regex Nodes keep pattern logic in the Inspector — change the pattern without editing code
- `findall` returns a list; `replace` returns a modified string; `split` returns a list of substrings
- Combine with a Condition Node to validate format: `operation: match`, then route on non-null result

---

## Tutorial T-N74: Template Render Node

### What it does

The **Template Render Node** renders a Jinja2 template (inline string or `.j2` file)
using variables sourced from the shared store. The rendered string is written to an
output key. This is the standard way to build complex, reusable LLM prompts that
incorporate dynamic data.

### Use cases

- Building LLM prompts from templates with multiple variable substitutions
- Generating HTML or Markdown reports from flow results
- Constructing SQL queries with safe variable interpolation

### What you'll build

A flow that renders a customer-email template with data from the shared store.

### Step-by-step

**Step 1: Add a Template Render Node** named `EmailComposer`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `template` | _(inline template — see code)_ |
| `context_key` | `email_context` |
| `output_key` | `rendered_email` |

**Step 3: Wire Start → EmailComposer → Stop.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

TEMPLATE = """\
Subject: Your order #{{ order_id }} has shipped

Hi {{ customer_name }},

Your order of {{ item_count }} item(s) has been dispatched.
Estimated delivery: {{ delivery_date }}.

Thank you for shopping with us!
"""

class EmailComposer(Node):
    def prep(self, shared):
        return shared.get(
            "email_context",
            {
                "order_id": "ORD-20240528",
                "customer_name": "Alice",
                "item_count": 3,
                "delivery_date": "2024-06-02",
            },
        )

    def exec(self, prep_res):
        try:
            from jinja2 import Template
            return Template(TEMPLATE).render(**prep_res)
        except ImportError:
            # Fallback: manual substitution
            result = TEMPLATE
            for k, v in prep_res.items():
                result = result.replace("{{ " + k + " }}", str(v))
            return result

    def post(self, shared, prep_res, exec_res):
        shared["rendered_email"] = exec_res
        return "default"
```

**Step 5: Run and inspect `rendered_email`** — a fully rendered email string.

### What you learned

- Template Render Nodes cleanly separate template logic from data — change the template file without touching flow code
- Jinja2's full power (loops, conditionals, filters) is available in inline templates
- Feed the rendered string directly into a Text to Speech Node or Email Send Node

---

## Tutorial T-N75: JSON Parse Node

### What it does

The **JSON Parse Node** converts between a JSON string and a Python dict/list. The
`parse` operation decodes a JSON string to a Python object; the `serialize` operation
encodes a Python object to a JSON string. The `extract` operation parses and then
applies a dotted path (e.g. `results.0.title`) to navigate nested structures.

### Use cases

- Parsing the JSON response body from an API Call Node
- Extracting a specific field from a deeply nested JSON structure
- Serialising a result dict to a JSON string before writing to a file

### What you'll build

A flow that parses a JSON API response and extracts the first result's title.

### Step-by-step

**Step 1: Add a JSON Parse Node** named `ResponseParser`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `input_key` | `raw_json` |
| `output_key` | `parsed_data` |
| `operation` | `parse` |
| `path` | `results.0.title` |

**Step 3: Wire Start → ResponseParser → Stop.**

**Step 4: Paste the code:**

```python
import json
from pocketflow import Node

class ResponseParser(Node):
    PATH = "results.0.title"

    def prep(self, shared):
        return shared.get(
            "raw_json",
            '{"results": [{"title": "PocketFlow Intro", "score": 0.95}, '
            '{"title": "Advanced RAG", "score": 0.82}]}',
        )

    def exec(self, prep_res):
        data = json.loads(prep_res)
        # Navigate dotted path
        current = data
        for part in self.PATH.split("."):
            if isinstance(current, list):
                current = current[int(part)]
            else:
                current = current[part]
        return {"full": data, "extracted": current}

    def post(self, shared, prep_res, exec_res):
        shared["parsed_data"] = exec_res["full"]
        shared["extracted_title"] = exec_res["extracted"]
        return "default"
```

**Step 5: Run:**

```
extracted_title: "PocketFlow Intro"
parsed_data: {"results": [...]}
```

### What you learned

- JSON Parse Nodes turn opaque strings into navigable Python structures
- The `path` property (dotted notation) extracts specific fields without custom code
- `operation: serialize` is the inverse — useful before writing to a file or sending over HTTP

---

## Tutorial T-N76: List Operations Node

### What it does

The **List Operations Node** applies a single list transformation to a shared-store
value. Operations: `filter` (keep items matching a condition), `sort` (ascending/
descending, with optional key), `slice` (start:end:step), `unique` (deduplicate),
`flatten` (one level deep), `reverse`, `count`.

### Use cases

- Deduplicating search result URLs before scraping
- Sorting LLM candidate answers by confidence score
- Slicing a paginated result list to the first page

### What you'll build

A flow that deduplicates and sorts a list of scores.

### Step-by-step

**Step 1: Add two List Operations Nodes:** `Deduper` (operation `unique`) and
`Sorter` (operation `sort`).

**Step 2: Wire Start → Deduper → Sorter → Stop.**

**Step 3: Paste the code:**

```python
# Deduper
from pocketflow import Node

class Deduper(Node):
    def prep(self, shared):
        return shared.get("scores", [4, 7, 2, 7, 4, 9, 2, 5])

    def exec(self, prep_res):
        return list(dict.fromkeys(prep_res))   # preserves order

    def post(self, shared, prep_res, exec_res):
        shared["scores"] = exec_res
        return "default"
```

```python
# Sorter
from pocketflow import Node

class Sorter(Node):
    REVERSE = True   # descending

    def prep(self, shared):
        return shared.get("scores", [])

    def exec(self, prep_res):
        return sorted(prep_res, reverse=self.REVERSE)

    def post(self, shared, prep_res, exec_res):
        shared["sorted_scores"] = exec_res
        return "default"
```

**Step 4: Run:**

```
scores (after dedup): [4, 7, 2, 9, 5]
sorted_scores: [9, 7, 5, 4, 2]
```

### What you learned

- List Operations Nodes chain naturally — each one takes an input key and writes an output key
- `unique` uses insertion-order deduplication (no sorting side-effect)
- For complex pipelines, prefer Map + Reduce over a long chain of List Operations Nodes

---

## Tutorial T-N77: String Operations Node

### What it does

The **String Operations Node** applies a single string transformation. Operations:
`split`, `join`, `strip`, `upper`, `lower`, `replace`, `format` (printf-style or
str.format), `truncate` (with optional ellipsis).

### Use cases

- Normalising model output: strip whitespace, lowercase before classification
- Splitting a comma-separated string into a list for a downstream Map Node
- Truncating a generated summary to fit in an SMS or notification

### What you'll build

A flow that cleans and truncates an LLM response for display.

### Step-by-step

**Step 1: Add two String Operations Nodes:** `Stripper` (operation `strip`) and
`Truncator` (operation `truncate`).

**Step 2: Wire Start → Stripper → Truncator → Stop.**

**Step 3: Configure `Truncator`:** `max_length = 80`, `ellipsis = "…"`.

**Step 4: Paste the code:**

```python
# Stripper
from pocketflow import Node

class Stripper(Node):
    def prep(self, shared):
        return shared.get(
            "raw_response",
            "  \n  PocketFlow is a minimalist LLM framework for building "
            "agents and workflows. It is designed to be small and readable.  \n  ",
        )

    def exec(self, prep_res):
        return prep_res.strip()

    def post(self, shared, prep_res, exec_res):
        shared["clean_response"] = exec_res
        return "default"
```

```python
# Truncator
from pocketflow import Node

class Truncator(Node):
    MAX_LEN = 80
    ELLIPSIS = "…"

    def prep(self, shared):
        return shared.get("clean_response", "")

    def exec(self, prep_res):
        text = prep_res
        if len(text) <= self.MAX_LEN:
            return text
        return text[: self.MAX_LEN - len(self.ELLIPSIS)] + self.ELLIPSIS

    def post(self, shared, prep_res, exec_res):
        shared["display_response"] = exec_res
        return "default"
```

**Step 5: Run:**

```
display_response: "PocketFlow is a minimalist LLM framework for building agents and…"
```

### What you learned

- String Operations Nodes are pipeline steps — chain Strip → Truncate → Upper as needed
- `truncate` ensures display strings fit constrained outputs (notifications, SMS, tooltips)
- `split` returns a list, making it easy to feed a comma-separated value into a Map Node

---

[↑ Series Index](gtkn_index.md)
[← Part 17](gtkn_part17.md)
[→ Part 19: Resilience, Messaging, and Security Nodes](gtkn_part19.md)
