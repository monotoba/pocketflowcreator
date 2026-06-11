# Tutorial: Exporting Standalone Python Scripts

**What you'll learn:** Export a PocketFlow graph as a self-contained Python script with no framework dependencies.

**Prerequisites:** Tutorial 1 (IDE Tour), Tutorial 2 (Your First Flow)

---

## Why Standalone Scripts?

PocketFlow Creator normally exports a Python package with template stubs. But sometimes you need:
- **A single `.py` file** that runs the flow independently
- **No PocketFlow framework** required to run
- **No `pip install` needed** beyond stdlib (optional external libs detected at runtime)
- **Embedded provider implementations** (Ollama, OpenAI, Anthropic, Gemini, DeepSeek)

When you export a standalone script, you get exactly that.

---

## Step 1: Create a Simple Flow

1. **New Project** → File > New Project…
   - Name: `sentiment_analyzer`
   - Create a graph called `analyze_sentiment.pfcgraph.yaml`

2. **Add nodes** to the canvas:
   - **Start Node** → position at left
   - **LLM Prompt Node** → center
   - **Stop Node** → right

3. **Wire edges**
   - Start → LLM Prompt (action: `default`)
   - LLM Prompt → Stop (action: `default`)

4. **Configure LLM Prompt Node** (in Object Inspector):
   - `prompt_file`: `Analyze this text and rate sentiment 1–10: {{input}}`
   - `output_key`: `result`
   - `input_key`: `input`

5. **Configure provider**
   - Tools > Provider Manager
   - Add an Ollama provider (or OpenAI, Anthropic, etc.)
   - Set as default or wire to the LLM node

---

## Step 2: Export as Standalone Script

1. **File > Export PocketFlow Project**
   - Location: any folder
   - Click **Export**

2. **Check the export folder**
   ```
   exports/sentiment_analyzer/
   ├── generated/          # Framework-based Python package
   │   ├── analyze_sentiment_nodes.py
   │   ├── analyze_sentiment_flow.py
   │   └── __init__.py
   ├── custom/
   ├── tests/
   ├── standalone/         # ← NEW: Self-contained scripts
   │   ├── analyze_sentiment_standalone.py
   │   └── __init__.py
   └── main.py
   ```

3. **Open the standalone script**
   ```bash
   cat exports/sentiment_analyzer/standalone/analyze_sentiment_standalone.py
   ```

---

## Step 3: What's Inside the Standalone Script

The generated script contains:

### 1. **Imports** (stdlib only)
```python
import copy
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
```

### 2. **Embedded Provider Classes**
```python
# ── Provider Classes ─────────────────────────────────────────────────────

class OllamaProvider:
    """Ollama-compatible LLM provider (full implementation included)."""
    def __init__(self, base_url, default_model, timeout):
        ...
    
    def complete(self, prompt, model=None):
        ...

class OpenAIProvider:
    """OpenAI-compatible LLM provider (full implementation included)."""
    ...
```

### 3. **Provider Instances**
```python
# ── Provider Instances ───────────────────────────────────────────────────

_provider_local_ollama = OllamaProvider(
    base_url="http://localhost:11434",
    default_model="qwen2.5-coder:14b",
    timeout=120,
)

# Cloud provider keys loaded from environment:
# export OPENAI_API_KEY="sk-..."
_provider_openai = OpenAIProvider(
    api_key=os.environ.get("OPENAI_API_KEY", ""),
    base_url="https://api.openai.com/v1",
    default_model="gpt-4o-mini",
    timeout=120,
)
```

### 4. **Graph Definition**
```python
# ── Graph data ───────────────────────────────────────────────────────────

_START = "start-node-1"

_NODES = {
    "start-node-1": {
        "type": "start_node",
        "title": "Start",
        "props": {},
        "provider": None,
    },
    "llm-node-1": {
        "type": "llm_prompt_node",
        "title": "Analyze Sentiment",
        "props": {
            "prompt_file": "Analyze sentiment...",
            "output_key": "result",
        },
        "provider": _provider_local_ollama,
    },
    ...
}

_EDGES = [
    {"from": "start-node-1", "action": "default", "to": "llm-node-1"},
    {"from": "llm-node-1", "action": "default", "to": "stop-node-1"},
]
```

### 5. **Node Dispatch** (execution logic)
```python
# ── Node Dispatch ──────────────────────────────────────────────────────

def _run_node(node_id, node, shared, outgoing_actions):
    """Execute the specified node; return the action to take next."""
    node_type = node["type"]
    
    if node_type == "start_node":
        return "default"
    
    elif node_type == "llm_prompt_node":
        provider = node["provider"]
        prompt = node["props"]["prompt_file"]
        # Interpolate variables from shared store
        for key, val in shared.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", str(val))
        result = provider.complete(prompt)
        shared[node["props"]["output_key"]] = result
        return "default"
    
    elif node_type == "stop_node":
        return ""
```

### 6. **Flow Runner**
```python
# ── Flow Runner ───────────────────────────────────────────────────────

def run_flow(shared=None):
    """Execute the flow and return the final shared store state."""
    shared = dict(shared or {})
    
    edge_map = {}
    for edge in _EDGES:
        if edge["from"] not in edge_map:
            edge_map[edge["from"]] = []
        edge_map[edge["from"]].append(edge)
    
    current_node_id = _START
    visited = 0
    
    while current_node_id and visited < 200:
        node = _NODES.get(current_node_id)
        if not node:
            break
        visited += 1
        
        outgoing = edge_map.get(current_node_id, [])
        chosen_action = _run_node(current_node_id, node, shared, outgoing)
        
        next_edge = next(
            (e for e in outgoing if e["action"] == chosen_action),
            outgoing[0] if outgoing else None,
        )
        current_node_id = next_edge["to"] if next_edge else ""
    
    return shared


if __name__ == "__main__":
    result = run_flow({"input": "The food was terrible."})
    print(json.dumps(result, indent=2, default=str))
```

