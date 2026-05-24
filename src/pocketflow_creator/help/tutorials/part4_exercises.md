# Part 4 — Creator System Exercises

These exercises combine multiple features and require you to build something non-trivial.
No step-by-step instructions are given — use what you learned in Parts 1–3.

[← Tutorials Index](index.md)

---

## Exercise A: Build a Complete News Summariser

**Skills exercised:** Multi-stage workflow, LLM chaining, Shared Store Designer, custom node type, export and run

**Objective:** Fetch news headlines, summarise each one, and produce a daily digest.

1. Create project `news_summariser`
2. Design the graph:
   - **Fetch Headlines** (Basic Node) — fetches from an RSS feed or static list
   - **Summarise Each** (Batch Node) — one LLM call per headline
   - **Rank Headlines** (Router Node) — routes `important` vs `routine`
   - **Format Digest** (Basic Node) — assembles the final output
   - **Save Report** (Basic Node) — writes to `output/digest.md`
3. Create a custom node type `rss_reader_node`:
   - Property: `feed_url` (string)
   - Action: `default`
4. Implement all node code via double-click
5. Define shared store schema:
   - `headlines` (array), `summaries` (array), `digest` (string)
6. Validate, run with Mock Provider, inspect Run Log
7. Export and run standalone: `python main.py`

**Stretch goal:** Replace the static headline list with a real RSS library (`feedparser`) in your custom node implementation.

---

## Exercise B: Coding Agent with Memory

**Skills exercised:** Agentic loop, tool nodes, subflow, breakpoints, debug stepping

**Objective:** Build an agent that can write, test, and fix simple Python code.

1. Create project `coding_agent`
2. Design the agent loop:
   - Get Task → Plan → Write Code → Run Tests (Human Review Node) → Fix Errors → Done
3. Add a **Subflow Node** embedding a `fix_loop.pfcgraph.yaml` sub-graph for the repair cycle
4. Implement **Run Tests** as a Human Review Node that shows test output and asks for approval
5. Set breakpoints at Write Code and Fix Errors to debug iteratively
6. Use Debug Mode to inspect the shared store after each code generation step

**Key shared store keys:** `task`, `plan`, `code`, `test_output`, `error`, `iteration`

---

## Exercise C: Multi-Provider LLM Router

**Skills exercised:** Custom node types, Router Node, Inspector properties, validation

**Objective:** Route LLM requests to different providers based on task type.

1. Create a custom node type `llm_router_node`:
   - Properties: `fast_model` (string), `smart_model` (string), `threshold` (integer, default: 5)
   - Actions: `fast, smart, fallback`
2. Build the graph:
   - Input → Classify Complexity → route → Fast LLM or Smart LLM → Merge → Output
3. Wire the Router based on complexity score (low → fast, high → smart, error → fallback)
4. Test validation — confirm all three action edges are required
5. Run with Mock Provider, switch to Ollama in Tools > Provider Manager, test each path
6. Export and verify each provider path runs correctly

---

## Exercise D: Full IDE Workout

**Skills exercised:** Everything — create, edit, custom nodes, debug, export, package

Complete all of the following in one session to verify you have mastered the full Creator workflow:

- [ ] Create a new project from the **Simple LLM Flow** template
- [ ] Add 3 additional nodes from the palette
- [ ] Edit node titles and Actions in the inspector
- [ ] Create one custom node type via the wizard (Node > New Custom Node Type…)
- [ ] Implement all node code using double-click → Python editor
- [ ] Define a shared store schema with at least 4 keys
- [ ] Set a breakpoint and run in debug mode (Shift+F5)
- [ ] Inspect the Shared Store mid-run
- [ ] Export the project (File > Export PocketFlow Project…)
- [ ] Verify `custom/` and `generated/` directories exist in the export
- [ ] Run `python main.py` from the exported directory
- [ ] Switch from Dark to System theme via Tools > Options
- [ ] Switch the language to Español and restart; verify the UI is in Spanish

---

[← Back to Tutorials Index](index.md)
