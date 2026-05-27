# Part 4 — Creator System Exercises

These exercises are open-ended projects. Unlike the tutorials in Parts 1–3, they do not
give you step-by-step instructions for every action. Instead, each exercise gives you an
objective, explains what you are building and why it is interesting, identifies the skills
and patterns you will need, and offers stretch goals that push further.

Use Parts 1–3 as your reference. When you get stuck, re-read the tutorial for the relevant
pattern rather than guessing. The goal is to build fluency — the ability to reach for the
right pattern without being told which one to use.

[← Tutorials Index](index.md)

---

## Exercise A: Build a Complete News Summariser

### What you are building

A flow that fetches news headlines, summarises each one with an LLM, ranks them by
importance, and assembles a daily digest report saved to a Markdown file.

This is a representative real-world pipeline: external data in, LLM processing in the
middle, formatted output at the end. It combines batch processing, conditional routing,
and file output in a single project.

### Why this is worth building

News summarisation is a canonical LLM use case, but building it end-to-end teaches
something more important: how to design a pipeline where the data contract between nodes
is explicit and the output format is predictable. A pipeline that produces clean, consistent
output is reusable; one that produces ad-hoc strings is not.

You will also practice the Shared Store Designer — defining your schema before writing code
forces you to think about what each node needs and what it produces before you write a
single line.

### Skills exercised

- Multi-stage workflow (Tutorial 10)
- Batch Node for per-item LLM calls (Tutorial 14)
- Conditional routing with Router Node (Tutorial 11)
- Shared Store Designer for schema definition (Tutorial 22)
- Custom node type wizard for the RSS reader (Tutorial 5)
- Export and standalone run (Tutorial 21)

### Objective

Build a flow with the following graph:

```
[Start] → [Fetch Headlines] → [Summarise Each (BatchNode)]
        → [Rank Headlines (Router)] ──important──→ [Format Digest]
                                   └─routine────→ [Filter Out]   → [Format Digest]
        → [Format Digest] → [Save Report] → [Stop]
```

The digest should be a Markdown file written to `output/digest.md` containing:
- A header with today's date
- A section for important headlines with their summaries
- A section for routine headlines (optional: omit entirely if you filter them out)

### Step-by-step guidance

**1. Design the schema first.**

Open the Shared Store Designer before writing any code. Define at minimum:

| Key | Type | Notes |
|---|---|---|
| `headlines` | array | List of headline strings fetched by Fetch Headlines |
| `summaries` | array | One summary string per headline, same order |
| `important` | array | Filtered list of (headline, summary) pairs rated important |
| `routine` | array | Filtered list of routine (headline, summary) pairs |
| `digest` | string | Final formatted Markdown report |

Deciding these keys upfront means every node has a clear contract before you write its
`prep` and `post` methods.

**2. Create a custom node type for the RSS reader.**

Use Node > New Custom Node Type. Give it:
- Type ID: `rss_reader_node`
- Category: Data/IO
- Properties: `feed_url` (string, default: `https://feeds.bbci.co.uk/news/rss.xml`)
- Actions: `default`

The wizard creates the YAML and a Python skeleton. Implement `exec` using the `feedparser`
library (install with `pip install feedparser`). If you prefer not to use a real feed,
return a static list of 5–10 headline strings.

**3. Use BatchNode for summarisation.**

`Summarise Each` should extend `BatchNode`. Its `prep` returns `shared["headlines"]`.
Its `exec` receives one headline string and returns a one-sentence summary. Its `post`
receives the list of all summaries and writes `shared["summaries"]`.

Write the prompt carefully: "Summarise this headline in one sentence without adding
information not in the headline." This constraint prevents the LLM from hallucinating
context.

**4. Route by importance.**

`Rank Headlines` is a Router Node with actions `important` and `routine`. In `exec`, call
the LLM with a prompt that classifies each (headline, summary) pair. A simple approach:
classify all pairs in one call by asking for a JSON list of indices rated important.

**5. Format and save.**

`Format Digest` assembles the final Markdown string. `Save Report` writes it to
`output/digest.md` (create the `output/` directory if it does not exist).

