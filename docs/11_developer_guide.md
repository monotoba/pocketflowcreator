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

- `app.main`: PySide6 main window, toolbar, docks, dialogs.
- `model.graph_model`: graph, node, and edge dataclasses.
- `model.node_type`: reusable component metadata (`NodeTypeDefinition`).
- `validation.graph_validator`: structural graph validation.
- `generation.python_generator`: starter generated-code output.
- `runtime.providers`: provider interfaces and mock provider.
- `node_package_loader`: loads single-file and multi-file node packages from
  `addon_nodes/` (ships with Creator) and `~/.pocketflow_creator/nodes/` (user).

## Node Package System

Node packages extend the palette with additional node types.  Two sources:

### Add-on nodes (`addon_nodes/`)

Located at `src/pocketflow_creator/addon_nodes/`.  These 34 scientific and
engineering packages ship with Creator and are loaded at startup into the
`_ADDON_NODE_REGISTRY`.  They appear in the palette under "Scientific &
Engineering" and in the toolbar after the built-in groups.

Each file follows the `__node_meta__` convention (see `node_package_loader.py`
module docstring for the full key reference).

### User nodes (`~/.pocketflow_creator/nodes/`)

Loaded into `_USER_NODE_REGISTRY` after add-on nodes.  Appear in the palette
under "Custom Nodes".

### Package formats

**Single-file** — one `.py` file, module name prefix `_pfc_node_pkg_<stem>`.

**Multi-file folder** — a subdirectory whose name matches its entry-point file:
`my_plugin/my_plugin.py`.  Loaded with `submodule_search_locations` so relative
imports (`from . import helpers`) work without any `sys.path` mutation.
Module name prefix `_pfc_addon_dir_<dir_name>`.  Two plugins with identically
named helper files cannot interfere with each other.

### Adding a new add-on node

1. Create `src/pocketflow_creator/addon_nodes/my_node.py`.
2. Declare `__node_meta__` with at least `"node"` and `"category"`.
3. Define one class with `prep`, `exec`, and `post` methods.
4. Update `tests/test_node_package_loader.py` — increment the expected count in
   `test_discover_addon_nodes_finds_all` and add the category if new.

### Toolbar super-groups

Built-in nodes in the toolbar are clustered into named super-groups (defined in
`_TOOLBAR_SUPER_GROUPS` in `app/main.py`).  Within a super-group, categories are
separated by `tb.addSeparator()` (thin line).  Between super-groups a transparent
`QWidget` spacer of 32 px is used.  Before the add-on and custom sections a 48 px
spacer provides a more prominent visual break.

The spacer widget requires an explicit height (`setFixedSize(width, 32)`) — a
width-only constraint is collapsed to zero by Qt's toolbar layout engine.

## Refactoring Rule

Refactor in small steps. Keep tests passing. Avoid replacing the entire architecture unless the design is intentionally revised and documented.
