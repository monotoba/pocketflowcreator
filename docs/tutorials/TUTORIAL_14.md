# Tutorial 14: Map-Reduce / Batch Processing

**PocketFlow example:** `pocketflow-map-reduce`
**What you'll learn:** Use a Batch Node to process many items in parallel and reduce results.

### Graph

```
[Start] → [LoadItems] → [ProcessEach (BatchNode)] → [Aggregate] → [Stop]
```

### Steps

1. New project: `tut_map_reduce`
2. Add nodes: Start, Basic Node (Load Items), **Batch Node** (Process Each), Basic Node (Aggregate), Stop
3. Double-click **Load Items**:

```python
class LoadItems(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        # Load a list of items to evaluate
        return ["Resume A text...", "Resume B text...", "Resume C text..."]

    def post(self, shared, prep_res, exec_res):
        shared["items"] = exec_res
        return "default"
```

4. Double-click **Process Each** (BatchNode):

```python
class ProcessEach(BatchNode):
    def prep(self, shared):
        # Return the list — BatchNode calls exec once per item
        return shared["items"]

    def exec(self, item):
        prompt = f"Rate this resume 1-10 and explain why:\n{item}"
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        # exec_res is a list of results, one per item
        shared["ratings"] = exec_res
        return "default"
```

5. Double-click **Aggregate**:

```python
class Aggregate(Node):
    def prep(self, shared):
        return shared.get("ratings", [])

    def exec(self, prep_res):
        prompt = f"Summarise these {len(prep_res)} resume evaluations:\n" + \
                 "\n".join(f"{i+1}. {r}" for i, r in enumerate(prep_res))
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        shared["summary"] = exec_res
        return "default"
```

---
