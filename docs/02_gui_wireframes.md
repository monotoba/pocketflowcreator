# GUI Wireframes and Menu Design

## Main Window

```text
+----------------------------------------------------------------------------------------------------------------------+
| PocketFlow Creator - DocumentSummarizer.pfcproj                                                                      |
+----------------------------------------------------------------------------------------------------------------------+
| File  Edit  View  Project  Flow  Node  Run  Tools  Window  Help                                                      |
+----------------------------------------------------------------------------------------------------------------------+
| Toolbar: [New] [Open] [Save] | [Select] [Pan] [Wire] | [Validate] [Run] [Step] [Stop] | Provider: Ollama [Test]     |
+----------------------+----------------------+---------------------------------------------------+-------------------+
| Project Explorer     | Component Palette    | Graph Designer                                    | Object Inspector  |
| DocumentSummarizer   | Core                 |  [Start] --> [Load] --> [Summarize] --> [Review]  | Object properties |
| ├─ Flows             |  Start Node          |                         | approved            | Actions           |
| ├─ Prompts           |  LLM Prompt Node     |                         v                     | Prompt            |
| ├─ Node Types        |  Router Node         |                      [Save]                   | Python Hooks      |
| ├─ Tools             |  Tool Node           |                                                   | Generated Code    |
| └─ Tests             |  Human Node          |                                                   |                   |
+----------------------+----------------------+---------------------------------------------------+-------------------+
| Problems | Run Log | Shared Store | Prompt Preview | Generated Code | Python | Markdown | YAML | Test Results          |
+----------------------------------------------------------------------------------------------------------------------+
```

The main window is the primary work area. It follows the RAD layout used by Delphi, Visual Basic, Qt Designer, and similar tools. The graph designer shows workflow structure; the object inspector edits selected object behavior; the project explorer organizes real files; the component palette supplies reusable node types; the bottom panels support validation, debugging, code, prompts, YAML metadata, and tests.

## File Menu

```text
File
├─ New Project...
├─ New From Template...
├─ Open Project...
├─ Open Recent
├─ Close Project
├─ Save
├─ Save As...
├─ Save All
├─ Import
│  ├─ Import PocketFlow Python Project...
│  ├─ Import Graph YAML/JSON...
│  ├─ Import Prompt Files...
│  └─ Import Custom Node Type...
├─ Export
│  ├─ Export PocketFlow Project...
│  ├─ Export Graph Image...
│  ├─ Export Project Report...
│  ├─ Export Run Trace...
│  └─ Export Template Package...
├─ Project Settings...
├─ Print Graph...
└─ Exit
```

New Project opens the project wizard and creates a full project scaffold. New From Template starts from a predefined workflow. Open Project loads an existing `.pfcproj` project. Open Recent gives quick access to recent projects. Close Project checks for unsaved changes before closing. Save saves the active resource. Save As saves the active resource under another name. Save All writes all modified resources. Import commands bring existing PocketFlow projects, graph files, prompts, or custom node types into the current project. Export commands generate runnable PocketFlow code, graph images, reports, traces, or reusable template packages. Project Settings opens project configuration. Print Graph prints the active graph. Exit closes the application.

## Edit Menu

```text
Edit
├─ Undo
├─ Redo
├─ Cut
├─ Copy
├─ Paste
├─ Duplicate
├─ Delete
├─ Select All
├─ Find...
├─ Find in Project...
├─ Replace...
├─ Rename...
├─ Preferences...
└─ Keyboard Shortcuts...
```

Undo and Redo reverse or reapply graph, inspector, and editor changes. Cut, Copy, Paste, Duplicate, Delete, and Select All operate according to the active context. Find searches the active editor or graph. Find in Project searches all project resources. Replace updates text in the active editor or, with confirmation, across the project. Rename updates object names and related references. Preferences controls application-level behavior. Keyboard Shortcuts lets users inspect and customize key bindings.

## View Menu

