# Tutorial 15: Human-in-the-Loop

**PocketFlow example:** `pocketflow-fastapi-hitl` / `pocketflow-cli-hitl`
**What you'll learn:** Pause execution at a Human Review Node for user approval before continuing.

### Graph

```
[Start] → [DraftContent] → [Human Review] ──approved──→ [Publish] → [Stop]
                                           └─rejected────→ [Revise]  → [Human Review]
```

### Steps

1. New project: `tut_hitl`
2. Add nodes:
   - Start, LLM Prompt (Draft Content)
   - **Human Review Node** (title: `Review Draft`) — Actions: `approved, rejected`
   - Basic Node (Publish), Basic Node (Revise), Stop
3. Wire with the approval loop (Revise → Review Draft)
4. Double-click **Review Draft**:

```python
class ReviewDraft(Node):
    def prep(self, shared):
        return shared.get("draft", "")

    def exec(self, prep_res):
        print("\n=== DRAFT FOR REVIEW ===")
        print(prep_res)
        print("=========================")
        decision = input("Approve? (yes/no): ").strip().lower()
        return decision

    def post(self, shared, prep_res, exec_res):
        if exec_res in ("yes", "y", "approve", "approved"):
            return "approved"
        feedback = input("Feedback for revision: ").strip()
        shared["feedback"] = feedback
        return "rejected"
```

5. Double-click **Revise**:

```python
class Revise(Node):
    def prep(self, shared):
        return shared.get("draft", ""), shared.get("feedback", "")

    def exec(self, prep_res):
        draft, feedback = prep_res
        prompt = f"Revise this draft based on feedback:\nDraft: {draft}\nFeedback: {feedback}"
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["draft"] = exec_res
        return "default"
```

6. Run > Debug Active Flow to step through with breakpoints at Review Draft

---