**6. Validate, run, export.**

Validate the project (Ctrl+Shift+V). Run with the Mock Provider first to verify the graph
structure — mock LLM responses will be placeholder strings, but you can confirm nodes
execute in the right order and the Shared Store populates correctly. Then switch to a real
provider and run again to see real summaries.

Export (Ctrl+E) and run standalone:

```bash
cd exports/news_summariser
pip install pocketflow feedparser
python main.py
```

### Stretch goals

- Replace the static headline list with a real RSS library fetch. Use `aiohttp` in an
  `AsyncNode` (Tutorial 26) to fetch the feed without blocking.
- Schedule the flow to run daily using a cron job or a simple Python scheduler.
- Add a second Router branch for a third category: `breaking` (for urgent stories) that
  goes to a separate section in the digest with a visual flag.

---

## Exercise B: Coding Agent with Memory

### What you are building

An agent that accepts a programming task in plain English, writes a Python solution, runs
a test suite against it, reads the test results, and iterates until the tests pass — or
until a maximum iteration count is reached.

### Why this is worth building

The coding agent exercises every advanced pattern at once: agentic looping, human-in-the-
loop review, subflow composition for the repair cycle, and debug-mode inspection of shared
state across iterations. It also forces you to think carefully about what the shared store
holds across multiple rounds — one of the trickier aspects of stateful agent design.

### Skills exercised

- Agentic loop with Router Node (Tutorial 12)
- Human-in-the-Loop for test review (Tutorial 15)
- Subflow composition for the fix cycle (Tutorial 20)
- Debug Mode with breakpoints (Tutorial 19)
- AsyncNode for running tests as a subprocess (Tutorial 26)

### Objective

Build a flow with this high-level structure:

```
[Start] → [Get Task] → [Plan] → [Write Code] → [Run Tests]
        ──pass──→ [Human Review] ──approved──→ [Save Output] → [Stop]
        ──fail───→ [Fix Errors] → [Write Code]  (loop)
[Human Review] ──rejected──→ [Fix Errors] → [Write Code]    (loop)
```

The agent should:
- Accept a task description (e.g., "Write a function that returns the Fibonacci sequence up to n")
- Plan the implementation in one LLM call
- Write the Python code in a second LLM call
- Run `pytest` against the written code
- If tests fail, read the output and revise the code
- If tests pass, present to a human reviewer before saving

### Step-by-step guidance

**1. Define the shared store schema.**

Key decisions:
- `task` (string): the original task description
- `plan` (string): the LLM-generated plan
- `code` (string): the current Python implementation
- `test_output` (string): the raw pytest output
- `test_passed` (boolean): whether the last test run passed
- `iteration` (integer): how many code revision rounds have occurred
- `max_iterations` (integer, default: 5): safety limit
- `feedback` (string): human reviewer feedback

**2. Build the fix loop as a subflow.**

Create `graphs/fix_loop.pfcgraph.yaml`. This sub-graph contains:
Start → Read Test Output → Diagnose Failure → Revise Code → Stop.

The `Diagnose Failure` node calls the LLM with the code, the test output, and the error
message to produce a diagnosis. `Revise Code` calls the LLM again with the diagnosis to
produce a revised implementation.

In the main graph, the `Fix Errors` node is a Subflow Node pointing to `fix_loop.pfcgraph.yaml`.

**3. Run tests with a subprocess.**

`Run Tests` writes `shared["code"]` to a temporary file, then runs `pytest` on it. Use
`subprocess.run` in `exec` to capture stdout and stderr. Write the combined output to
`shared["test_output"]` and set `shared["test_passed"]` based on the return code.

**4. Add the human review gate.**

`Human Review` is a Human Review Node (Tutorial 15). It prints the current code and test
results, asks for approval, and returns `approved` or `rejected`. If rejected, ask for
feedback and write it to `shared["feedback"]`.

**5. Add a maximum iteration guard.**

In the Router Node that reads `test_passed` and `iteration`, add logic: if
`iteration >= max_iterations`, route to the human review regardless of test status. Without
this, a persistent test failure loops forever.

**6. Debug with breakpoints.**

