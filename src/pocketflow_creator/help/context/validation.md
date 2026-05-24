# Validation

PocketFlow Creator validates your graph before running or exporting it.

## Running Validation

- **Project > Validate Project** (Ctrl+Shift+V) — validates all graphs in the project
- **Flow > Validate Active Flow** — validates only the current graph
- Validation also runs automatically before Run and before Export

## Reading Results

- **Problems tab** — lists all validation issues with code, severity, and node ID
- **Canvas** — nodes with errors gain a **red border badge**
- **Status bar** — shows a summary count

## Error Codes

| Code | Meaning | Fix |
|---|---|---|
| PFCE1001 | No start node set | Flow > Set Start Node on a node |
| PFCE1002 | Duplicate node IDs | Delete and re-add one of the duplicates |
| PFCE1003 | Start node ID doesn't exist | Re-set the start node |
| PFCE2001 | Edge source node missing | Delete the dangling edge |
| PFCE2002 | Edge destination node missing | Delete the dangling edge |
| PFCE2003 | Edge has no action label | Click the edge; set an action label |
| PFCE2101 | Action not declared on source node | Add the action name to the node's **Actions** field in Inspector |
| PFCE2102 | Subflow node missing `subflow_ref` | Set `subflow_ref` to a valid graph path in Inspector |

## Severity Levels

| Level | Meaning |
|---|---|
| **error** | Blocks export and run |
| **warning** | Reported but does not block (reserved for future use) |

## Validation and Code Generation

`GraphValidator.validate()` must return zero errors before:
- `PythonGenerator` generates `nodes.py` / `flow.py`
- `FlowRunner` runs the graph
- The Exporter writes the export package

[← Help Index](../index.md) | [Tutorial 18: Validation](../tutorials/part3_advanced.md)
