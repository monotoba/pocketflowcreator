# PocketFlow Creator — Project Memory

This file is the single source of truth for project context, architecture decisions,
working conventions, and current state. Read it at the start of any session before
looking at code or picking up tasks.

---

## What This Project Is

A **Delphi/VB-style RAD visual designer** for building PocketFlow-based LLM workflows.
The user selects a node type from a palette, places it on a graph canvas, edits its
properties in an inspector, wires action ports to other nodes, validates the graph, then
exports a normal Python PocketFlow project.

The app is a **project generator**, not a runtime. Generated projects run without the
visual designer installed.

**Guiding rule:**
```
Every visible object has properties.
Every transition is an action.
Every generated behavior can be inspected as Python.
Every custom behavior belongs in user-owned files that are never overwritten.
```

---

## Architecture Rules (Do Not Break These)

1. **Layers are separate.** GUI (`app/`) never imports from `validation/` or `generation/`
   directly — it goes through a controller or service interface. `model/`, `validation/`,
   and `generation/` are UI-agnostic pure-Python packages.

2. **No real LLM calls in tests.** Use `MockProvider` for all tests. Tests must be
   deterministic and run offline.

3. **Never overwrite `custom/`.** When re-exporting a project, the `generated/` directory
   may be replaced. The `custom/` directory must never be overwritten. Guard this at the
   export layer.

4. **Project files are plain text.** `.pfcproj.yaml` and `.pfcgraph.yaml` files must remain
   human-readable and version-control friendly. No binary formats, no embedded blobs.

5. **Standard and custom node types use the same metadata model.** `NodeTypeDefinition` is
   the one type. Custom nodes extend it — they do not get a separate model.

6. **Validation runs before generation and execution.** `GraphValidator.validate()` must
   return zero errors before `PythonGenerator` is invoked or a flow is started.

7. **Provider credentials are never stored in project files.** Provider config goes in
   user-local profiles, not in `.pfcproj.yaml`.

---

## Current Implementation State (v0.1.0 — 2026-05-23)

See `STATUS.md` for the full inventory. Short version:

**Done:**
- Data models: `GraphModel`, `NodeModel`, `EdgeModel`, `NodeTypeDefinition`, `ProjectModel`
- `GraphValidator` with 4 rule checks and PFCE error codes
- `PythonGenerator` producing `nodes.py` + `flow.py` from a `GraphModel`
- `MockProvider` (deterministic), `OllamaProvider` (stub, no HTTP yet)
- PySide6 `MainWindow` — full menu bar, 4 dock regions, 9 bottom tabs (all stub content)
- Example project: `examples/document_summarizer/`
- 12 design/spec documents in `docs/`
- 7 passing unit tests

**Not yet done:**
- Project YAML loader and saver (needed before GUI File > Open/Save can work)
- Real graph canvas (`QGraphicsScene`, node items, edge routing, drag/drop)
- Real property grid inspector
- Real editor widgets (Python/Markdown/YAML syntax highlighting)
- Menu action dispatch (all actions are stubs)
- `OllamaProvider` HTTP integration
- Run/debug engine
- Custom node type wizard

---

## Key Files

| Path | Purpose |
|---|---|
| `src/pocketflow_creator/model/graph_model.py` | `GraphModel`, `NodeModel`, `EdgeModel` |
| `src/pocketflow_creator/model/node_type.py` | `NodeTypeDefinition` |
| `src/pocketflow_creator/model/project.py` | `ProjectModel` |
| `src/pocketflow_creator/validation/graph_validator.py` | `GraphValidator`, `ValidationIssue` |
| `src/pocketflow_creator/generation/python_generator.py` | `PythonGenerator` |
| `src/pocketflow_creator/runtime/providers.py` | `LLMProvider`, `MockProvider`, `OllamaProvider` |
| `src/pocketflow_creator/app/main.py` | `MainWindow`, `run()` |
| `examples/document_summarizer/` | Reference project showing expected file layout |
| `docs/` | Full design spec — read before implementing a new area |
| `STATUS.md` | Test/lint counts and what's done vs. deferred |
| `TASKS.md` | Milestones and task list — update as work completes |

