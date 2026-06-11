# Tutorial 4: The Code Editor — RAD Node Coding

**What you'll learn:** How double-clicking a node opens its implementation in the code editor, and how to write real node logic.

**Prerequisites:** Tutorial 2 — an open project with nodes on the canvas.

### How the Code File Works

Every graph has a companion code file at `code/<graph_stem>.py`.
When you **double-click a node** on the canvas:
1. The file is created if it doesn't exist
2. A class stub is added for that node (if not already there)
3. The **Python** tab opens and scrolls to that node's class

### Steps

1. Open the project from Tutorial 2
2. Double-click the **Ask LLM** node on the canvas
3. The Python tab opens, showing:

```python
# --- NODE_START: node_abc12345 ---
class AskLlm(Node):
    """llm_prompt_node: Ask LLM"""

    def prep(self, shared: dict) -> object:
        return None

    def exec(self, prep_res: object) -> object:
        return None

    def post(self, shared: dict, prep_res: object, exec_res: object) -> str:
        return "default"

# --- NODE_END: node_abc12345 ---
```

4. Edit the stub to implement real logic:

```python
# --- NODE_START: node_abc12345 ---
class AskLlm(Node):
    """llm_prompt_node: Ask LLM"""

    def prep(self, shared: dict) -> str:
        # Read the prompt template from disk
        prompt_path = shared.get("prompt_file", "prompts/hello.md")
        with open(prompt_path) as f:
            return f.read()

    def exec(self, prep_res: str) -> str:
        # Call the LLM (injected via shared["llm"])
        llm = shared.get("llm")
        return llm.complete(prep_res) if llm else f"[mock] {prep_res}"

    def post(self, shared: dict, prep_res: str, exec_res: str) -> str:
        shared["llm_response"] = exec_res
        print(exec_res)
        return "default"

# --- NODE_END: node_abc12345 ---
```

5. Save (Ctrl+S)

### Deleting a Node

- Select a node on the canvas
- Press **Delete** key
- The node is removed from the canvas AND its class is removed from `code/main.py`

---
