# About PocketFlow

PocketFlow is a minimalist LLM framework — 100 lines of Python — that expresses LLM
workflows as directed graphs of nodes connected by labelled action edges.

**Repository:** [https://github.com/The-Pocket/PocketFlow](https://github.com/The-Pocket/PocketFlow)

---

## Core Concepts

### Nodes

Every unit of work is a **Node**. A node has three lifecycle methods:

```python
class MyNode(Node):
    def prep(self, shared):
        # Read from shared store; prepare inputs for exec
        return shared.get("question", "")

    def exec(self, prep_res):
        # Do the work (LLM call, tool call, computation)
        return llm.complete(prep_res)

    def post(self, shared, prep_res, exec_res):
        # Write results back to shared store; return an action string
        shared["answer"] = exec_res
        return "default"
```

### The Shared Store

The **shared store** is a plain Python `dict` passed to every node in the flow.
Nodes read from it in `prep()` and write to it in `post()`.
It is the only communication channel between nodes.

### Actions and Edges

`post()` returns an **action string** (e.g. `"default"`, `"yes"`, `"no"`).
The flow follows the edge whose label matches that action string to determine the next node.

```python
flow = node_a - "yes" >> node_b
flow = node_a - "no" >> node_c
```

### Flows

A **Flow** is a directed graph of nodes. You set a start node and wire edges.
The flow engine executes nodes in sequence, following action edges.

---

## Node Types

| Base class | Purpose |
|---|---|
| `Node` | Standard single-execution node |
| `BatchNode` | Runs `exec()` once per item in a list returned by `prep()` |
| `AsyncNode` | Async version of Node (uses `async def exec`) |
| `AsyncBatchNode` | Async batch processing |

---

## Key Patterns

| Pattern | Description |
|---|---|
| **Single Q&A** | One LLM node answers a question |
| **Chat loop** | LLM node + history accumulation + routing back to itself |
| **Structured output** | LLM node with JSON schema validation and retry |
| **Conditional routing** | `post()` returns different actions to branch the flow |
| **Agent with tools** | LLM decides which tool node to call; routing back until done |
| **RAG** | Retrieval node → context injection → LLM node |
| **Map-reduce batch** | `BatchNode` fans out; aggregator node fans in |
| **Human-in-the-loop** | Node pauses and waits for user input via shared store |
| **LLM-as-judge** | Evaluator node scores output; retry edge loops back on failure |
| **Multi-agent** | Multiple flows communicate via a shared store or message queue |

Each pattern is covered in [Part 2 Tutorials](tutorials/part2_patterns.md).

---

## The Three-Layer Architecture

```
┌──────────────────────────────────────────────┐
│  Your nodes (custom Python in custom/)       │
├──────────────────────────────────────────────┤
│  PocketFlow runtime (pocketflow package)     │
├──────────────────────────────────────────────┤
│  LLM Provider (Ollama, OpenAI, etc.)         │
└──────────────────────────────────────────────┘
```

PocketFlow does not bundle an LLM provider. You wire your preferred provider into each
LLM node. PocketFlow Creator uses `OllamaProvider` by default and supports any provider
that implements the `LLMProvider` protocol.

---

## Cookbook Examples

The PocketFlow repository ships 40+ cookbook examples:

| Level | Topics |
|---|---|
| Beginner | Hello World, Chat, Structured Output, Workflow, Routing |
| Intermediate | Agent, RAG, Map-Reduce, HITL, LLM-as-Judge, Multi-Agent |
| Advanced | Streaming, Memory, Subflow, Async, Web search, Code execution |

PocketFlow Creator provides visual equivalents of every cookbook example in its
[tutorial series](tutorials/index.md).
