# Tutorial 22: Shared Store Designer

**What you'll learn:** Define the shared-store schema to document and validate data contracts between nodes.

### Steps

1. Open a project in Creator
2. In Project Explorer, double-click **Shared Store** (under the project root)
3. The Shared Store Designer dialog opens with a table:
   - **Namespace** — group keys by domain (e.g., `llm`, `user`, `data`)
   - **Key** — the dict key
   - **Type** — `string`, `integer`, `number`, `boolean`, `array`, `object`, `null`
   - **Default** — initial value if not set by any node

4. Add rows for your flow:
   | Namespace | Key | Type | Default |
   |---|---|---|---|
   | user | question | string | |
   | llm | response | string | |
   | llm | model | string | gpt-4o |
   | data | items | array | |

5. Click **Validate** to check type names are valid JSON Schema types
6. Click **OK** to save — the schema is stored in `project.pfcproj.yaml`

7. Use the **Shared Store** tab during a run to observe live values matching your schema

---
