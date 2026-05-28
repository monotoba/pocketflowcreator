# Getting to Know Nodes — Tutorial Series

Welcome to **Getting to Know Nodes**, a hands-on tutorial series for PocketFlow Creator. This series walks you through every node type available in the **Component Palette**, one at a time. Instead of describing node behaviour in the abstract, each tutorial asks you to build a small, self-contained mini-flow that demonstrates exactly what that node does, why it exists, and how you configure it through the **Object Inspector**.

By the time you finish all nineteen parts you will have built 83 mini-flows and will have a concrete mental model of every node type in the palette. You will know when to reach for a **Batch Node** versus an **Async Parallel Batch Node**, why you might prefer a **Classifier Node** over a hand-coded **Router Node**, and how **Subflow Nodes** let you compose large pipelines from reusable building blocks. The series is ordered from simplest to most powerful — start at Part 1 and work forwards, since later tutorials assume you are already comfortable with the node types introduced earlier.

> ⚠️ **Note:** Complete **Tutorial 0 — IDE Tour** (found in [Part 1 of the main tutorial series](part1_fundamentals.md#tutorial-0-ide-tour)) before starting this series. That tutorial familiarises you with the six panels of the IDE — **Component Palette**, **Canvas**, **Object Inspector**, **Project Explorer**, **Python editor tab**, and **Run Log tab** — and introduces the vocabulary used throughout these pages.

---

## All 83 Node Types at a Glance

| # | Node Type | Category | Part |
|---|-----------|----------|------|
| 1 | Start Node | Flow Control | [Part 1](gtkn_part1.md) |
| 2 | Stop Node | Flow Control | [Part 1](gtkn_part1.md) |
| 3 | Basic Node | Flow Control | [Part 1](gtkn_part1.md) |
| 4 | File Reader Node | I/O | [Part 2](gtkn_part2.md) |
| 5 | File Writer Node | I/O | [Part 2](gtkn_part2.md) |
| 6 | Python Tool Node | I/O | [Part 2](gtkn_part2.md) |
| 7 | Router Node | Flow Control | [Part 3](gtkn_part3.md) |
| 8 | Human Review Node | Human-in-the-Loop | [Part 3](gtkn_part3.md) |
| 9 | Human Input Node | Human-in-the-Loop | [Part 3](gtkn_part3.md) |
| 10 | LLM Prompt Node | LLM / AI | [Part 4](gtkn_part4.md) |
| 11 | JSON LLM Node | LLM / AI | [Part 4](gtkn_part4.md) |
| 12 | Classifier Node | LLM / AI | [Part 4](gtkn_part4.md) |
| 13 | Judge Node | LLM / AI | [Part 4](gtkn_part4.md) |
| 14 | Batch Node | Batch / Async | [Part 5](gtkn_part5.md) |
| 15 | Async Node | Batch / Async | [Part 5](gtkn_part5.md) |
| 16 | Async Batch Node | Batch / Async | [Part 5](gtkn_part5.md) |
| 17 | Async Parallel Batch Node | Batch / Async | [Part 5](gtkn_part5.md) |
| 18 | RAG Node | LLM / AI | [Part 6](gtkn_part6.md) |
| 19 | Agent Node | LLM / AI | [Part 6](gtkn_part6.md) |
| 20 | Subflow Node | Flow Control | [Part 6](gtkn_part6.md) |
| 21 | Chain of Thought Node | AI / Reasoning | [Part 7](gtkn_part7.md) |
| 22 | Majority Vote Node | AI / Reasoning | [Part 7](gtkn_part7.md) |
| 23 | Supervisor Node | AI / Reasoning | [Part 7](gtkn_part7.md) |
| 24 | Debate Advocate Node | AI / Reasoning | [Part 7](gtkn_part7.md) |
| 25 | Debate Judge Node | AI / Reasoning | [Part 7](gtkn_part7.md) |
| 26 | Web Search Node | Web / Search | [Part 8](gtkn_part8.md) |
| 27 | Web Scrape Node | Web / Search | [Part 8](gtkn_part8.md) |
| 28 | API Call Node | Web / Search | [Part 8](gtkn_part8.md) |
| 29 | Text Chunk Node | Data / Vector | [Part 9](gtkn_part9.md) |
| 30 | Embed Node | Data / Vector | [Part 9](gtkn_part9.md) |
| 31 | Vector Index Node | Data / Vector | [Part 9](gtkn_part9.md) |
| 32 | Vector Retrieve Node | Data / Vector | [Part 9](gtkn_part9.md) |
| 33 | DB Schema Node | Database / SQL | [Part 10](gtkn_part10.md) |
| 34 | NL to SQL Node | Database / SQL | [Part 10](gtkn_part10.md) |
| 35 | SQL Execute Node | Database / SQL | [Part 10](gtkn_part10.md) |
| 36 | Speech to Text Node | Voice / Audio | [Part 11](gtkn_part11.md) |
| 37 | Text to Speech Node | Voice / Audio | [Part 11](gtkn_part11.md) |
| 38 | PDF Extract Node | Document / Vision | [Part 11](gtkn_part11.md) |
| 39 | Image Vision Node | Document / Vision | [Part 11](gtkn_part11.md) |
| 40 | Data Validate Node | Document / Vision | [Part 11](gtkn_part11.md) |
| 41 | Code Gen Node | Code / Execution | [Part 12](gtkn_part12.md) |
| 42 | Code Exec Node | Code / Execution | [Part 12](gtkn_part12.md) |
| 43 | Test Gen Node | Code / Execution | [Part 12](gtkn_part12.md) |
| 44 | Map Node | Data Processing | [Part 13](gtkn_part13.md) |
| 45 | Reduce Node | Data Processing | [Part 13](gtkn_part13.md) |
| 46 | Condition Node | Data Processing | [Part 13](gtkn_part13.md) |
| 47 | Loop Counter Node | Data Processing | [Part 13](gtkn_part13.md) |
| 48 | Transform Node | Data Processing | [Part 13](gtkn_part13.md) |
| 49 | Merge Node | Data Processing | [Part 13](gtkn_part13.md) |
| 50 | Calendar Read Node | Calendar | [Part 14](gtkn_part14.md) |
| 51 | Calendar Write Node | Calendar | [Part 14](gtkn_part14.md) |
| 52 | MCP Tool Node | MCP / Agent Protocol | [Part 14](gtkn_part14.md) |
| 53 | A2A Send Node | MCP / Agent Protocol | [Part 14](gtkn_part14.md) |
| 54 | A2A Receive Node | MCP / Agent Protocol | [Part 14](gtkn_part14.md) |
| 55 | Log Node | Observability / Utility | [Part 15](gtkn_part15.md) |
| 56 | Timer Node | Observability / Utility | [Part 15](gtkn_part15.md) |
| 57 | Cache Node | Observability / Utility | [Part 15](gtkn_part15.md) |
| 58 | Trace Node | Observability / Utility | [Part 15](gtkn_part15.md) |
| 59 | Registry Node | Data Structures / Memory | [Part 15](gtkn_part15.md) |
| 60 | Stack Push Node | Data Structures / Memory | [Part 15](gtkn_part15.md) |
| 61 | Stack Pop Node | Data Structures / Memory | [Part 15](gtkn_part15.md) |
| 62 | Queue Enqueue Node | Data Structures / Memory | [Part 15](gtkn_part15.md) |
| 63 | Queue Dequeue Node | Data Structures / Memory | [Part 15](gtkn_part15.md) |
| 64 | Local Memory Node | Data Structures / Memory | [Part 15](gtkn_part15.md) |
| 65 | Shell Command Node | System / Shell | [Part 16](gtkn_part16.md) |
| 66 | TTY Serial Node | System / Shell | [Part 16](gtkn_part16.md) |
| 67 | Spreadsheet Node | System / Shell | [Part 16](gtkn_part16.md) |
| 68 | Socket Node | Networking | [Part 17](gtkn_part17.md) |
| 69 | WebSocket Node | Networking | [Part 17](gtkn_part17.md) |
| 70 | Webhook Trigger Node | Networking | [Part 17](gtkn_part17.md) |
| 71 | Context Compact Node | AI / LLM Utilities | [Part 18](gtkn_part18.md) |
| 72 | Conversation History Node | AI / LLM Utilities | [Part 18](gtkn_part18.md) |
| 73 | Regex Node | Text / Data Processing | [Part 18](gtkn_part18.md) |
| 74 | Template Render Node | Text / Data Processing | [Part 18](gtkn_part18.md) |
| 75 | JSON Parse Node | Text / Data Processing | [Part 18](gtkn_part18.md) |
| 76 | List Operations Node | Text / Data Processing | [Part 18](gtkn_part18.md) |
| 77 | String Operations Node | Text / Data Processing | [Part 18](gtkn_part18.md) |
| 78 | Retry Node | Resilience | [Part 19](gtkn_part19.md) |
| 79 | Rate Limiter Node | Resilience | [Part 19](gtkn_part19.md) |
| 80 | Email Send Node | Messaging | [Part 19](gtkn_part19.md) |
| 81 | Email Read Node | Messaging | [Part 19](gtkn_part19.md) |
| 82 | Notification Node | Messaging | [Part 19](gtkn_part19.md) |
| 83 | Secret Node | Security | [Part 19](gtkn_part19.md) |

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
| [Part 7](gtkn_part7.md) | AI / Reasoning Nodes | Chain of Thought, Majority Vote, Supervisor, Debate Advocate, Debate Judge |
| [Part 8](gtkn_part8.md) | Web and Search Nodes | Web Search, Web Scrape, API Call |
| [Part 9](gtkn_part9.md) | Data and Vector Nodes | Text Chunk, Embed, Vector Index, Vector Retrieve |
| [Part 10](gtkn_part10.md) | Database and SQL Nodes | DB Schema, NL to SQL, SQL Execute |
| [Part 11](gtkn_part11.md) | Voice, Audio, and Document Nodes | Speech to Text, Text to Speech, PDF Extract, Image Vision, Data Validate |
| [Part 12](gtkn_part12.md) | Code Execution Nodes | Code Gen, Code Exec, Test Gen |
| [Part 13](gtkn_part13.md) | Data Processing Nodes | Map, Reduce, Condition, Loop Counter, Transform, Merge |
| [Part 14](gtkn_part14.md) | Calendar and Agent Protocol Nodes | Calendar Read, Calendar Write, MCP Tool, A2A Send, A2A Receive |
| [Part 15](gtkn_part15.md) | Observability and Data Structure Nodes | Log, Timer, Cache, Trace, Registry, Stack Push/Pop, Queue Enqueue/Dequeue, Local Memory |
| [Part 16](gtkn_part16.md) | System, Shell, and Hardware Nodes | Shell Command, TTY Serial, Spreadsheet |
| [Part 17](gtkn_part17.md) | Networking Nodes | Socket, WebSocket, Webhook Trigger |
| [Part 18](gtkn_part18.md) | AI/LLM Utility and Text Processing Nodes | Context Compact, Conversation History, Regex, Template Render, JSON Parse, List Operations, String Operations |
| [Part 19](gtkn_part19.md) | Resilience, Messaging, and Security Nodes | Retry, Rate Limiter, Email Send, Email Read, Notification, Secret |

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
