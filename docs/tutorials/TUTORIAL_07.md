# Tutorial 7: Hello World — Single Node Q&A

**PocketFlow example:** `pocketflow-hello-world`
**What you'll learn:** The simplest possible flow: one question, one answer.

### Graph

```
[Start] --default--> [AskLLM] --default--> [Stop]
```

### Steps

1. New project: `tut_hello_world`
2. Add nodes: Start, LLM Prompt Node (title: `Ask LLM`), Stop Node
3. Wire: Start → Ask LLM (action: `default`), Ask LLM → Stop (action: `default`)
4. Auto Layout; Zoom to Fit
5. Double-click **Ask LLM** to open code editor

```python
class AskLlm(Node):
    def prep(self, shared):
        return shared.get("question", "What is PocketFlow?")

    def exec(self, prep_res):
        return call_llm(prep_res)  # your LLM helper

    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res
        print("Answer:", exec_res)
        return "default"
```

6. Create `prompts/main.md`:
   ```
   Answer the following question concisely: {question}
   ```
7. Run > Run Active Flow — check Run Log and Shared Store tabs

---