Set breakpoints on `Write Code` and `Run Tests`. Run in Debug Mode (Shift+F5). After each
code generation, inspect the Shared Store to verify `code` contains valid Python. After
each test run, inspect `test_output` and `test_passed`.

### Stretch goals

- Replace the simple test file write with a proper temp directory and a generated
  test scaffold based on the task description.
- Add a second LLM call before `Write Code` that converts the task into a test first
  ("test-driven" generation): write the test, then write code to pass it.
- Track `iteration` in the Shared Store Designer with a default of `0` and confirm it
  increments correctly by watching it in Debug Mode.

---

## Exercise C: Multi-Provider LLM Router

### What you are building

A flow that classifies each incoming request by complexity, then routes it to a different
LLM provider: fast/cheap for simple requests, powerful/expensive for complex ones, with a
fallback path for errors.

### Why this is worth building

In production, not all LLM requests need the same model. Routing by complexity reduces
cost significantly — simple factual lookups do not need a frontier model. This exercise
teaches you to design a custom node type with configurable properties, wire a three-way
Router, and test each path independently using the debug tools.

### Skills exercised

- Custom node type wizard with properties and multiple actions (Tutorial 5)
- Conditional routing with three-way Router Node (Tutorial 11)
- Inspector properties for runtime configuration (Tutorial 3)
- Validation and error badges (Tutorial 18)
- Debug Mode to test each path (Tutorial 19)

### Objective

Create a custom node type `llm_router_node` with these properties:

| Property | Type | Default | Description |
|---|---|---|---|
| `fast_model` | string | `ollama/mistral` | Model for low-complexity requests |
| `smart_model` | string | `gpt-4o` | Model for high-complexity requests |
| `threshold` | integer | `5` | Complexity score above which to use the smart model |

The node classifies the input with a cheap LLM call (or a heuristic) and returns one of
three actions: `fast`, `smart`, or `fallback` (for errors or ambiguous cases).

Build a flow:

```
[Start] → [Classify Complexity (llm_router_node)]
        ──fast────→ [Fast LLM]   → [Merge Output] → [Stop]
        ├─smart───→ [Smart LLM]  → [Merge Output]
        └─fallback─→ [Fallback]  → [Merge Output]
```

### Step-by-step guidance

**1. Create the custom node type.**

Use Node > New Custom Node Type. The wizard generates a YAML file in
`node_types/llm_router_node.yaml` and a Python skeleton. Fill in the three properties
and three actions. Save and confirm the node appears in the palette under a "Routing"
or custom category.

**2. Implement the classification logic.**

In the node's `exec`, score the input by length or call a fast local model to estimate
complexity (1–10 scale). Return the action string based on the score vs. `threshold`.

A simple heuristic that avoids a classification LLM call entirely:

```python
def exec(self, prep_res):
    question = prep_res
    score = min(10, len(question.split()) // 5 + 1)
    if score <= self.threshold:
        return "fast"
    return "smart"
```

This is appropriate for an exercise; in production you would use an LLM or a trained
classifier.

**3. Configure models in Inspector.**

Drag the `llm_router_node` from the palette. In Inspector, set `fast_model`,
`smart_model`, and `threshold` for this instance. This is what configurable properties are
for: the logic is in the code, the values are in the Inspector.

**4. Wire the three-way Router.**

Wire all three output actions. Validate the project — confirm there are no PFCE2101 errors
(undeclared actions). A common mistake is declaring `fast, smart, fallback` in the node
type but forgetting to wire the `fallback` edge, leaving it unresolved.

**5. Test each path in Debug Mode.**

Set `user_question` in the Shared Store Designer to a short question (should route `fast`).
Run in Debug Mode. Verify the route taken in the Run Log. Change the question to a complex
multi-part query. Re-run. Verify `smart` is chosen.

Set a breakpoint on the Router Node. Inspect `shared["route"]` after the classification
to confirm the score and decision are correct.

**6. Export and test each path.**

Export the project. Edit `custom/main_custom.py` to implement `call_llm` for both the fast
and smart models (the fast model points to Ollama, the smart model to the OpenAI API or
similar). Run `python main.py` and exercise each path.

