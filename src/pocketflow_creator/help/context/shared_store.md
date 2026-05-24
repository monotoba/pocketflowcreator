# Shared Store Designer

The Shared Store Designer documents and validates the data contracts between nodes.

## What Is the Shared Store?

The shared store is a plain Python `dict` passed to every node in the flow.
Nodes read from it in `prep()` and write to it in `post()`.
It is the only communication channel between nodes.

## Opening the Designer

- **Tools > Shared Store Inspector…** — opens the designer for the current project
- **Project Explorer > double-click "Shared Store"** — same dialog

## Columns

| Column | Description |
|---|---|
| **Namespace** | Groups related keys (e.g., `llm`, `user`, `data`). Use any string. |
| **Key** | The dict key used in code: `shared["key"]` or `shared.get("key")` |
| **Type** | JSON Schema type: `string`, `integer`, `number`, `boolean`, `array`, `object`, `null` |
| **Default** | Optional initial value; displayed in the Run Log before any node sets the key |

## Adding, Editing, Removing Rows

- **Add:** Click an empty row and type; or use the add-row button
- **Edit:** Click any cell to edit in place
- **Remove:** Select a row and press Delete

## Validate

Click **Validate** to check:
- All type names are valid JSON Schema primitive types
- No duplicate Namespace+Key combinations

## How It Affects Runs

The shared store schema is documentation — it does not enforce types at runtime.
During a run, the **Shared Store** tab shows live key/value pairs. Keys defined in
the designer appear with their types annotated.

## Saving

Click **OK** to save. The schema is stored in `project.pfcproj.yaml` under the
`shared_store_schema` field.

[← Help Index](../index.md) | [About PocketFlow](../about_pocketflow.md)
