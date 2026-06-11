# Tutorial 20: Subflow Composition

**What you'll learn:** Embed a reusable sub-graph inside a parent flow using the Subflow Node.

### Steps

1. Create a project with two graphs:
   - `graphs/main.pfcgraph.yaml` — the parent flow
   - `graphs/summarizer.pfcgraph.yaml` — a reusable summarization sub-flow

2. Build `summarizer.pfcgraph.yaml`:
   - Start → Load Text → Summarize (LLM) → Stop

3. In `main.pfcgraph.yaml`, add a **Subflow Node**:
   - Drag **Subflow Node** from the palette
   - In Object Inspector, the **[Subflow]** section appears
   - Set `subflow_ref` to `graphs/summarizer.pfcgraph.yaml`

4. Validate — if `subflow_ref` is set correctly, no PFCE2102 error appears

5. Wire parent flow around the Subflow Node as usual

> **Note:** Subflow recursive execution is a planned enhancement (T-B05 MVP — passthrough only).
> The `subflow_ref` property documents intent and passes through the runner with the ref recorded
> in the shared store.

---
