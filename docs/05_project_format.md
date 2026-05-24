# Project Format

Recommended project layout:

```text
my_project/
├─ my_project.pfcproj.yaml
├─ graphs/
│  └─ main.pfcgraph.yaml
├─ prompts/
├─ node_types/
├─ tools/
├─ schemas/
├─ src/my_project/
│  ├─ generated/
│  ├─ custom/
│  └─ main.py
├─ tests/
└─ exports/
```

## Graph File Example

```yaml
schema_version: 0.1
id: main
title: MainFlow
flow_type: sync
start_node: node_start
nodes:
  - id: node_start
    type_id: start_node
    title: Start
    position: {x: 80, y: 80}
    actions: [default]
  - id: node_summarize
    type_id: llm_prompt_node
    title: Summarize Document
    position: {x: 360, y: 80}
    reads: [document.text]
    writes: [document.summary]
    actions: [success, error]
edges:
  - id: edge_start_summarize
    from_node: node_start
    action: default
    to_node: node_summarize
```

## Determinism Rules

- Stable IDs should not change when display names change.
- YAML output should have deterministic key order.
- Generated code should be reproducible from graph metadata.
- User custom files should not be generated into the same folder as generated files.
