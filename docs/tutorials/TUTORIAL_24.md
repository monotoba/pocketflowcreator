# Tutorial 24: Memory — Short-Term and Long-Term Context

**PocketFlow example:** `pocketflow-memory`
**What you'll learn:** Maintain two memory layers — recent conversation (short-term) and condensed summaries (long-term).

### Graph

```
[Start] → [GetInput] → [UpdateShortTerm] → [ShouldCondense?]
    ──yes──→ [CondenseToLongTerm] → [CallLLM] → [GetInput]
    ──no───→                        [CallLLM] → [GetInput]
[GetInput] --exit--> [Stop]
```

### Steps

1. New project: `tut_memory`
2. Build the graph with a Router Node for `ShouldCondense?` (Actions: `yes, no`)
3. In Shared Store Designer, define:
   - `short_term_history` (array) — last N messages
   - `long_term_summary` (string) — condensed prior context
   - `condensation_threshold` (integer, default: 10)

4. Double-click **Should Condense?**:

```python
class ShouldCondense(Node):
    THRESHOLD = 10

    def prep(self, shared):
        return len(shared.get("short_term_history", []))

    def exec(self, prep_res):
        return "yes" if prep_res >= self.THRESHOLD else "no"

    def post(self, shared, prep_res, exec_res):
        return exec_res
```

5. Double-click **Condense To Long Term**:

```python
class CondenseToLongTerm(Node):
    def prep(self, shared):
        history = shared.get("short_term_history", [])
        old_summary = shared.get("long_term_summary", "")
        return history, old_summary

    def exec(self, prep_res):
        history, old_summary = prep_res
        msgs = "\n".join(f"{m['role']}: {m['content']}" for m in history)
        prompt = f"Existing summary: {old_summary}\n\nNew messages:\n{msgs}\n\nCreate updated summary:"
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["long_term_summary"] = exec_res
        shared["short_term_history"] = []  # reset short-term
        return "default"
```

---
