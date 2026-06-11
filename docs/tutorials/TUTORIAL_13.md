# Tutorial 13: Retrieval-Augmented Generation (RAG)

**PocketFlow example:** `pocketflow-rag`
**What you'll learn:** Index documents, retrieve relevant chunks, generate an answer.

### Graph

```
[Start] → [LoadDocs] → [EmbedChunks] → [StoreIndex] → [GetQuestion]
        → [RetrieveChunks] → [GenerateAnswer] → [Stop]
```

### Steps

1. New project: `tut_rag`
2. Add nodes for each stage; set Reads/Writes in Inspector:
   - **Load Docs** — Writes: `raw_docs`
   - **Embed Chunks** — Reads: `raw_docs`, Writes: `chunks, embeddings`
   - **Store Index** — Reads: `chunks, embeddings`, Writes: `index`
   - **Get Question** — Writes: `question`
   - **Retrieve Chunks** — Reads: `index, question`, Writes: `context`
   - **Generate Answer** — Reads: `context, question`, Writes: `answer`

3. Double-click **Load Docs** and implement document loading
4. Double-click **Embed Chunks**:

```python
class EmbedChunks(Node):
    def prep(self, shared):
        text = shared["raw_docs"]
        # Split into 500-char chunks
        return [text[i:i+500] for i in range(0, len(text), 500)]

    def exec(self, prep_res):
        # Replace with a real embedding model
        return [(chunk, [0.1] * 128) for chunk in prep_res]

    def post(self, shared, prep_res, exec_res):
        shared["chunks"] = [c for c, _ in exec_res]
        shared["embeddings"] = [e for _, e in exec_res]
        return "default"
```

5. Double-click **Generate Answer**:

```python
class GenerateAnswer(Node):
    def prep(self, shared):
        context = "\n".join(shared.get("context", []))
        question = shared.get("question", "")
        return f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"

    def exec(self, prep_res):
        return call_llm(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res
        print("Answer:", exec_res)
        return "default"
```

---
