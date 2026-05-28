# Part 10 — Database and SQL Nodes

This part covers three nodes that form a natural-language-to-SQL pipeline: inspecting
a database schema, translating a plain-English question into SQL, and executing the
resulting query.

**Prerequisite:** Complete Part 4 (LLM Nodes) for context on how an LLM generates SQL.

---

## Tutorial T-N33: DB Schema Node

### What it does

The **DB Schema Node** connects to a relational database and returns its schema as a
structured dict: table names, column names, data types, primary keys, and foreign-key
relationships. The schema is stored in the shared store and consumed by a downstream
NL-to-SQL Node that needs to know the table structure before writing a query.

### Use cases

- Bootstrapping a natural-language query interface to an existing database
- Generating documentation for an undocumented schema
- Validating that an expected table/column exists before running a migration

### What you'll build

A flow — **Start → SchemaInspector → Stop** — that retrieves the schema of a
small SQLite database with two tables (`orders` and `products`).

### Step-by-step

**Step 1: Create project `gtkn_part10`.**

**Step 2: Drag a DB Schema Node** named `SchemaInspector`.

**Step 3: Set Inspector properties:**

| Property | Value |
|---|---|
| `connection_key` | `db_conn` |
| `output_key` | `db_schema` |
| `dialect` | `sqlite` |

**Step 4: Wire Start → SchemaInspector → Stop.**

**Step 5: Paste the node code:**

```python
from pocketflow import Node

class SchemaInspector(Node):
    def prep(self, shared):
        # In production: shared["db_conn"] holds a live connection object.
        return shared.get("db_conn", None)

    def exec(self, prep_res):
        # Simulated schema for a small e-commerce database.
        return {
            "tables": {
                "orders": {
                    "columns": {
                        "order_id": "INTEGER PRIMARY KEY",
                        "customer_id": "INTEGER",
                        "total": "REAL",
                        "created_at": "TEXT",
                    },
                    "foreign_keys": [
                        {"from": "customer_id", "to": "customers.id"}
                    ],
                },
                "products": {
                    "columns": {
                        "product_id": "INTEGER PRIMARY KEY",
                        "name": "TEXT",
                        "price": "REAL",
                        "stock": "INTEGER",
                    },
                    "foreign_keys": [],
                },
            }
        }

    def post(self, shared, prep_res, exec_res):
        shared["db_schema"] = exec_res
        return "default"
```

**Step 6: Run and inspect `db_schema` in the Shared Store tab.**

### What you learned

- DB Schema Nodes decouple schema discovery from query generation — you can cache the schema and skip re-inspection on subsequent runs
- The output dict structure (tables → columns → types) is the format that NL-to-SQL Nodes expect
- `dialect` selects the SQL flavour (`sqlite`, `postgresql`, `mysql`, `mssql`) for schema introspection

---

## Tutorial T-N34: NL to SQL Node

### What it does

The **NL to SQL Node** takes a plain-English question and a database schema (from the
shared store) and produces a syntactically correct SQL query. Under the hood it calls
an LLM with the schema and question concatenated; the model returns a SQL string that
is ready to execute.

### Use cases

- Building a natural-language database interface without hard-coding queries
- Rapid prototyping of analytics dashboards
- Letting non-technical users query data with plain questions

### What you'll build

Extend the flow from T-N33: add an NL-to-SQL Node that turns "How many orders were
placed after 2024-01-01?" into a `SELECT COUNT(*)` statement.

### Step-by-step

**Step 1: Add an NL to SQL Node** named `QueryBuilder` after `SchemaInspector`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `question_key` | `nl_question` |
| `schema_key` | `db_schema` |
| `output_key` | `generated_sql` |
| `dialect` | `sqlite` |

**Step 3: Re-wire: SchemaInspector → QueryBuilder → Stop.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

class QueryBuilder(Node):
    def prep(self, shared):
        return {
            "question": shared.get(
                "nl_question",
                "How many orders were placed after 2024-01-01?",
            ),
            "schema": shared.get("db_schema", {}),
        }

    def exec(self, prep_res):
        # Production: send schema + question to an LLM and parse the reply.
        # Simulation: return a hard-coded answer for this specific question.
        question = prep_res["question"].lower()
        if "orders" in question and "after" in question:
            return "SELECT COUNT(*) FROM orders WHERE created_at > '2024-01-01';"
        return "SELECT * FROM orders LIMIT 10;"

    def post(self, shared, prep_res, exec_res):
        shared["generated_sql"] = exec_res
        return "default"
```

**Step 5: Run.** `generated_sql` will hold:

```sql
SELECT COUNT(*) FROM orders WHERE created_at > '2024-01-01';
```

### What you learned

- NL-to-SQL Nodes need the schema to avoid hallucinating column names
- The generated SQL string is stored untouched — a downstream SQL Execute Node runs it
- `dialect` is passed to the LLM so it produces the correct date syntax (SQLite vs PostgreSQL differ)

---

## Tutorial T-N35: SQL Execute Node

### What it does

The **SQL Execute Node** runs a SQL statement against a live database connection and
writes the result set to the shared store. `SELECT` queries return a list of row dicts;
`INSERT`, `UPDATE`, and `DELETE` return an affected-row count.

### Use cases

- Closing the NL-to-SQL loop by actually running the generated query
- Running periodic data-quality checks from within a flow
- Inserting LLM-generated records into a database

### What you'll build

Complete the NL-to-SQL pipeline: add an SQL Execute Node that runs the query
produced in T-N34 and stores the result.

### Step-by-step

**Step 1: Add an SQL Execute Node** named `QueryRunner` after `QueryBuilder`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `connection_key` | `db_conn` |
| `sql_key` | `generated_sql` |
| `output_key` | `query_result` |

**Step 3: Wire QueryBuilder → QueryRunner → Stop.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

class QueryRunner(Node):
    def prep(self, shared):
        return {
            "sql": shared.get("generated_sql", ""),
            "conn": shared.get("db_conn", None),
        }

    def exec(self, prep_res):
        sql = prep_res["sql"]
        # Production: conn.execute(sql).fetchall()
        # Simulation: return plausible data for the COUNT query.
        if sql.strip().upper().startswith("SELECT COUNT"):
            return [{"COUNT(*)": 142}]
        return [
            {"order_id": 1, "customer_id": 7, "total": 59.99},
            {"order_id": 2, "customer_id": 3, "total": 120.00},
        ]

    def post(self, shared, prep_res, exec_res):
        shared["query_result"] = exec_res
        return "default"
```

**Step 5: Run and inspect:**

```
generated_sql: "SELECT COUNT(*) FROM orders WHERE created_at > '2024-01-01';"
query_result: [{"COUNT(*)": 142}]
```

### What you learned

- The complete NL-to-SQL pipeline is: **SchemaInspector → QueryBuilder → QueryRunner**
- `query_result` is always a list of dicts for `SELECT`, or `[{"rows_affected": N}]` for DML
- The connection object lives in `shared["db_conn"]` — set it up in a Basic Node at the start of the flow and close it in a final Basic Node

---

[↑ Series Index](gtkn_index.md)
[← Part 9](gtkn_part9.md)
[→ Part 11: Voice, Audio, and Document Nodes](gtkn_part11.md)
