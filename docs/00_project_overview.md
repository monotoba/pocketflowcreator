# Project Overview

PocketFlow Creator is a RAD-style visual designer for PocketFlow LLM workflows. Its purpose is to let users build agentic workflows by selecting node types, placing nodes on a graph, editing node properties, wiring action ports, validating the graph, running/debugging it, and exporting a normal Python PocketFlow project.

The product should feel like Delphi Studio or Visual Basic:

- Component palette for selecting node types.
- Designer surface for arranging workflow components.
- Object inspector for editing properties.
- Events/actions panel for wiring behavior.
- Code-behind view for generated or custom Python.
- Project explorer for prompts, node types, schemas, tools, tests, and exports.

The guiding rule is:

```text
Every visible object has properties.
Every transition is an action.
Every generated behavior can be inspected as Python.
Every custom behavior belongs in user-owned files that are never overwritten.
```
