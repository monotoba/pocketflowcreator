# Tutorial 16: LLM-as-Judge / Evaluator Loop

**PocketFlow example:** `pocketflow-judge`
**What you'll learn:** Use one LLM to generate content and another to evaluate and improve it.

### Graph

```
[Start] → [Generate] → [Evaluate] ──pass────→ [Stop]
                    ^              └─fail──────→ [Refine] → [Generate]
```

### Steps

1. New project: `tut_judge`
2. Add nodes:
   - Start, LLM Prompt (Generate), Router Node (Evaluate, Actions: `pass, fail`),
     LLM Prompt (Refine), Stop
3. Wire with loop: Refine → Generate
4. Add a safety counter in shared store to prevent infinite loops:

```python
class Evaluate(Node):
    MAX_ITERATIONS = 3

    def prep(self, shared):
        return shared.get("output", ""), shared.get("iteration", 0)

    def exec(self, prep_res):
        output, iteration = prep_res
        if iteration >= self.MAX_ITERATIONS:
            return "pass"  # force exit after max iterations
        prompt = f"""Evaluate this output. Is the quality good enough?
Output: {output}
Answer only PASS or FAIL."""
        verdict = call_llm(prompt).strip().upper()
        return "pass" if verdict == "PASS" else "fail"

    def post(self, shared, prep_res, exec_res):
        shared["iteration"] = shared.get("iteration", 0) + 1
        return exec_res
```

---
