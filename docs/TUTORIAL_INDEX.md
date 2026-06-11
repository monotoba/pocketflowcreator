# PocketFlow Creator — Tutorials

This document provides step-by-step tutorials for every major feature of PocketFlow Creator
and every core pattern from the PocketFlow framework. Work through Part 1 first to learn
the IDE; then pick any Part 2 or Part 3 tutorial in any order.

---

## How to Read These Tutorials

Each tutorial lists:
- **What you'll learn** — the skill or pattern covered
- **Prerequisites** — what to complete first
- **Step-by-step instructions** — exact UI actions
- **Expected result** — what success looks like

Node properties shown as `Property: value` are set in the **Object Inspector** panel (right side).
Code shown in `code blocks` is written in the **Python editor** tab (bottom panel).

---

# Part 1 — Getting Started with PocketFlow Creator

| Tutorial | Title | Focus |
|----------|-------|-------|
| [Tutorial 1](tutorials/TUTORIAL_01.md) | IDE Tour | Learn the six panels of the Creator IDE |
| [Tutorial 2](tutorials/TUTORIAL_02.md) | Your First Flow — Hello World | Create a project, add nodes, wire them, run |
| [Tutorial 3](tutorials/TUTORIAL_03.md) | Using the Properties Inspector | Edit node properties and data contracts |
| [Tutorial 4](tutorials/TUTORIAL_04.md) | The Code Editor — RAD Node Coding | Implement node logic with double-click editing |
| [Tutorial 5](tutorials/TUTORIAL_05.md) | Creating a Custom Node Type | Use the Node Wizard to define reusable types |
| [Tutorial 6](tutorials/TUTORIAL_06.md) | Project Templates | Start from built-in templates |

---

# Part 2 — PocketFlow Patterns in Creator

Each tutorial in this section maps a PocketFlow cookbook example to a Creator project.

| Tutorial | Title | Pattern |
|----------|-------|---------|
| [Tutorial 7](tutorials/TUTORIAL_07.md) | Hello World — Single Node Q&A | Simplest flow: question → LLM → answer |
| [Tutorial 8](tutorials/TUTORIAL_08.md) | Chat with History | Maintain conversation history across turns |
| [Tutorial 9](tutorials/TUTORIAL_09.md) | Structured Output — Resume Data Extraction | Extract typed fields from unstructured text |
| [Tutorial 10](tutorials/TUTORIAL_10.md) | Multi-Stage Workflow — Article Writer | Chain LLM calls through stages (outline → draft → style) |
| [Tutorial 11](tutorials/TUTORIAL_11.md) | Conditional Routing — Chat Guardrail | Branch flow based on LLM classification |
| [Tutorial 12](tutorials/TUTORIAL_12.md) | Agent with Tools | Build an agent that chooses which tool to use |
| [Tutorial 13](tutorials/TUTORIAL_13.md) | Retrieval-Augmented Generation (RAG) | Index docs, retrieve chunks, generate answers |
| [Tutorial 14](tutorials/TUTORIAL_14.md) | Map-Reduce / Batch Processing | Process many items in parallel and aggregate |
| [Tutorial 15](tutorials/TUTORIAL_15.md) | Human-in-the-Loop | Pause for user approval before continuing |
| [Tutorial 16](tutorials/TUTORIAL_16.md) | LLM-as-Judge / Evaluator Loop | Use LLM to evaluate and improve generated content |
| [Tutorial 17](tutorials/TUTORIAL_17.md) | Multi-Agent System | Two agents debate or collaborate |

---

# Part 3 — Advanced Creator Features

| Tutorial | Title | Focus |
|----------|-------|-------|
| [Tutorial 18](tutorials/TUTORIAL_18.md) | Validation and Error Badges | Use the validator to find graph problems |
| [Tutorial 19](tutorials/TUTORIAL_19.md) | Debug Mode and Breakpoints | Step through a flow node by node |
| [Tutorial 20](tutorials/TUTORIAL_20.md) | Subflow Composition | Embed reusable sub-graphs |
| [Tutorial 21](tutorials/TUTORIAL_21.md) | Exporting and Running a Standalone Project | Export as independent Python package |
| [Tutorial 22](tutorials/TUTORIAL_22.md) | Shared Store Designer | Define data contracts and schema |
| [Tutorial 23](tutorials/TUTORIAL_23.md) | Streaming Output | Produce incremental output in real time |
| [Tutorial 24](tutorials/TUTORIAL_24.md) | Memory — Short-Term and Long-Term Context | Maintain two memory layers |
| [Tutorial 25](tutorials/TUTORIAL_25.md) | Packaging for Distribution | Create self-contained executables |

---

# Part 4 — Creator System Exercises

These exercises combine multiple features and require you to build something non-trivial.

| Exercise | Title | Skills |
|----------|-------|--------|
| [Exercise A](tutorials/EXERCISE_A.md) | Build a Complete News Summariser | Multi-stage workflow, LLM chaining, batch processing |
| [Exercise B](tutorials/EXERCISE_B.md) | Coding Agent with Memory | Agentic loop, tool nodes, subflow, debugging |
| [Exercise C](tutorials/EXERCISE_C.md) | Multi-Provider LLM Router | Custom nodes, routing, validation |
| [Exercise D](tutorials/EXERCISE_D.md) | Full IDE Workout | Everything — create, edit, debug, export |

---

## Quick Reference: Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| New project | Ctrl+N |
| Open project | Ctrl+O |
| Save | Ctrl+S |
| Save all | Ctrl+Shift+S |
| Export project | Ctrl+E |
| Validate | Ctrl+Shift+V |
| Run active flow | F5 |
| Debug active flow | Shift+F5 |
| Toggle breakpoint | F9 |
| Zoom to fit | Ctrl+0 |
| Auto layout | Ctrl+Shift+L |

---

## Tutorial Organization

The tutorials are organized into individual files for easier maintenance and discovery:

```
docs/
├── TUTORIAL_INDEX.md          ← You are here
└── tutorials/
    ├── TUTORIAL_01.md through TUTORIAL_25.md    (25 tutorials)
    └── EXERCISE_A.md through EXERCISE_D.md      (4 exercises)
```

Each tutorial file is self-contained and can be updated independently without affecting others.

---

*PocketFlow Creator v0.3.2*