---

## Development Workflow

```bash
# First time
./scripts/setup-prj.sh          # creates .venv and installs deps

# Every session
./scripts/test.sh               # run all tests (must stay green)
./scripts/lint.sh               # ruff check src tests
./scripts/run_app.sh            # launch the GUI (headless on CI: skip)
```

**Before starting any task:** run `test.sh` to confirm baseline is green.
**Before committing:** run `test.sh` and `lint.sh`. Do not commit failing tests.

Work in **vertical slices** — each slice adds a complete capability end-to-end:
model → service → test → GUI wire-up. Do not add GUI stubs for features whose
backing service doesn't exist yet.

---

## Lint Baseline

9 pre-existing issues from the original scaffold are not yet fixed (tracked as T-005).
Until T-005 is closed, `ruff check` will report these; do not let new issues pile on.
See STATUS.md for the list of affected files.

---

## Commit Conventions

- **Author:** `Monotoba`
- **Co-authored-by:** Add `Co-Authored-By: Claude <noreply@anthropic.com>` on roughly
  1 in 10 commits — not every commit.
- **Message style:** imperative subject line, short body if needed. Reference milestone
  and task IDs when relevant (e.g., `M2-A: Add ProjectLoader`).
- **No force-push to main.**

---

## Error Code Namespace

Graph validation issues use the `PFCE` prefix:

| Code | Meaning |
|---|---|
| PFCE1001 | No start node selected |
| PFCE1002 | Duplicate node ID |
| PFCE1003 | Start node ID does not exist |
| PFCE2001 | Edge source node does not exist |
| PFCE2002 | Edge destination node does not exist |
| PFCE2003 | Edge has no action label |
| PFCE2101 | Edge action not declared by source node |

New error codes should continue from the highest currently assigned number in the
relevant block (1xxx = node/graph structure, 2xxx = edges, 3xxx = reserved for node types).

PFCE2102 added: subflow_node missing/unresolved `subflow_ref`.

---

## Tutorials (M10)

`docs/TUTORIALS.md` is the authoritative user-facing tutorial document.
It contains **25 tutorials + 4 exercises** in 4 parts:

- **Part 1 — Creator Fundamentals** (Tutorials 1–6): IDE tour, first flow, inspector,
  code editor, custom node wizard, project templates
- **Part 2 — PocketFlow Patterns** (Tutorials 7–17, 23–24): maps every major PocketFlow
  cookbook pattern (hello world, chat, structured output, workflow, routing, agent, RAG,
  batch, HITL, judge, multi-agent, streaming, memory) to Creator graph + code
- **Part 3 — Advanced Features** (Tutorials 18–22, 25): validation, debug/breakpoints,
  subflow, export, shared store designer, packaging
- **Part 4 — Exercises** (A–D): News Summariser, Coding Agent, Multi-Provider Router,
  Full IDE Workout

PocketFlow repo (https://github.com/The-Pocket/PocketFlow) has 40+ cookbook examples
across beginner/intermediate/advanced levels. All are covered in the tutorials.

---

## RAD Studio Features Added (Post-Backlog)

These features were added after the backlog (M10+) in response to user feedback:

| Feature | Files changed |
|---|---|
| Inspector property editing (Actions, Reads, Writes, typed properties) | `main.py` |
| Editable inspector cells styled with blue tint + tooltip | `main.py` |
| Canvas → code sync (`code/<stem>.py` per graph) | `canvas.py`, `main.py`, `code_manager.py` |
| Double-click node → Python editor scrolled to class | `main.py` |
| Delete key removes node from canvas AND code file | `canvas.py`, `main.py` |
| Auto Layout (BFS layered, Ctrl+Shift+L) | `canvas.py`, `main.py` |
| Zoom to Fit on graph load | `main.py` |
| System / Light / Dark theme modes (replaces dark-only checkbox) | `main.py` |