---

## Step 4: Run the Standalone Script

### **Scenario A: Local Ollama**
```bash
# With Ollama running locally on port 11434
python exports/sentiment_analyzer/standalone/analyze_sentiment_standalone.py

# Output:
# {
#   "input": "The food was terrible.",
#   "result": "Sentiment: 2/10 (very negative)"
# }
```

### **Scenario B: Cloud Provider**
```bash
# With OpenAI API key
export OPENAI_API_KEY="sk-..."
python exports/sentiment_analyzer/standalone/analyze_sentiment_standalone.py

# Output:
# {
#   "input": "The food was terrible.",
#   "result": "Sentiment Rating: 1/10\nAnalysis: Strongly negative..."
# }
```

### **Scenario C: Modify Shared Store at Runtime**
```python
# In Python
from sentiment_analyzer_standalone import run_flow

result = run_flow({
    "input": "This product exceeded all expectations!"
})
print(result["result"])  # "Sentiment: 9/10 (very positive)"
```

---

## Step 4b: Interactive Nodes (Human Input / Review)

If your flow includes **Human Input Node** or **Human Review Node**, the standalone script uses stdin/stdout/stderr:

### Human Input Node Example
```bash
# Prompts on stdout, reads from stdin
python script.py
[Human Input Node] Enter your name:
> Alice

# Piped input
echo "Alice" | python script.py

# From file
python script.py < names.txt > results.txt
```

### Human Review Node Example
```bash
# Displays content on stdout, reads approval from stdin
python script.py
[Human Review Node] Review this:
The quick brown fox jumps over the lazy dog
Approve? [y/n]: y

# Non-interactive (handles EOF gracefully)
python script.py < /dev/null  # No crash, sets action to 'rejected'
```

### I/O Redirection in CI/CD
```bash
# Jenkins/GitHub Actions/GitLab CI
python script.py < input.txt > output.json 2> errors.log

# Shell script
#!/bin/bash
cat << EOF | python script.py > results.json
approval_input
EOF

# With timeout
timeout 30 python script.py < input.txt
```

**Key Points:**
- ✅ **stdin** for user input (Human Input Node, Human Review Node)
- ✅ **stdout** for prompts and flow output
- ✅ **stderr** for errors (automatically captured)
- ✅ **EOF handling** — gracefully sets action to "cancelled" if input EOF reached
- ✅ **Works in pipelines** — no GUI dialogs, pure text I/O

---

## Step 5: Error Handling for Missing Dependencies

Some nodes require external libraries. The standalone script checks for them at runtime:

```python
# If beautifulsoup4 is missing:
$ python script.py

ERROR in Web Scrape Node: web_scrape_node requires beautifulsoup4: pip install beautifulsoup4
```

You can then install and re-run:
```bash
pip install beautifulsoup4
python script.py
```

---

## Supported Features in Standalone Scripts

**All 91+ node types are fully supported in standalone scripts.**

Below is a breakdown by category showing what external dependencies (if any) each category requires:

| Category | Nodes | Requires |
|----------|-------|----------|
| **Flow Control** | start, stop, basic, router, subflow | stdlib only |
| **LLM / Reasoning** | llm_prompt, json_llm, rag, agent, chain_of_thought, majority_vote, supervisor, debate, judge | LLM provider |
| **Resilience** | provider_failover, retry, rate_limiter | stdlib only |
| **Core Data** | map, reduce, merge, transform, condition, loop, json_parse, list_ops, string_ops, log, timer, cache, trace | stdlib only |
| **External APIs** | web_search, web_scrape, api_call, pdf_extract, spreadsheet | Optional: beautifulsoup4, PyPDF2, openpyxl |
| **Database** | db_schema, nl_to_sql, sql_execute | sqlite3 (built-in) |
| **Memory** | registry, stack, queue, local_memory, secret | stdlib only |
| **Hardware I/O** | usb_serial, audio_input, audio_output, video_input, video_output, webcam | Optional: pyserial, sounddevice, opencv-python |
| **Communication** | socket, websocket, email, calendar, a2a_send, a2a_receive | Optional: websockets, google-auth-oauthlib |
| **Human I/O** | human_input, human_review | stdin/stdout (text I/O) |
| **Async** | async_node, async_batch_node, async_parallel_batch_node | stdlib only |
| **Batch** | batch_node | stdlib only |
| **Code** | code_gen, code_exec, test_gen | Optional: sandbox requires restricted subprocess |
| **Search & Vision** | image_vision, text_chunk, embed, vector_index, vector_retrieve | Optional: vectorstore libs, PIL |
| **Utilities** | classifier, context_compact, conversation_history, mcp_tool, notification, speech_to_text, text_to_speech, data_validate, shell_command, tty_serial, webhook_trigger | Optional: Various (speech libs, etc.)

---

## Limitations

Standalone scripts run flows **line-by-line without the Creator UI**:
- ✅ Node dispatch and execution
- ✅ Shared store state management
- ✅ LLM provider calls
- ✅ File I/O, API calls, etc.

But they cannot:
- ❌ Display the flow visually
- ❌ Show real-time step-through debugging
- ❌ Inspect shared store in Object Inspector
- ❌ Modify the graph interactively

For those, use **Run Active Flow** or **Debug Active Flow** in Creator instead.

---

## Next Steps

- Try exporting different flows as standalone scripts
- Modify the `shared` dict to test different inputs
- Deploy standalone scripts to CI/CD pipelines or serverless platforms
- See [Tutorial: Hardware I/O](hardware_io.md) for sensor and device integration

