# About PocketFlow

PocketFlow is a minimalist LLM framework — the entire runtime is **100 lines of Python** —
that expresses LLM workflows as directed graphs of nodes connected by labelled action edges.

| | |
|---|---|
| **Repository** | [https://github.com/The-Pocket/PocketFlow](https://github.com/The-Pocket/PocketFlow) |
| **Author** | Zachary Huang ([@ZacharyHuang](https://github.com/zachary62)) |
| **Organisation** | [The Pocket](https://github.com/The-Pocket) |
| **Licence** | MIT |

---

## The philosophy

Most LLM frameworks grow into sprawling abstractions that hide what is actually happening.
PocketFlow takes the opposite approach: the framework is small enough to read in a single
sitting, yet powerful enough to express every major LLM pattern — chat loops, agents,
retrieval-augmented generation, batch processing, human-in-the-loop, and multi-agent
systems.

The core insight is that *every* LLM application is a directed graph:

- **Nodes** do the work — they call LLMs, tools, databases, or run arbitrary Python.
- **Edges** are labelled with action strings that `post()` returns, making control flow
  explicit and testable.
- **The shared store** is a plain `dict` — the only communication channel between nodes,
  no hidden state.

---

## How a node works

```python
class MyNode(Node):
    def prep(self, shared):
        # Read from the shared store; prepare inputs for exec.
        return shared.get("question", "")

    def exec(self, prep_res):
        # Do the work: LLM call, tool call, file I/O, anything.
        return llm.complete(prep_res)

    def post(self, shared, prep_res, exec_res):
        # Write results back; return an action string to route the flow.
        shared["answer"] = exec_res
        return "default"
```

---

## Wiring a flow

```python
flow = fetch_node - "ok" >> summarise_node
flow = fetch_node - "error" >> retry_node
flow = summarise_node >> done_node   # shorthand for "default"
```

`post()` returns `"ok"` or `"error"` and the framework follows the matching edge.
There is no magic — the routing table is just a dict of action strings to next nodes.

---

## Node base classes

| Class | Purpose |
|---|---|
| `Node` | Standard single-execution node |
| `BatchNode` | Runs `exec()` once per item returned by `prep()` |
| `AsyncNode` | Async node (`async def exec`) |
| `AsyncBatchNode` | Async batch processing |

---

## Cookbook patterns

The PocketFlow repository ships 40+ cookbook examples covering:

| Level | Topics |
|---|---|
| Beginner | Hello World, Chat, Structured Output, Workflow, Routing |
| Intermediate | Agent with tools, RAG, Map-Reduce, HITL, LLM-as-Judge, Multi-Agent |
| Advanced | Streaming, Memory, Subflow, Async, Web search, Code execution |

---

## Why PocketFlow Creator was born

PocketFlow's simplicity is a strength, but designing a multi-node flow by writing Python
directly means holding the entire graph in your head — which nodes exist, how they connect,
what actions each one declares, and how shared store keys flow between them.

**PocketFlow Creator** was built to give PocketFlow a visual design surface without
taking away any of its transparency.  The goal is the same RAD experience that made
Delphi and Visual Basic productive for a generation of developers — drag a node onto a
canvas, wire its action ports, inspect its properties, and see the generated Python
immediately — while keeping the output as plain, readable PocketFlow code that runs
without the designer installed.

The designer is a *generator*, not a runtime wrapper.  Every exported project is
self-contained Python that you own completely.

- [Getting Started](getting_started.md)
- [Your First Flow](your_first_flow.md)
- [About PocketFlow Creator](about_pocketflow_creator.md)
- [Help Home](index.md)