### Stretch goals

- Add a `classify_model` property to the router node so the classification call itself
  can use a configurable model separate from the fast and smart models.
- Add a fourth action: `cached` — if the exact question has been asked before (check
  a dict in shared state), return the cached answer without calling any model.
- Implement a cost tracker: each path writes its estimated token cost to `shared["cost"]`,
  and a final aggregator node logs the total after each run.

---

## Exercise D: Full IDE Workout

### What you are building

This is a comprehensive end-to-end exercise that verifies you have mastered every major
feature of Creator. There is no specific project to build — you work through a checklist
of actions, each of which exercises a different part of the IDE. At the end, you should
have touched every major feature at least once.

### Why this matters

Individual tutorials teach patterns in isolation. This exercise forces you to move between
panels, switch modes, and use features in combination — which is how real project work
actually happens. It also surfaces any gaps: if a step is unfamiliar, go back to the
relevant tutorial before continuing.

### The workout

Complete every item on the list. Tick each one off as you finish it.

**Project and Canvas**

- [ ] Create a new project from the **Simple LLM Flow** template (File > New From Template)
- [ ] Add 3 additional nodes from the palette — use at least one Batch Node and one Router Node
- [ ] Edit node titles and Actions fields in the Object Inspector
- [ ] Arrange nodes manually and use View > Zoom to Fit (Ctrl+0) to tidy the canvas
- [ ] Draw an edge, then delete it and re-draw it with a different action label
- [ ] Select multiple nodes with Shift+Click and move them together

**Custom Node Type**

- [ ] Create one custom node type via the wizard (Node > New Custom Node Type)
- [ ] Give it at least two properties and two actions
- [ ] Drag an instance of your custom type from the palette onto the canvas
- [ ] Set one of its properties in the Inspector to a non-default value
- [ ] Verify the type appears correctly in the validation output (Project > Validate Project)

**Code Editor**

- [ ] Implement all node code using double-click → Python editor
- [ ] Use the `# --- NODE_START` and `# --- NODE_END` markers as the boundary for your code
- [ ] Delete a node class body from the code editor and confirm the node disappears from the canvas
- [ ] Re-add it by dragging from the palette (confirm it gets fresh `# --- NODE_START` markers)

**Shared Store**

- [ ] Define a shared store schema with at least 4 keys in the Shared Store Designer
- [ ] Include at least one key with a default value, one of type `array`, and one of type `integer`
- [ ] Use the Shared Store tab during a run to confirm your nodes write the correct values

**Debug Mode**

- [ ] Set a breakpoint on a non-trivial node (F9)
- [ ] Run > Debug Active Flow (Shift+F5)
- [ ] Inspect the Shared Store while paused — confirm values match what you expect
- [ ] Resume execution (F5) and confirm it continues to the next breakpoint or to the end
- [ ] Remove all breakpoints and run normally to confirm the flow completes cleanly

**Export and Standalone Run**

- [ ] Export the project (File > Export PocketFlow Project…, Ctrl+E)
- [ ] Open the export directory and verify `custom/`, `generated/`, and `main.py` exist
- [ ] Implement `call_llm` in `custom/main_custom.py`
- [ ] Run `python main.py` from the export directory and confirm it executes without Creator

**Settings and Localisation**

- [ ] Switch from Dark to System (or Light) theme via Tools > Options
- [ ] Switch the UI language to Español and restart Creator
- [ ] Verify at least three menu items appear in Spanish
- [ ] Switch back to English and restart

### What success looks like

You have completed the workout when every checkbox is ticked and the exported project runs
correctly from the command line without any import errors or missing-file errors. If any
step fails, treat it as a diagnostic: identify which tutorial covers that feature and
review it before attempting the step again.

### Stretch goals

- Repeat the workout, but this time build a genuinely useful project rather than a
  demonstration one — a tool you would actually use.
- Time yourself. The first run might take 90 minutes. A fluent Creator user completes
  this workout in under 20 minutes.
- Record which steps took the longest. Those are your weak spots — go back to the
  relevant tutorials and re-read them until the steps feel automatic.

---

[← Back to Tutorials Index](index.md)
