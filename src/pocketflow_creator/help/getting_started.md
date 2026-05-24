# Getting Started

## Installation

### Prerequisites

- Python 3.10 or later
- pip

### Install from source

```bash
git clone https://github.com/your-org/pocketflow-creator.git
cd pocketflow-creator
./scripts/setup-prj.sh       # creates .venv and installs all dependencies
```

### Launch the application

```bash
./scripts/run_app.sh         # Linux / macOS
scripts\run_app.bat          # Windows
```

Or, if installed into an active virtualenv:

```bash
pocketflow-creator
```

---

## First Launch

On first launch the application opens with no project loaded. The canvas is empty and
most menu items are greyed out until a project is opened or created.

**To create your first project:** File > New Project…

**To open an existing project:** File > Open Project… and select a `.pfcproj.yaml` file.

---

## The Six Panels

```
┌──────────────────────────────────────────────────────────────────┐
│  Menu Bar: File  Edit  View  Project  Flow  Node  Run  Tools     │
├──────────────┬───────────────────────────────┬───────────────────┤
│  Project     │                               │  Object           │
│  Explorer    │       Graph Canvas            │  Inspector        │
│              │                               │                   │
├──────────────┤                               ├───────────────────┤
│  Component   │                               │  Component        │
│  Palette     │                               │  Palette          │
│              ├───────────────────────────────┴───────────────────┤
│              │  Python | YAML | Markdown | Run Log | Shared Store │
│              │  Test Results | Prompt Preview | Generated Code    │
└──────────────┴──────────────────────────────────────────────────-┘
```

| Panel | What it does |
|---|---|
| **Project Explorer** | Tree view of graphs, prompts, node types, and tools in the open project |
| **Component Palette** | Drag-and-drop source for built-in node types |
| **Graph Canvas** | Visual editor — place nodes, draw edges, arrange the flow |
| **Object Inspector** | Edit properties of the selected node or edge |
| **Bottom tabs** | Code editor (Python/YAML/Markdown), Run Log, Shared Store view, Test Results, Prompt Preview, Generated Code |
| **Status bar** | Current operation, validation errors, and YAML parse feedback |

---

## Quick-start Workflow

1. **File > New Project…** — name the project and choose a folder
2. Drag a **Start Node** from the Component Palette onto the canvas
3. Drag an **LLM Node** and connect its input port to the Start Node's `default` action port
4. Drag a **Stop Node** and connect the LLM Node's `default` action port to it
5. Select the LLM Node and fill in **Title** and **Prompt File** in the Object Inspector
6. **Project > Validate Project** — fix any red badges
7. **Run > Run Active Flow** — watch the Run Log tab

For a detailed walkthrough see [Your First Flow](your_first_flow.md).

---

## Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| New project | Ctrl+N |
| Open project | Ctrl+O |
| Save | Ctrl+S |
| Undo / Redo | Ctrl+Z / Ctrl+Y |
| Run | F5 |
| Debug | Shift+F5 |
| Toggle breakpoint | F9 |
| Auto layout | Ctrl+Shift+L |
| Zoom to fit | Ctrl+0 |
| Help | F1 |

---

## Next Steps

- [Your First Flow](your_first_flow.md) — step-by-step Hello World
- [About PocketFlow](about_pocketflow.md) — the framework this tool targets
- [Tutorials Part 1](tutorials/part1_fundamentals.md) — IDE deep-dive
