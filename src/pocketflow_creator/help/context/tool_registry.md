# Tool Registry

**Tools > Tool Registry** shows all Python functions decorated with `@tool` that PocketFlow Creator has discovered in your project's `tools/` directory.

## What Is a Tool?

A *tool* is a Python function that a PocketFlow agent node can call during execution. Tools are defined using the `@tool` decorator pattern:

```python
from pocketflow import tool

@tool
def search_web(query: str) -> str:
    """Search the web and return a summary of results."""
    ...
```

The function name becomes the tool's identifier. The first line of the docstring is shown in the registry as the description.

## Tool Discovery

PocketFlow Creator scans every `.py` file in your project's `tools/` directory for functions decorated with `@tool`. The decorator may be bare (`@tool`) or an attribute (`@pocketflow.tool`).

Only the `tools/` directory at the project root is scanned. Sub-packages are not traversed.

## Registry Columns

| Column | Content |
|---|---|
| **Function** | The Python function name (used as the tool identifier) |
| **File** | The source file within `tools/` |
| **Description** | First line of the function's docstring |

## Adding a Tool

1. Create or open a `.py` file in `<project>/tools/`.
2. Import and apply the `@tool` decorator to a function.
3. Write a clear one-line docstring — it appears as the description in this dialog.
4. Re-open Tool Registry to see the function listed.

## Using Tools in Flows

In a node's **Reads** or **Writes** property you can reference tool output by name. LLM agent nodes automatically receive the tool list when the flow runs if the node type declares `uses_tools: true` in its YAML definition.

## Related Help

- [Canvas](canvas.md) — placing and wiring nodes
- [Inspector](inspector.md) — node properties, Reads, Writes
- [Node Type Wizard](node_type_wizard.md) — creating node types that use tools
- [Help Home](../index.md)
