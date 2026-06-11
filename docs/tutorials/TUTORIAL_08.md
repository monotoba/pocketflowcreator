# Tutorial 8: Chat with History

**PocketFlow example:** `pocketflow-chat`
**What you'll learn:** Maintain conversation history in the shared store across turns.

### Graph

```
[Start] --default--> [GetInput] --continue--> [CallLLM] --default--> [PrintReply]
                                    ^                                      |
                                    └──────────────────────────────────────┘
                                              (loop back)
[GetInput] --exit--> [Stop]
```

### Steps

1. New project: `tut_chat`
2. Add nodes:
   - **Start Node** (title: `Start`)
   - **Basic Node** (title: `Get Input`) — Actions: `continue, exit`
   - **LLM Prompt Node** (title: `Call LLM`) — Actions: `default`
   - **Basic Node** (title: `Print Reply`) — Actions: `default`
   - **Stop Node** (title: `Stop`)
3. Wire edges:
   - Start → Get Input (`default`)
   - Get Input → Call LLM (`continue`)
   - Get Input → Stop (`exit`)
   - Call LLM → Print Reply (`default`)
   - Print Reply → Get Input (`default`)  ← this creates the loop
4. Auto Layout; notice the loop in the graph
5. Double-click **Get Input**:

```python
class GetInput(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        user_input = input("You: ").strip()
        return user_input

    def post(self, shared, prep_res, exec_res):
        if exec_res.lower() in ("quit", "exit", "bye"):
            return "exit"
        shared.setdefault("history", [])
        shared["history"].append({"role": "user", "content": exec_res})
        return "continue"
```

6. Double-click **Call LLM**:

```python
class CallLlm(Node):
    def prep(self, shared):
        return shared.get("history", [])

    def exec(self, prep_res):
        return call_llm_with_history(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["history"].append({"role": "assistant", "content": exec_res})
        shared["last_reply"] = exec_res
        return "default"
```

7. Double-click **Print Reply**:

```python
class PrintReply(Node):
    def prep(self, shared):
        return shared.get("last_reply", "")

    def exec(self, prep_res):
        print(f"Assistant: {prep_res}")
        return None

    def post(self, shared, prep_res, exec_res):
        return "default"
```

8. Run > Debug Active Flow; step through the loop

---
