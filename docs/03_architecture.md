# Architecture

## Layered Structure

```text
GUI Layer
  Main window, graph designer, inspectors, editors, dialogs

Design Model Layer
  ProjectModel, GraphModel, NodeModel, EdgeModel, NodeTypeDefinition

Validation Layer
  Graph validation, node metadata validation, prompt/schema validation, safety checks

Generation Layer
  Python PocketFlow code generator, test generator, report generator

Runtime Layer
  Debug runner, trace model, provider adapters, mock provider

Project Files
  YAML/JSON graph files, Markdown prompts, Python custom code, tests, schemas
```

## Key Architectural Decisions

1. The GUI is a visual project generator, not a replacement runtime.
2. Standard and custom node types use the same metadata model.
3. Generated code and custom code are physically separated.
4. Graph project files must be deterministic and version-control friendly.
5. Validation must run before code generation and execution.
6. Tests must not require real LLM calls.

## Suggested Package Layout

```text
src/pocketflow_creator/
├─ app/
├─ graph/
├─ model/
├─ node_templates/
├─ validation/
├─ generation/
├─ runtime/
└─ resources/
```
