# Tutorials Index

PocketFlow Creator tutorials cover every major feature of the IDE and every core pattern
from the PocketFlow framework. Work through Part 1 first to learn the IDE; then pick any
Part 2 or Part 3 tutorial in any order.

---

## Getting to Know Nodes — Node-Type Tutorial Series

[→ Open the Series Index](gtkn_index.md)

A dedicated series that teaches every built-in and addon node type through hands-on mini-flows, progressing from the simplest nodes to the most advanced. Parts 1–19 cover all 83 built-in nodes; Parts 20–25 cover all 34 addon nodes (geospatial, hydrology, aerospace, weather, wind energy, scientific computing, and data catalog).

| Part | Nodes covered |
|---|---|
| [Part 1 — Foundation](gtkn_part1.md) | Start, Stop, Basic |
| [Part 2 — I/O and Tools](gtkn_part2.md) | File Reader, File Writer, Python Tool |
| [Part 3 — Flow Control & Human Interaction](gtkn_part3.md) | Router, Human Review, Human Input |
| [Part 4 — LLM Nodes](gtkn_part4.md) | LLM Prompt, JSON LLM, Classifier, Judge |
| [Part 5 — Batch and Async](gtkn_part5.md) | Batch, Async, Async Batch, Async Parallel Batch |
| [Part 6 — Advanced Patterns](gtkn_part6.md) | RAG, Agent, Subflow |
| Parts 7–19 — All remaining builtin nodes | See [full series index](gtkn_index.md) |
| **Addon Nodes** | |
| [Part 20 — Geospatial](gtkn_part20.md) | USGS Elevation Point, 3DEP, National Map, Earthquake Catalog, Landsat, ShakeMap Fetch, ShakeMap Scenario |
| [Part 21 — Hydrology & Water](gtkn_part21.md) | USGS Water Data, NWIS Query, StreamStats, SWMM, EPANET, MODFLOW 6, FloPy, pyWatershed |
| [Part 22 — Weather & Building Energy](gtkn_part22.md) | NOAA Weather, WRF Model, EnergyPlus Run |
| [Part 23 — Aerospace CFD & Geometry](gtkn_part23.md) | Open VSP, VSPAERO, SU2 CFD, Cart3D, FUN3D |
| [Part 24 — Aerospace Propulsion & MDO](gtkn_part24.md) | NASA CEA, RocketPy, GMAT, OpenMDAO, Optimization, NASA Trick |
| [Part 25 — Wind Energy, Sci. Computing & Data](gtkn_part25.md) | OpenFAST, KiteFAST, MATLAB Engine, Octave Script, USGS Data Catalog |

---

## How to Read These Tutorials

Each tutorial lists:
- **What you'll learn** — the skill or pattern covered
- **Prerequisites** — what to complete first
- **Step-by-step instructions** — exact UI actions
- **Expected result** — what success looks like

Node properties shown as `Property: value` are set in the **Object Inspector** panel.
Code shown in `code blocks` is written in the **Python editor** tab.

---

## Part 1 — Getting Started with PocketFlow Creator

[→ Open Part 1](part1_fundamentals.md)

