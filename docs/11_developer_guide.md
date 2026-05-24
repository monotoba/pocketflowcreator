# Developer Guide

## Setup

```bash
./scripts/setup-prj.sh
./scripts/test.sh
```

## Run

```bash
./scripts/run_app.sh
```

## Important Modules

- `app.main`: initial PySide6 shell.
- `model.graph_model`: graph, node, and edge dataclasses.
- `model.node_type`: reusable component metadata.
- `validation.graph_validator`: structural graph validation.
- `generation.python_generator`: starter generated-code output.
- `runtime.providers`: provider interfaces and mock provider.

## Refactoring Rule

Refactor in small steps. Keep tests passing. Avoid replacing the entire architecture unless the design is intentionally revised and documented.
