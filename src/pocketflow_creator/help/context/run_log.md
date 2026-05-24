# Run Log

The **Run Log** tab shows the execution trace of the most recent flow run.

## Columns

| Column | Description |
|---|---|
| **Node** | The node title and ID |
| **Action** | The action returned by `post()` — the edge taken to the next node |
| **Prompt** | For LLM nodes: the prompt text sent to the provider |
| **Response** | For LLM nodes: the response received from the provider |

## Shared Store Tab

The **Shared Store** tab next to Run Log shows the live shared store state:
- Updated after each node executes
- Shows key/value pairs as the flow progresses
- In debug mode, pauses between nodes so you can inspect state

## Running a Flow

- **Run > Run Active Flow** (F5) — runs all nodes to completion
- **Run > Debug Active Flow** (Shift+F5) — pauses at breakpoints
- **Run > Stop** — aborts the current run
- **Run > Resume** — continues after a debug pause

## Trace Files

Each run saves a JSON trace file to `run_reports/<timestamp>.json`. The file contains:
- All steps executed
- Shared store state before and after each node
- Prompts and responses for LLM nodes

## Test Results Tab

**Run > Run Tests** executes `pytest` in the project directory and displays the output in
the **Test Results** tab.

[← Help Index](../index.md) | [Tutorial 19: Debug Mode](../tutorials/part3_advanced.md)
