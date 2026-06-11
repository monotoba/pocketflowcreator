# Tutorial 10: Multi-Stage Workflow — Article Writer

**PocketFlow example:** `pocketflow-workflow`
**What you'll learn:** Chain LLM calls through distinct stages: outline → draft → style.

### Graph

```
[Start] → [GenerateOutline] → [WriteDraft] → [ApplyStyle] → [Save] → [Stop]
```

### Steps

1. New project: `tut_workflow`
2. Add five nodes (Start, 3× LLM Prompt Node, Stop)
3. Set titles: `Generate Outline`, `Write Draft`, `Apply Style`
4. For each LLM node, set a separate prompt file:
   - `prompts/outline.md`
   - `prompts/draft.md`
   - `prompts/style.md`
5. Wire sequentially; Auto Layout
6. Create `prompts/outline.md`:
   ```
   Create a 5-point outline for an article about: {topic}
   Return only the outline as a numbered list.
   ```
7. Create `prompts/draft.md`:
   ```
   Write a 3-paragraph article using this outline:
   {outline}
   ```
8. Create `prompts/style.md`:
   ```
   Rewrite this article in an engaging, professional tone:
   {draft}
   ```
9. Double-click **Generate Outline**:

```python
class GenerateOutline(Node):
    def prep(self, shared):
        topic = shared.get("topic", "the future of AI")
        return open("prompts/outline.md").read().format(topic=topic)

    def exec(self, prep_res):
        return call_llm(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["outline"] = exec_res
        return "default"
```

10. Implement Write Draft and Apply Style similarly, reading `outline` / `draft` from shared store

---
