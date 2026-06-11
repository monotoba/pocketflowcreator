# Exercise A: Build a Complete News Summariser

**Skills exercised:** Multi-stage workflow, LLM chaining, Shared Store Designer, custom node type, export and run

**Objective:** Fetch news headlines, summarise each one, and produce a daily digest.

1. Create project `news_summariser`
2. Design the graph:
   - Fetch Headlines (Basic Node) — fetches from an RSS feed or static list
   - **Summarise Each** (Batch Node) — one LLM call per headline
   - Rank Headlines (Router Node) — routes `important` vs `routine`
   - Format Digest (Basic Node) — assembles the final output
   - Save Report (Basic Node) — writes to `output/digest.md`
3. Create a custom node type `rss_reader_node`:
   - Property: `feed_url` (string)
   - Action: `default`
4. Implement all node code via double-click
5. Define shared store schema for `headlines` (array), `summaries` (array), `digest` (string)
6. Validate, run with Mock Provider, inspect Run Log
7. Export and run standalone

---
