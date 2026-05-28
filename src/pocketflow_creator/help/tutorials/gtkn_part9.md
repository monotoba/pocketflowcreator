# Part 9 — Data and Vector Nodes

This part covers four nodes that implement a Retrieval-Augmented Generation (RAG)
pipeline from scratch: chunking documents, generating embeddings, indexing them in a
vector store, and retrieving the most relevant chunks at query time.

**Prerequisite:** Complete Part 6 (RAG Node) for context on how RAG fits together;
that part uses the all-in-one RAG Node while this part shows the composable building
blocks.

---

## Tutorial T-N29: Text Chunk Node

### What it does

The **Text Chunk Node** splits a long text into overlapping or non-overlapping segments
of a fixed token/character size. Downstream Embed Nodes then process each chunk
independently, enabling retrieval from documents longer than a single LLM context
window.

### Use cases

- Pre-processing a PDF or web page before embedding
- Splitting chat history into retrievable segments
- Any task where a document must be divided before vector indexing

### What you'll build

A flow — **Start → DocChunker → Stop** — that splits a 200-word article into
chunks of 50 characters with a 10-character overlap.

### Step-by-step

**Step 1: Create project `gtkn_part9`.**

**Step 2: Drag a Text Chunk Node** named `DocChunker`.

**Step 3: Set Inspector properties:**

| Property | Value |
|---|---|
| `input_key` | `document` |
| `output_key` | `chunks` |
| `chunk_size` | `50` |
| `overlap` | `10` |
| `method` | `character` |

**Step 4: Wire Start → DocChunker → Stop.**

**Step 5: Paste the node code:**

```python
from pocketflow import Node

class DocChunker(Node):
    CHUNK_SIZE = 50
    OVERLAP = 10

    def prep(self, shared):
        return shared.get(
            "document",
            "PocketFlow is a minimalist LLM framework. "
            "It supports nodes, flows, and shared state. "
            "Async execution and batch processing are built in. "
            "The design is intentionally small and readable.",
        )

    def exec(self, prep_res):
        text = prep_res
        size = self.CHUNK_SIZE
        step = size - self.OVERLAP
        chunks = []
        start = 0
        while start < len(text):
            chunks.append(text[start : start + size])
            start += step
        return chunks

    def post(self, shared, prep_res, exec_res):
        shared["chunks"] = exec_res
        return "default"
```

**Step 6: Run and inspect the Shared Store.** You will see a list of 50-character
strings with 10-character overlaps between consecutive chunks.

### What you learned

- `chunk_size` and `overlap` trade retrieval precision against context coverage
- `method: character` is the simplest strategy; `token` uses a tokeniser for LLM-aligned splits
- The output is a list of strings — each string is one chunk ready for embedding

---

## Tutorial T-N30: Embed Node

### What it does

The **Embed Node** converts a list of text strings into dense vector embeddings using
a configured embedding model (e.g. `text-embedding-3-small`, `nomic-embed-text` via
Ollama). Each string becomes a float list; the list of embeddings is stored alongside
the original texts.

### Use cases

- Converting document chunks to vectors before indexing
- Embedding a user query before similarity search
- Generating semantic representations for clustering or classification

### What you'll build

Extend the flow from T-N29 to embed the chunks. The Embed Node processes the list
produced by `DocChunker`.

### Step-by-step

**Step 1: Add an Embed Node** named `ChunkEmbedder` after `DocChunker`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `input_key` | `chunks` |
| `output_key` | `embeddings` |
| `model` | _(leave empty — uses mock provider)_ |
| `batch_size` | `10` |

**Step 3: Re-wire: Start → DocChunker → ChunkEmbedder → Stop.**

**Step 4: Paste the Embedder code:**

```python
from pocketflow import Node

class ChunkEmbedder(Node):
    DIM = 4   # Mock embedding dimension; real models use 768 or 1536.

    def prep(self, shared):
        return shared.get("chunks", [])

    def exec(self, prep_res):
        chunks = prep_res
        # Production: batch-call the embedding API.
        # Here we simulate with deterministic pseudo-vectors.
        embeddings = []
        for i, chunk in enumerate(chunks):
            seed = sum(ord(c) for c in chunk[:10])
            vec = [(seed + i * j) % 100 / 100.0 for j in range(self.DIM)]
            embeddings.append(vec)
        return embeddings

    def post(self, shared, prep_res, exec_res):
        shared["embeddings"] = exec_res
        return "default"
```

**Step 5: Run and check** that `embeddings` is a list of float lists, one per chunk.

