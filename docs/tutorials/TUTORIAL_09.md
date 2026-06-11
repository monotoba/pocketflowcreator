# Tutorial 9: Structured Output — Resume Data Extraction

**PocketFlow example:** `pocketflow-structured-output`
**What you'll learn:** Use an LLM to extract typed fields from unstructured text.

### Graph

```
[Start] --default--> [LoadResume] --default--> [ExtractFields] --default--> [ValidateOutput] --default--> [Stop]
```

### Steps

1. New project: `tut_structured_output`
2. Add nodes: Start, Basic Node × 3 (Load Resume, Extract Fields, Validate Output), Stop
3. Wire sequentially with `default` actions
4. In Object Inspector for **Extract Fields**:
   - Reads: `resume_text`
   - Writes: `extracted_data`

5. Double-click **Load Resume**:

```python
class LoadResume(Node):
    def prep(self, shared):
        return shared.get("resume_path", "sample_resume.txt")

    def exec(self, prep_res):
        with open(prep_res) as f:
            return f.read()

    def post(self, shared, prep_res, exec_res):
        shared["resume_text"] = exec_res
        return "default"
```

6. Double-click **Extract Fields**:

```python
class ExtractFields(Node):
    def prep(self, shared):
        return shared["resume_text"]

    def exec(self, prep_res):
        prompt = f"""Extract from this resume:
- name
- email
- years_of_experience (number)
- skills (list)

Resume:
{prep_res}

Respond as JSON only."""
        raw = call_llm(prompt)
        import json
        return json.loads(raw)

    def post(self, shared, prep_res, exec_res):
        shared["extracted_data"] = exec_res
        return "default"
```

7. Use the **Shared Store Designer** (Tools > Shared Store Inspector) to define the schema:
   - Key: `extracted_data`, Type: `object`
   - Key: `resume_text`, Type: `string`

---
