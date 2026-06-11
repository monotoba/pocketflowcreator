# Tutorial 12: Agent with Tools

**PocketFlow example:** `pocketflow-agent`
**What you'll learn:** Build an LLM agent that decides which tool to call based on a question.

### Graph

```
[Start] → [Decide] ──search──→ [WebSearch]  → [Decide]
                  └─calculate──→ [Calculator] → [Decide]
                  └─answer────→ [FinalAnswer] → [Stop]
```

### Steps

1. New project: `tut_agent`
2. Add nodes:
   - Start, Router Node (title: `Decide`, Actions: `search, calculate, answer`)
   - Basic Node × 2 (Web Search, Calculator)
   - Basic Node (Final Answer)
   - Stop
3. Wire the loop: Web Search → Decide, Calculator → Decide
4. Wire the exit: Final Answer → Stop
5. Double-click **Decide**:

```python
class Decide(Node):
    TOOLS = ["search", "calculate", "answer"]

    def prep(self, shared):
        history = shared.get("tool_history", [])
        question = shared.get("question", "")
        return question, history

    def exec(self, prep_res):
        question, history = prep_res
        history_text = "\n".join(f"- {h}" for h in history)
        prompt = f"""Question: {question}
Previous steps: {history_text or 'none'}
Choose the next action: search, calculate, or answer."""
        action = call_llm(prompt).strip().lower()
        return action if action in self.TOOLS else "answer"

    def post(self, shared, prep_res, exec_res):
        shared.setdefault("tool_history", []).append(f"chose: {exec_res}")
        return exec_res
```

6. Double-click **Web Search**:

```python
class WebSearch(Node):
    def prep(self, shared):
        return shared.get("question", "")

    def exec(self, prep_res):
        # Replace with real search API
        return f"[search result for: {prep_res}]"

    def post(self, shared, prep_res, exec_res):
        shared["search_result"] = exec_res
        shared["tool_history"].append(f"searched: {exec_res}")
        return "default"
```

---
