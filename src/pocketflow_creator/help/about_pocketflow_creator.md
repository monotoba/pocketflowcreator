# About PocketFlow Creator

PocketFlow Creator is a RAD (Rapid Application Development) visual designer for building
PocketFlow LLM workflows. It follows the Delphi/VB style: every visible object has properties,
every transition is an action, every generated behavior can be inspected as Python, and every
custom behavior belongs in user-owned files that are never overwritten.

**Version:** 0.1.1  
**Framework target:** PocketFlow (any version)  
**Language:** Python 3.10+  
**GUI framework:** PySide6 (Qt 6)

---

## Design Principles

| Principle | Meaning |
|---|---|
| **Project generator, not a runtime** | Generated projects run without Creator installed |
| **Plain-text project files** | `.pfcproj.yaml` and `.pfcgraph.yaml` are human-readable and version-control friendly |
| **Never overwrite `custom/`** | Hand-edited node implementations survive every re-export |
| **Validate before generate** | The graph must pass validation before code is generated or a flow is run |
| **One node type model** | Built-in and custom nodes use the same `NodeTypeDefinition` — no special cases |
| **Offline-first** | No calls to external services during design time; LLM calls only happen at run time |

---

## Application Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  GUI (app/)                                                     │
│    MainWindow  ·  GraphCanvas  ·  Editors  ·  HelpBrowser       │
│    NodeTypeWizard  ·  SharedStoreDesigner                        │
├─────────────────────────────────────────────────────────────────┤
│  Services (controller layer)                                    │
│    ProjectLoader/Saver  ·  GraphLoader/Saver  ·  Exporter       │
│    CodeManager  ·  FlowRunner                                   │
├─────────────────────────────────────────────────────────────────┤
│  Domain (model / validation / generation)                       │
│    GraphModel  ·  NodeModel  ·  EdgeModel                       │
│    NodeTypeDefinition  ·  ProjectModel                          │
│    GraphValidator  ·  PythonGenerator                           │
├─────────────────────────────────────────────────────────────────┤
│  Runtime (providers)                                            │
│    LLMProvider (protocol)  ·  OllamaProvider  ·  MockProvider   │
└─────────────────────────────────────────────────────────────────┘
```

The GUI never imports directly from `validation/` or `generation/` — it goes through the
controller layer. The domain packages are UI-agnostic pure Python and can be used from
scripts, tests, or CI pipelines.

---

## Project File Layout

```
MyProject/
├── MyProject.pfcproj.yaml      ← project metadata and settings
├── graphs/
│   └── main.pfcgraph.yaml      ← graph: nodes, edges, properties
├── prompts/
│   └── ask_llm.md              ← LLM prompt files (Markdown)
├── node_types/
│   └── my_custom_node.yaml     ← custom node type definitions
├── tools/
│   └── search.py               ← tool implementations
└── schemas/
    └── output_schema.json      ← JSON Schema for structured output nodes
```

After export, the standalone project appears in `exports/MyProject/`:

```
exports/MyProject/
├── generated/          ← regenerated on every export
│   ├── nodes.py        ← node class stubs
│   └── flow.py         ← PocketFlow wiring
├── custom/             ← NEVER overwritten — your implementations live here
│   └── my_node_impl.py
├── tests/
│   └── test_flow.py
└── main.py
```

---

## The RAD Coding Model

PocketFlow Creator follows the Delphi RAD model for node code:

1. **Drop a node on the canvas** → Creator adds a class stub to `code/<graph>.py`
2. **Double-click the node** → Python editor opens scrolled to that class
3. **Edit the class** → changes persist in `code/<graph>.py`
4. **Delete the node from canvas** → the class block is removed from the code file
5. **Export** → Creator merges the code file into `custom/` (never overwriting existing files)

The marker format:
```python
# --- NODE_START: node_abc ---
class MyNode(Node):
    def prep(self, shared): ...
    def exec(self, prep_res): ...
    def post(self, shared, prep_res, exec_res): return "default"
# --- NODE_END: node_abc ---
```

---

## Validation Error Codes

| Code | Meaning |
|---|---|
| PFCE1001 | No start node selected |
| PFCE1002 | Duplicate node ID |
| PFCE1003 | Start node ID does not exist |
| PFCE2001 | Edge source node does not exist |
| PFCE2002 | Edge destination node does not exist |
| PFCE2003 | Edge has no action label |
| PFCE2101 | Edge action not declared by source node |
| PFCE2102 | Subflow node missing or unresolved subflow_ref |

---

## Internationalization

The UI supports multiple languages. Change the language in **Tools > Options > Language**.
A restart is required for the change to take effect.

Currently shipped: **English** (en), **Spanish** (es), **French** (fr), **German** (de).

---

## Contributing

See `docs/12_developer_guide.md` in the source tree for development setup, architecture
notes, and contribution guidelines.
