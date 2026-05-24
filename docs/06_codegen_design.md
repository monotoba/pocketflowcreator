# Code Generation Design

Generated projects should remain ordinary Python projects that can run without the visual designer.

## Output Structure

```text
src/my_agent/
├─ generated/
│  ├─ flow.py
│  ├─ nodes.py
│  └─ providers.py
├─ custom/
│  ├─ custom_nodes.py
│  └─ tools.py
└─ main.py
```

## Generation Rules

1. Generate readable Python.
2. Keep node classes small.
3. Keep provider code in adapter modules.
4. Do not hardcode secrets.
5. Never overwrite files under `custom/`.
6. Generate smoke tests.
7. Prefer mock provider in generated tests.

## PocketFlow Mapping

- Node instance maps to a Python class or configured subclass instance.
- Edge action maps to `node - "action" >> destination`.
- Default edge maps to `node >> destination`.
- Flow start node maps to `Flow(start=start_node)`.
- Shared-store reads/writes map to `prep()` and `post()` behavior.
