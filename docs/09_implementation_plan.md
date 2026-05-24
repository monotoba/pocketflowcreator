# Implementation Plan

## Phase 1: Core Project Model

- Project file loader/saver.
- Graph, node, edge, node type, tool, and shared-store models.
- Basic validation.
- Example project.
- Unit tests.

## Phase 2: RAD GUI Shell

- Main window.
- Project explorer.
- Component palette.
- Graph designer placeholder.
- Object inspector.
- Bottom panels.
- Menu and toolbar actions.

## Phase 3: Real Graph Designer

- QGraphicsView/QGraphicsScene graph canvas.
- Node items with action ports.
- Edge routing.
- Drag/drop from palette.
- Inspector synchronization.
- Continuous validation markers.

## Phase 4: Editors

- Python editor.
- Markdown/prompt editor.
- YAML editor.
- Shared-store designer.
- Provider manager.
- Tool registry.

## Phase 5: Code Generation and Export

- Template-based generated Python.
- Generated tests.
- Exported project package.
- Graph image and project report export.

## Phase 6: Run and Debug

- Mock provider runner.
- Ollama provider integration.
- Step debugger.
- Shared-store diffs.
- Prompt preview and response inspection.
- Run trace export.

## Phase 7: Custom Node Type System

- Node type wizard.
- Metadata validation.
- Inheritance support.
- Custom node library manager.