```text
View
├─ Panels
│  ├─ Project Explorer
│  ├─ Component Palette
│  ├─ Object Inspector
│  ├─ Problems
│  ├─ Run Log
│  ├─ Shared Store Viewer
│  ├─ Prompt Preview
│  ├─ Generated Code
│  ├─ Python Editor
│  ├─ Markdown Editor
│  ├─ YAML Editor
│  └─ Test Results
├─ Zoom In
├─ Zoom Out
├─ Zoom to Fit
├─ Actual Size
├─ Grid
│  ├─ Show Grid
│  ├─ Snap to Grid
│  └─ Grid Settings...
├─ Theme
│  ├─ System
│  ├─ Light
│  └─ Dark
├─ Layout
│  ├─ Reset Layout
│  ├─ Save Layout...
│  └─ Load Layout...
└─ Full Screen
```

The View menu controls panels, zoom, grid, theme, layout, and full-screen behavior. Panel toggles allow the workspace to adapt to graph design, code editing, prompt editing, debugging, or documentation work. Zoom and grid commands operate on the graph designer. Theme and layout commands control visual comfort and workspace arrangement.

## Project Menu

```text
Project
├─ Validate Project
├─ Generate Code
├─ Regenerate All Generated Files
├─ Clean Generated Files
├─ Open Project Folder
├─ Open Terminal Here
├─ Git
│  ├─ Initialize Repository
│  ├─ Commit Changes...
│  ├─ Show Changes
│  └─ Create Restore Point
├─ Project Settings...
├─ Provider Profiles...
├─ Shared Store Schema...
├─ Manage Templates...
└─ Package Project...
```

Validate Project runs all project checks. Generate Code updates generated Python for selected resources. Regenerate All Generated Files rebuilds all generated output and should recommend a Git checkpoint first. Clean Generated Files removes only generated artifacts. Open Project Folder and Open Terminal Here help users work outside the GUI. Git commands support local safety checkpoints. Project Settings, Provider Profiles, Shared Store Schema, and Manage Templates open specialized project configuration tools. Package Project creates distributable archives.

## Flow Menu

```text
Flow
├─ New Flow...
├─ New Subflow...
├─ Rename Flow...
├─ Duplicate Flow
├─ Delete Flow
├─ Set Start Node
├─ Flow Properties...
├─ Auto Layout
├─ Validate Active Flow
├─ Run Active Flow
├─ Generate Flow Code
├─ Convert Selection to Subflow...
└─ Manage Flow Parameters...
```

The Flow menu manages top-level flows and reusable subflows. It creates, renames, duplicates, deletes, validates, runs, and generates code for flows. Set Start Node defines the entry point. Auto Layout arranges the graph. Convert Selection to Subflow packages selected nodes into a reusable component. Manage Flow Parameters edits subflow and batch-flow parameters.

## Node Menu

```text
Node
├─ New Custom Node Type...
├─ Edit Node Type...
├─ Duplicate Node Type...
├─ Delete Node Type...
├─ Add Selected Node to Palette...
├─ Generate Node Skeleton
├─ Open Node Python Code
├─ Open Node Metadata YAML
├─ Open Node Prompt
├─ Validate Selected Node
├─ Run Selected Node
├─ Create Test for Selected Node
└─ Manage Node Libraries...
```

The Node menu manages node instances and reusable node types. New Custom Node Type launches the wizard for inherited components. Edit, Duplicate, and Delete operate on reusable node type definitions. Add Selected Node to Palette converts a configured instance into a reusable component. Skeleton, Python, YAML, and Prompt commands open implementation resources. Validate, Run, and Create Test help debug nodes in isolation.

## Run Menu

```text
Run
├─ Run Project
├─ Run Active Flow
├─ Run Selected Node
├─ Debug Active Flow
├─ Step Into Node
├─ Step Over Node
├─ Continue
├─ Stop
├─ Restart Run
├─ Breakpoints
│  ├─ Toggle Breakpoint
│  ├─ Clear All Breakpoints
│  └─ Breakpoint Manager...
├─ Run Tests
├─ Run Selected Test
├─ Configure Run...
└─ Open Latest Run Report
```