| Tutorial | Topic |
|---|---|
| Tutorial 0 | [IDE Tour](part1_fundamentals.md#tutorial-0-ide-tour) |
| Tutorial 1 | [Hello LLM — Your First LLM Call](part1_fundamentals.md#tutorial-1-hello-llm) |
| Tutorial 2 | [Your First Flow — Hello World](part1_fundamentals.md#tutorial-2-your-first-flow--hello-world) |
| Tutorial 3 | [Using the Properties Inspector](part1_fundamentals.md#tutorial-3-using-the-properties-inspector) |
| Tutorial 4 | [The Code Editor — RAD Node Coding](part1_fundamentals.md#tutorial-4-the-code-editor--rad-node-coding) |
| Tutorial 5 | [Creating a Custom Node Type](part1_fundamentals.md#tutorial-5-creating-a-custom-node-type) |
| Tutorial 6 | [Project Templates](part1_fundamentals.md#tutorial-6-project-templates) |

---

## Part 2 — PocketFlow Patterns in Creator

[→ Open Part 2](part2_patterns.md)

| Tutorial | Pattern |
|---|---|
| Tutorial 7  | [Hello World — Single Node Q&A](part2_patterns.md#tutorial-7-hello-world--single-node-qa) |
| Tutorial 8  | [Chat with History](part2_patterns.md#tutorial-8-chat-with-history) |
| Tutorial 9  | [Structured Output — Resume Data Extraction](part2_patterns.md#tutorial-9-structured-output--resume-data-extraction) |
| Tutorial 10 | [Multi-Stage Workflow — Article Writer](part2_patterns.md#tutorial-10-multi-stage-workflow--article-writer) |
| Tutorial 11 | [Conditional Routing — Chat Guardrail](part2_patterns.md#tutorial-11-conditional-routing--chat-guardrail) |
| Tutorial 12 | [Agent with Tools](part2_patterns.md#tutorial-12-agent-with-tools) |
| Tutorial 13 | [Retrieval-Augmented Generation (RAG)](part2_patterns.md#tutorial-13-retrieval-augmented-generation-rag) |
| Tutorial 14 | [Map-Reduce / Batch Processing](part2_patterns.md#tutorial-14-map-reduce--batch-processing) |
| Tutorial 15 | [Human-in-the-Loop](part2_patterns.md#tutorial-15-human-in-the-loop) |
| Tutorial 16 | [LLM-as-Judge / Evaluator Loop](part2_patterns.md#tutorial-16-llm-as-judge--evaluator-loop) |
| Tutorial 17 | [Multi-Agent System](part2_patterns.md#tutorial-17-multi-agent-system) |
| Tutorial 23 | [Streaming Output](part2_patterns.md#tutorial-23-streaming-output) |
| Tutorial 24 | [Memory — Short-Term and Long-Term Context](part2_patterns.md#tutorial-24-memory--short-term-and-long-term-context) |
| Tutorial 26 | [Async Processing with AsyncNode](part2_patterns.md#tutorial-26-async-processing-with-asyncnode) |
| Tutorial 27 | [Async Batch Processing with AsyncBatchNode](part2_patterns.md#tutorial-27-async-batch-processing-with-asyncbatchnode) |
| Tutorial 28 | [Concurrent Async Batch with AsyncParallelBatchNode](part2_patterns.md#tutorial-28-concurrent-async-batch-with-asyncparallelbatchnode) |
| Tutorial 29 | [Using the Agent Node](part2_patterns.md#tutorial-29-using-the-agent-node) |
| Tutorial 30 | [Using the RAG Node](part2_patterns.md#tutorial-30-using-the-rag-node) |
| Tutorial 31 | [Using the Judge Node](part2_patterns.md#tutorial-31-using-the-judge-node) |
| Tutorial 32 | [Human Input + Classifier — Interactive Sentiment Triage](part2_patterns.md#tutorial-32-human-input--classifier--interactive-sentiment-triage) |

---

## Creating Custom Nodes

[→ Open the Guide](custom_nodes.md)

A complete guide to adding your own node types to the palette — using the GUI wizard
for project-local nodes and writing `.py` node packages for reusable, shareable nodes.

| Section | Topic |
|---|---|
| [Approach 1 — GUI Wizard](custom_nodes.md#approach-1--using-the-gui-wizard) | Definition / Actions / Properties tabs; node registered in the project |
| [Approach 2 — Node Package](custom_nodes.md#approach-2--writing-a-node-package) | `__node_meta__` dict, auto-detected class, optional icon draw-fn |
| [Installing a Package](custom_nodes.md#installing-a-package-via-the-gui) | Tools → Node Type Library → Install node package (.py) |
| [Node Type Library](custom_nodes.md#the-node-type-library-dialog) | Built-in / Installed Custom / Errors tabs |
| [External Editor Workflow](custom_nodes.md#developing-a-package-in-an-external-editor) | Type hints, secrets, unit-testing outside Creator |
| [Quick Reference](custom_nodes.md#quick-reference) | Minimal skeleton, full key table, property schema |

---

## Part 3 — Advanced Creator Features

[→ Open Part 3](part3_advanced.md)

| Tutorial | Topic |
|---|---|
| Tutorial 18 | [Validation and Error Badges](part3_advanced.md#tutorial-18-validation-and-error-badges) |
| Tutorial 19 | [Debug Mode and Breakpoints](part3_advanced.md#tutorial-19-debug-mode-and-breakpoints) |
| Tutorial 20 | [Subflow Composition](part3_advanced.md#tutorial-20-subflow-composition) |
| Tutorial 21 | [Exporting and Running a Standalone Project](part3_advanced.md#tutorial-21-exporting-and-running-a-standalone-project) |
| Tutorial 22 | [Shared Store Designer](part3_advanced.md#tutorial-22-shared-store-designer) |
| Tutorial 25 | [Packaging for Distribution](part3_advanced.md#tutorial-25-packaging-for-distribution) |

---

## Resilience Patterns

[→ Provider Failover Tutorial](resilience_failover.md)

**Provider Failover: Building Resilient LLM Workflows**

Master multi-provider LLM resilience: priority-ordered fallback, error-specific retries, session recovery with configurable cooldowns. Learn when to use Provider Failover vs Retry Node, configure complex provider strategies, and export flows that work in any environment.

---

## Part 4 — Exercises

[→ Open Part 4](part4_exercises.md)

| Exercise | Project |
|---|---|
| Exercise A | [Build a Complete News Summariser](part4_exercises.md#exercise-a-build-a-complete-news-summariser) |
| Exercise B | [Coding Agent with Memory](part4_exercises.md#exercise-b-coding-agent-with-memory) |
| Exercise C | [Multi-Provider LLM Router](part4_exercises.md#exercise-c-multi-provider-llm-router) |
| Exercise D | [Full IDE Workout](part4_exercises.md#exercise-d-full-ide-workout) |

---

[← Back to Help Index](../index.md)
