# Component Palette

The Component Palette lists all node types available for dragging onto the canvas.

## Built-in Node Types (20 total)

### Flow Control

| Type | Description |
|---|---|
| **Start Node** | Flow entry point. Every graph must have exactly one start node. |
| **Stop Node** | Flow exit point. No outgoing edges. |
| **Router Node** | Branches the flow based on the action returned by `post()`. |
| **Subflow Node** | Embeds another graph. Set `subflow_ref` to the graph file path. |

### General Purpose

| Type | Description |
|---|---|
| **Basic Node** | General-purpose node. Subclass it to implement any logic. |
| **Python Tool Node** | Runs arbitrary Python — calculations, API calls, data transformations. |

### LLM / AI

| Type | Description |
|---|---|
| **LLM Prompt Node** | Calls an LLM. Set `prompt_type` to `string` (inline text) or `path` (file). Supports `{{key}}` interpolation of shared store values. |
| **JSON LLM Node** | Like LLM Prompt Node but instructs the model to respond with structured JSON. |
| **Classifier Node** | Sends a classification prompt; returns one of a fixed set of labels as the action. |
| **Agent Node** | Implements the decide-act loop of an autonomous LLM agent. |
| **RAG Node** | Embedding and retrieval step for Retrieval-Augmented Generation pipelines. |
| **Judge Node** | Evaluates LLM output against criteria; returns `pass` or `fail`. |

### Data / I/O

| Type | Description |
|---|---|
| **File Reader Node** | Reads a file from disk into the shared store. |
| **File Writer Node** | Writes data from the shared store to a file on disk. |

### Processing

| Type | Description |
|---|---|
| **Batch Node** | Processes a list of items — `exec()` is called once per item (synchronous). |
| **Async Node** | Single async step (`async def exec_async`). |
| **Async Batch Node** | Processes items sequentially using async I/O. |
| **Async Parallel Batch Node** | Processes all items concurrently via `asyncio.gather`. |

### Human in the Loop

| Type | Description |
|---|---|
| **Human Review Node** | Pauses for human approval; actions: `approved, rejected`. |
| **Human Input Node** | Reads a string from the user at runtime and writes it to the shared store. |

## Custom Node Types

Custom types created via Node > New Custom Node Type… appear in the palette under their
declared **category** after the project is reloaded.

## Using the Palette

1. Find the node type by scrolling or looking at category groups
2. Click and hold on a node type
3. Drag it onto the **Graph Canvas**
4. Release — the node appears at the drop position
5. Click the new node to select it and edit its properties in the **Object Inspector**

## Node Lifecycle

Every node follows the `prep → exec → post` lifecycle:

```
shared store → prep(shared) → exec(prep_res) → post(shared, prep_res, exec_res) → action string
```

The action string from `post()` determines which edge to follow next.

[← Help Index](../index.md) | [Canvas Help](canvas.md)