The Run menu controls execution and debugging. Run Project uses the configured entry flow. Run Active Flow executes the open flow. Run Selected Node tests one node with sample shared-store data. Debug Active Flow starts step debugging. Step Into, Step Over, Continue, Stop, and Restart control execution. Breakpoint commands manage debug stops. Test commands run pytest. Configure Run selects provider, initial shared store, trace level, and max-step guards.

## Tools Menu

```text
Tools
├─ Provider Manager...
├─ Ollama Model Browser...
├─ Tool Registry...
├─ Prompt Library...
├─ Shared Store Inspector...
├─ Validate Python Environment
├─ Install/Update Dependencies...
├─ External Editors...
├─ Security Policy...
├─ Format Code
├─ Lint Project
└─ Options...
```

The Tools menu provides supporting utilities. Provider Manager configures LLM endpoints. Ollama Model Browser inspects local models. Tool Registry manages callable tools. Prompt Library manages reusable prompts. Shared Store Inspector edits and debugs shared state. Python environment validation checks dependencies. External Editors configures VS Code, Vim, Gedit, PyCharm, or other editors. Security Policy controls dangerous operations. Format and Lint operate on project code and metadata.

## Window Menu

```text
Window
├─ New Window
├─ Split Editor Right
├─ Split Editor Down
├─ Close Active Panel
├─ Close All Editors
├─ Next Tab
├─ Previous Tab
├─ Activate Graph Designer
├─ Activate Inspector
├─ Activate Project Explorer
└─ Restore Default Workspace
```

The Window menu manages workspace layout, multi-window use, editor splitting, tab navigation, and panel focus. It helps users work efficiently on large projects or multi-monitor setups.

## Help Menu

```text
Help
├─ PocketFlow Creator Help
├─ PocketFlow Quick Reference
├─ Node Type Authoring Guide
├─ Prompt Authoring Guide
├─ Keyboard Shortcuts
├─ Example Projects
├─ Report Issue...
├─ Show Log Folder
├─ About PocketFlow Creator
└─ About Qt/PySide
```

The Help menu provides documentation, examples, issue reporting, logs, and version information. The PocketFlow reference explains core concepts; the authoring guides explain custom node types and prompt design.

## Project Explorer

```text
Project Explorer
DocumentSummarizer
├─ Flows
├─ Graphs
├─ Prompts
├─ Node Types
├─ Tools
├─ Shared Store
├─ Source
├─ Tests
└─ Exports
```

The Project Explorer organizes all project resources. Flows open graph views. Prompts open Markdown editors. Node Types open YAML metadata and Python code. Tools open tool definitions. Shared Store opens schema and sample data. Source contains generated and custom Python. Tests and Exports contain validation and output artifacts.

## Component Palette

```text
Component Palette
Core: Start, Stop, Basic, Router
LLM: LLM Prompt, JSON LLM, Classifier, Critic/Judge
Tools: Python Tool, File Reader, File Writer, Shell Command
Control: Human Review, Error Handler, Loop Controller
Batch: Batch, Map, Reduce
Custom: user-defined node types
```

The Component Palette is the RAD component toolbox. Users drag components onto the graph or select a component and click the canvas. Custom node types appear here after creation or import.

## Graph Designer

```text
+---------------------+      success      +-----------------------+
| Load Document       |------------------->| Summarize Document    |
| Type: File Reader   |                    | Type: LLM Prompt Node |
| Writes: document.text                    | Reads: document.text  |
| success      o      |                    | success          o    |
| error        o      |                    | error            o    |
+---------------------+                    +-----------------------+
```

The Graph Designer is the workflow design surface. Node boxes display names, types, important properties, shared-store reads/writes, and action output ports. Edges represent PocketFlow action transitions. The background represents the selected flow and exposes flow properties when selected.

## Object Inspector

```text
Object: SummarizeDocument
Type: LLM Prompt Node
[General]
[LLM]
[Prompt]
[Shared Store]
[Actions]
[Retry]
[Python Hooks]
[Generated Code]
```

