# Project Explorer

The Project Explorer (left panel) shows the file and folder structure of the open project.

## Tree Structure

```
MyProject/
├── graphs/             ← double-click a .pfcgraph.yaml to open it on canvas
├── prompts/            ← double-click a .md file to open it in Markdown editor
├── node_types/         ← double-click a .yaml file to open it in YAML editor
├── tools/              ← double-click a .py file to open it in Python editor
├── schemas/            ← JSON Schema files for structured output validation
└── Shared Store        ← double-click to open the Shared Store Designer
```

## Opening Files

| File type | Action |
|---|---|
| `.pfcgraph.yaml` | Opens the graph on the canvas |
| `.md` | Opens in the Markdown editor tab |
| `.yaml` | Opens in the YAML editor tab |
| `.py` | Opens in the Python editor tab |
| Shared Store | Opens the Shared Store Designer dialog |

## After Opening a Graph

- The canvas shows the graph's nodes and edges
- The Component Palette becomes active
- The Object Inspector shows properties when a node is selected

## Project Metadata

The project root contains `<name>.pfcproj.yaml` with project-level settings including:
- Project name and description
- Shared store schema
- Default provider settings

[← Help Index](../index.md) | [Canvas Help](canvas.md)
