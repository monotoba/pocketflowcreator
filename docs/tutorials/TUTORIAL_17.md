# Tutorial 17: Multi-Agent System

**PocketFlow example:** `pocketflow-multi-agent` / `pocketflow-debate`
**What you'll learn:** Two agents with different roles run in a debate or adversarial pattern.

### Graph

```
[Start] → [AgentA: Propose] → [AgentB: Challenge] → [Judge] ──continue──→ [AgentA]
                                                             └─conclude────→ [Summary] → [Stop]
```

### Steps

1. New project: `tut_debate`
2. Add nodes with descriptive titles; set Actions appropriately
3. Double-click **Agent A: Propose**:

```python
class AgentAPropose(Node):
    def prep(self, shared):
        topic = shared.get("topic", "AI regulation")
        history = shared.get("debate_history", [])
        return topic, history

    def exec(self, prep_res):
        topic, history = prep_res
        context = "\n".join(history[-4:])  # last 4 turns
        prompt = f"""You are arguing IN FAVOR of: {topic}
Previous debate:
{context}
Make your strongest argument (2-3 sentences):"""
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared.setdefault("debate_history", []).append(f"PRO: {exec_res}")
        return "default"
```

4. Implement Agent B as the counter-argument and Judge to evaluate the winner
5. Run > Run Active Flow to watch the debate unfold in Run Log

---