The Object Inspector is the heart of the RAD experience. It edits whichever object is selected: project, flow, node, edge, prompt, tool, shared-store key, or custom node type. For node instances it controls general fields, provider settings, prompts, shared-store reads/writes, actions, retry behavior, optional Python hooks, and generated code mapping.

## Python Editor

```text
Python Editor: src/project/custom/verified_json_llm.py
[Save] [Format] [Lint] [Run Test] [Generate Skeleton] [Open External Editor]
```

The Python editor supports custom node classes, tool functions, custom hooks, and tests. Generated files should open read-only by default. Custom files are user-owned and protected from regeneration.

## Markdown Prompt Editor

```text
Markdown Prompt Editor: prompts/summarize.md
[Save] [Preview] [Insert Variable] [Estimate Tokens] [Test Prompt]
Editor | Preview
```

The Markdown editor is primarily for prompts. It supports shared-store variable insertion, preview, token estimates, missing-variable warnings, and prompt testing with sample shared-store data.

## YAML Editor

```text
YAML Editor: node_types/verified_json_llm.yaml
[Save] [Format] [Validate Schema] [Open External Editor]
```

The YAML editor handles project metadata, node type definitions, graph files, tool definitions, provider profiles, and shared-store schemas. It must validate files against schemas and show friendly error messages.

## Shared Store Designer

```text
Shared Store Schema
Tree: document.path, document.text, document.summary, project.audience
Properties: type, required, default, description, constraints
Sample Data: YAML/JSON fixture for tests and prompt previews
```

The Shared Store Designer defines expected workflow state. It gives prompts and nodes a common vocabulary and enables validation of reads/writes.

## Custom Node Type Wizard

```text
New Custom Node Type
Display Name
Node Type ID
Category
Base Type
Python Class Name
Module Path
Properties
Actions
Shared Store Reads/Writes
Code Mode
```

The Custom Node Type Wizard creates reusable components. Custom nodes may inherit from PocketFlow base classes, built-in node types, or other custom node types.

## Provider Manager

```text
+─────────────────────────────────────────────────────────────────+
| Provider Manager                                          [X]    |
+─────────────────────┬───────────────────────────────────────────+
| Profiles            | Profile Settings                          |
| ├─ Local Ollama ★   | Name: Local Ollama                       |
| ├─ OpenAI Prod      | API type: Ollama (local)                |
| └─ Claude Haiku     | Base URL: http://localhost:11434        |
|                     | Default model: qwen2.5-coder:14b       |
| [+ Add]             | Timeout: 120 s                          |
| [Delete]            | API Key: (none)                         |
| [Set Default ★]     |                                         |
|                     | [Test Connection] ✓ Connection OK      |
|                     |                                         |
|                     | ☐ Include API keys in project file     |
|                     |                                    [OK] |
+─────────────────────────────────────────────────────────────────+
```

The Provider Manager allows users to:
- Create named provider profiles (Ollama, LM Studio, OpenAI, Anthropic, Google Gemini, etc.)
- Configure base URL (with sensible defaults for each type, customizable for custom ports/hostnames)
- Set default model for each provider
- Store API keys securely (in system settings by default, or environment variables)
- Test connections before use with immediate feedback
- Set a default provider for workflows
- Optionally include API keys in project files for portable/shareable projects

See [docs/13_provider_setup.md](../docs/13_provider_setup.md) for comprehensive provider setup instructions.

## Tool Registry

```text
Tool Registry
Tool name, Python function, safety level, timeout, input schema, output schema
```

The Tool Registry defines callable tools for Tool Nodes. Safety metadata is required for shell, network, file-write, or destructive operations.

## Run Configuration

```text
Entry Flow
Provider Profile
Real/Mock LLM mode
Initial Shared Store
Max Steps
Timeout
Trace Level
Validate Before Run
```

Run Configuration defines how the project executes or debugs. Mock provider mode should be available for tests.

## Debug View

```text
Graph highlights current node
Current Node panel shows phase/action/timing/retry count
Shared Store Diff shows state changes
Prompt Preview/Response shows LLM inputs and outputs
```

The Debug View makes workflows inspectable. Users can step through nodes, inspect prompts, see selected actions, and view shared-store changes.