### What you learned

- The Embed Node maps N text strings to N float vectors in a single step
- `batch_size` controls how many texts are sent per API call to manage rate limits
- The output list is aligned with the input list — `chunks[i]` corresponds to `embeddings[i]`

---

## Tutorial T-N31: Vector Index Node

### What it does

The **Vector Index Node** builds an in-memory (or persistent) vector index from a
list of (text, embedding) pairs. The index object is stored in the shared store under
`index_key` and can be queried by a downstream Vector Retrieve Node.

### Use cases

- Building a searchable knowledge base from document chunks
- Caching an index for repeated queries within a single flow run
- Persisting an index to disk for reuse across flow runs

### What you'll build

Continue the pipeline: add a Vector Index Node that consumes `chunks` and `embeddings`
to build an index object.

### Step-by-step

**Step 1: Add a Vector Index Node** named `IndexBuilder` after `ChunkEmbedder`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `texts_key` | `chunks` |
| `embeddings_key` | `embeddings` |
| `index_key` | `vector_index` |
| `backend` | `memory` |

**Step 3: Re-wire to include `IndexBuilder`.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

class IndexBuilder(Node):
    def prep(self, shared):
        return {
            "texts": shared.get("chunks", []),
            "embeddings": shared.get("embeddings", []),
        }

    def exec(self, prep_res):
        texts = prep_res["texts"]
        embeddings = prep_res["embeddings"]
        # In production: use FAISS, Chroma, or similar.
        # Here we store a simple list-of-dicts as the index.
        return [
            {"text": t, "vector": v}
            for t, v in zip(texts, embeddings)
        ]

    def post(self, shared, prep_res, exec_res):
        shared["vector_index"] = exec_res
        return "default"
```

**Step 5: Run.** The shared store now contains `vector_index` — a list of
`{"text": ..., "vector": [...]}` dicts ready for cosine-similarity retrieval.

### What you learned

- The index is just a shared-store value — any node later in the flow can use it
- `backend: memory` is ephemeral; `backend: chroma` or `backend: faiss` uses persistence
- The index stores both the original text and the embedding so retrieval returns readable strings

---

## Tutorial T-N32: Vector Retrieve Node

### What it does

The **Vector Retrieve Node** encodes a query string, performs a nearest-neighbour
search against an existing index, and returns the top-k most similar text chunks.
The retrieved texts are stored under `results_key` and are typically fed into an LLM
node as context.

### Use cases

- The retrieval step of any RAG flow
- Finding the most relevant chunks before an LLM answers a question
- Semantic deduplication — finding near-duplicates in a corpus

### What you'll build

Complete the RAG pipeline: add a Vector Retrieve Node that answers the question
"What does PocketFlow support?" using the index built in T-N31.

### Step-by-step

**Step 1: Add a Vector Retrieve Node** named `ContextRetriever` after `IndexBuilder`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `query_key` | `question` |
| `index_key` | `vector_index` |
| `results_key` | `retrieved_context` |
| `top_k` | `2` |

**Step 3: Wire to `ContextRetriever → Stop`.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

class ContextRetriever(Node):
    TOP_K = 2

    def prep(self, shared):
        return {
            "query": shared.get("question", "What does PocketFlow support?"),
            "index": shared.get("vector_index", []),
        }

    def exec(self, prep_res):
        query = prep_res["query"]
        index = prep_res["index"]
        if not index:
            return []
        # Production: encode query + cosine similarity against index vectors.
        # Simulation: score by shared character count.
        def score(entry):
            return sum(1 for c in query if c in entry["text"])

        ranked = sorted(index, key=score, reverse=True)
        return [entry["text"] for entry in ranked[: self.TOP_K]]

    def post(self, shared, prep_res, exec_res):
        shared["retrieved_context"] = exec_res
        return "default"
```

**Step 5: Run and check:**

```
retrieved_context: [
  "PocketFlow is a minimalist LLM framework. It supports node...",
  "...Async execution and batch processing are built in...."
]
```

### What you learned

- The full RAG pipeline is: **DocChunker → ChunkEmbedder → IndexBuilder → ContextRetriever**
- `top_k` controls how many chunks are returned; more context improves answers but uses more tokens
- The retrieved text list feeds naturally into an LLM Prompt Node as `{{retrieved_context}}`

---

[↑ Series Index](gtkn_index.md)
[← Part 8](gtkn_part8.md)
[→ Part 10: Database and SQL Nodes](gtkn_part10.md)
