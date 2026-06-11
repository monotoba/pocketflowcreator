# Tutorial 1: IDE Tour

**What you'll learn:** The six panels of the PocketFlow Creator IDE and what each one does.

**Prerequisites:** App launched (`python -m pocketflow_creator` or `pocketflow-creator`).

### The Six Panels

```
┌──────────────────────────────────────────────────────────────────┐
│  Menu Bar: File  Edit  View  Project  Flow  Node  Run  Tools     │
├──────────────┬───────────────────────────────┬───────────────────┤
│              │                               │                   │
│  Project     │       Graph Canvas            │  Object           │
│  Explorer    │  (drag nodes here, wire       │  Inspector        │
│  (left dock) │   edges between ports)        │  (right dock)     │
│              │                               │                   │
├──────────────┤                               │  Component        │
│  Component   │                               │  Palette          │
│  Palette     │                               │  (drag sources)   │
│  (left dock) │                               │                   │
│              ├───────────────────────────────┴───────────────────┤
│              │  Python | Markdown | YAML | Run Log | Shared Store│
│              │  Test Results | Prompt Preview | Generated Code    │
└──────────────┴───────────────────────────────────────────────────┘
```

| Panel | Purpose |
|---|---|
| **Project Explorer** | Tree view of the loaded project — graphs, prompts, node types, tools |
| **Component Palette** | Drag-and-drop source for all built-in node types and snippets |
| **Graph Canvas** | Visual editor — nodes, edges, ports; your flow lives here |
| **Object Inspector** | Property editor for the selected node or edge |
| **Bottom tabs** | Code editor, run output, shared store view, test results |
| **Status bar** | Current operation and validation feedback |

### Quick Reference: Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| New project | Ctrl+N |
| Open project | Ctrl+O |
| Save | Ctrl+S |
| Save all | Ctrl+Shift+S |
| Export project | Ctrl+E |
| Validate | Ctrl+Shift+V |
| Run active flow | F5 |
| Debug active flow | Shift+F5 |
| Toggle breakpoint | F9 |
| Zoom to fit | Ctrl+0 |
| Auto layout | Ctrl+Shift+L |

---
