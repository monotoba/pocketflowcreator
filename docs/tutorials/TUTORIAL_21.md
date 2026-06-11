# Tutorial 21: Exporting and Running a Standalone Project

**What you'll learn:** Export a Creator project as a runnable Python package independent of Creator.

### Steps

1. Open any completed project (e.g., Tutorial 7 Hello World)
2. File > Export PocketFlow Project… (Ctrl+E)
3. The exporter writes to `exports/<package_name>/`:
   ```
   exports/hello_world/
   ├── generated/
   │   ├── main_nodes.py       ← auto-generated Node subclasses
   │   └── main_flow.py        ← wires the flow with >> syntax
   ├── custom/
   │   └── main_custom.py      ← YOUR code (never overwritten)
   ├── tests/
   │   └── test_main.py        ← test scaffolding
   └── main.py                 ← entry point
   ```
4. Re-exporting: `generated/` is always overwritten; `custom/` is never touched
5. Run outside Creator:
   ```bash
   cd exports/hello_world
   pip install pocketflow
   python main.py
   ```

---
