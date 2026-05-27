# Getting to Know Nodes — Tutorial Series

Welcome to **Getting to Know Nodes**, a hands-on tutorial series for PocketFlow Creator. This series walks you through every node type available in the **Component Palette**, one at a time. Instead of describing node behaviour in the abstract, each tutorial asks you to build a small, self-contained mini-flow that demonstrates exactly what that node does, why it exists, and how you configure it through the **Object Inspector**.

By the time you finish all six parts you will have built twenty mini-flows and will have a concrete mental model of every node type in the palette. You will know when to reach for a **Batch Node** versus an **Async Parallel Batch Node**, why you might prefer a **Classifier Node** over a hand-coded **Router Node**, and how **Subflow Nodes** let you compose large pipelines from reusable building blocks. The series is ordered from simplest to most powerful — start at Part 1 and work forwards, since later tutorials assume you are already comfortable with the node types introduced earlier.

> ⚠️ **Note:** Complete **Tutorial 0 — IDE Tour** (found in [Part 1 of the main tutorial series](part1_fundamentals.md#tutorial-0-ide-tour)) before starting this series. That tutorial familiarises you with the six panels of the IDE — **Component Palette**, **Canvas**, **Object Inspector**, **Project Explorer**, **Python editor tab**, and **Run Log tab** — and introduces the vocabulary used throughout these pages.

---

## All 20 Node Types at a Glance

| # | Node Type | Use Case | Part |
|---|-----------|----------|------|
| 1 | Start Node | Marks the entry point of every flow | [Part 1](gtkn_part1.md) |
| 2 | Stop Node | Marks the exit point of a flow | [Part 1](gtkn_part1.md) |
| 3 | Basic Node | General-purpose compute, transform, and I/O | [Part 1](gtkn_part1.md) |
| 4 | File Reader Node | Read a file from disk into the shared store | [Part 2](gtkn_part2.md) |
| 5 | File Writer Node | Write a shared store value to a file on disk | [Part 2](gtkn_part2.md) |
| 6 | Python Tool Node | Execute a registered `@tool`-decorated function | [Part 2](gtkn_part2.md) |
| 7 | Router Node | Branch the flow based on shared store state | [Part 3](gtkn_part3.md) |
| 8 | Human Review Node | Pause for human approval or rejection | [Part 3](gtkn_part3.md) |
| 9 | Human Input Node | Capture live text input from the user at runtime | [Part 3](gtkn_part3.md) |
| 10 | LLM Prompt Node | Send a prompt to an LLM and store the text reply | [Part 4](gtkn_part4.md) |
| 11 | JSON LLM Node | Prompt the LLM for structured JSON output | [Part 4](gtkn_part4.md) |
| 12 | Classifier Node | LLM-based multi-class routing | [Part 4](gtkn_part4.md) |
| 13 | Judge Node | LLM evaluates quality; returns pass or fail | [Part 4](gtkn_part4.md) |
| 14 | Batch Node | Process a list of items sequentially | [Part 5](gtkn_part5.md) |
| 15 | Async Node | Async coroutine for non-blocking I/O | [Part 5](gtkn_part5.md) |
| 16 | Async Batch Node | Async sequential batch processing | [Part 5](gtkn_part5.md) |
| 17 | Async Parallel Batch Node | Concurrent async batch via `asyncio.gather` | [Part 5](gtkn_part5.md) |
| 18 | RAG Node | Retrieval-Augmented Generation | [Part 6](gtkn_part6.md) |
| 19 | Agent Node | Autonomous tool-using AI agent loop | [Part 6](gtkn_part6.md) |
| 20 | Subflow Node | Embed another graph as a single node | [Part 6](gtkn_part6.md) |

---

## Series Structure

| Part | Title | Nodes Covered |
|------|-------|---------------|
| [Part 1](gtkn_part1.md) | Foundation Nodes | Start, Stop, Basic |
| [Part 2](gtkn_part2.md) | I/O and Tool Nodes | File Reader, File Writer, Python Tool |
| [Part 3](gtkn_part3.md) | Flow Control and Human Interaction | Router, Human Review, Human Input |
| [Part 4](gtkn_part4.md) | LLM Nodes | LLM Prompt, JSON LLM, Classifier, Judge |
| [Part 5](gtkn_part5.md) | Batch and Async Nodes | Batch, Async, Async Batch, Async Parallel Batch |
| [Part 6](gtkn_part6.md) | Advanced Nodes | RAG, Agent, Subflow |

---

## How to Use This Series

Each tutorial inside a part follows the same structure:

- **What it does** — a plain-English explanation of the node's role
- **Use cases** — real-world scenarios where this node shines
- **What you'll build** — one sentence describing the mini-flow
- **Step-by-step** — numbered instructions you follow in the IDE
- **What you learned** — a bullet summary to check your understanding

Tips and warnings are called out in blockquotes so they are easy to scan. Code blocks show the Python skeleton you will paste into the **Python editor tab**. Property values shown in `monospace` are typed into the **Object Inspector**.

---

[↑ Tutorials Index](index.md)  
[→ Start with Part 1](gtkn_part1.md)
