# Component Palette

The Component Palette lists all node types available for dragging onto the canvas.

## Built-in Node Types

| Type | Description |
|---|---|
| **Start Node** | Flow entry point. Every graph must have exactly one start node. |
| **Stop Node** | Flow exit point. No outgoing edges. |
| **Basic Node** | General-purpose node. Subclass it to implement any logic. |
| **LLM Prompt Node** | Calls an LLM using a prompt file. Set `prompt_file` in Inspector. |
| **Router Node** | Branches the flow based on the action returned by `post()`. |
| **Batch Node** | Processes a list of items — `exec()` is called once per item. |
| **Human Review Node** | Pauses for human input/approval; actions: `approved, rejected`. |
| **Subflow Node** | Embeds another graph. Set `subflow_ref` to the graph file path. |

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
