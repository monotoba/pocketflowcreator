# Tutorial 23: Streaming Output

**PocketFlow example:** `pocketflow-streaming`
**What you'll learn:** Design a flow that produces incremental output visible to the user in real time.

### Graph

```
[Start] → [StreamLLM] → [PrintChunks] → [Stop]
```

### Steps

1. New project: `tut_streaming`
2. Add a Basic Node (title: `Stream LLM`) with Writes: `chunks`
3. Double-click **Stream LLM**:

```python
class StreamLlm(Node):
    def prep(self, shared):
        return shared.get("prompt", "Tell me a story in 5 sentences.")

    def exec(self, prep_res):
        # Replace with your streaming LLM client
        full_text = call_llm(prep_res)
        # Simulate streaming by splitting into words
        return full_text.split()

    def post(self, shared, prep_res, exec_res):
        shared["chunks"] = exec_res
        for chunk in exec_res:
            print(chunk, end=" ", flush=True)
        print()
        return "default"
```

4. In Run Log during execution, watch chunks accumulate in the Shared Store tab

---
