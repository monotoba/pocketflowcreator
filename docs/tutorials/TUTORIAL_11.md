# Tutorial 11: Conditional Routing — Chat Guardrail

**PocketFlow example:** `pocketflow-chat-guardrail`
**What you'll learn:** Use a Router Node to branch flow based on LLM classification.

### Graph

```
[Start] → [ClassifyInput] ──on_topic──→ [AnswerQuestion] → [Stop]
                          └─off_topic──→ [Redirect]       → [Stop]
```

### Steps

1. New project: `tut_guardrail`
2. Add nodes:
   - **Start Node**
   - **Router Node** (title: `Classify Input`) — Actions: `on_topic, off_topic`
   - **LLM Prompt Node** (title: `Answer Question`)
   - **Basic Node** (title: `Redirect`)
   - **Stop Node**
3. Wire:
   - Start → Classify Input (`default`)
   - Classify Input → Answer Question (`on_topic`)
   - Classify Input → Redirect (`off_topic`)
   - Answer Question → Stop (`default`)
   - Redirect → Stop (`default`)
4. Double-click **Classify Input**:

```python
class ClassifyInput(Node):
    def prep(self, shared):
        return shared.get("user_question", "")

    def exec(self, prep_res):
        prompt = f"""Is this question about travel? Answer only YES or NO.
Question: {prep_res}"""
        answer = call_llm(prompt).strip().upper()
        return "on_topic" if answer == "YES" else "off_topic"

    def post(self, shared, prep_res, exec_res):
        return exec_res  # routes the flow
```

5. Notice: the Router Node's `post()` return value selects which edge to follow
6. Validate — the validator checks that `on_topic` and `off_topic` edges exist from Classify Input
7. Run > Validate Project — confirms routing is correct

---
