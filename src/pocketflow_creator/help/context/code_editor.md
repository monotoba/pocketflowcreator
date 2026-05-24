# Code Editor

The bottom **Python** tab is a syntax-highlighting editor for the graph's companion code file.

## The Code File

Every graph has a companion file at `code/<graph_stem>.py`. This file:
- Is created automatically when you first double-click a node
- Contains one class stub per node, delimited by marker comments
- Is your working implementation file during design time
- Is merged into `custom/` on export (existing files are never overwritten)

## Opening the Editor

- **Double-click a node** on the canvas — the file opens and scrolls to that node's class
- **Project Explorer > double-click a `.py` file** — opens the file in the Python tab

## Marker Format

```python
# --- NODE_START: <node_id> ---
class MyNode(Node):
    """<type_id>: <title>"""

    def prep(self, shared: dict) -> object:
        return None

    def exec(self, prep_res: object) -> object:
        return None

    def post(self, shared: dict, prep_res: object, exec_res: object) -> str:
        return "default"

# --- NODE_END: <node_id> ---
```

**Do not remove** the `NODE_START` / `NODE_END` marker comments. They allow Creator to:
- Locate the class for double-click navigation
- Remove the class when you delete the node from the canvas

## Syntax Highlighting

Python keywords, strings, comments, and decorators are highlighted.
The editor does not run a language server — for full IDE features, open the file in your
preferred external editor (the file is plain text).

## Saving

- **Ctrl+S** — saves the currently active editor tab to disk
- **Ctrl+Shift+S** (Save All) — saves all open editor tabs

## YAML and Markdown Editors

The **YAML** and **Markdown** tabs work the same way:
- **YAML** — validates on every keystroke; parse errors appear in the status bar
- **Markdown** — live preview updates in the right pane of the splitter

[← Help Index](../index.md) | [Tutorial 4: The Code Editor](../tutorials/part1_fundamentals.md)
