# Exercise B: Coding Agent with Memory

**Skills exercised:** Agentic loop, tool nodes, subflow, breakpoints, debug stepping

**Objective:** Build an agent that can write, test, and fix simple Python code.

1. Create project `coding_agent`
2. Design the agent loop:
   - Get Task → Plan → Write Code → Run Tests (Human Review Node) → Fix Errors → Done
3. Add a **Subflow Node** embedding a `fix_loop.pfcgraph.yaml` sub-graph
4. Implement **Run Tests** as a Human Review Node that shows test output and asks for approval
5. Set breakpoints at Write Code and Fix Errors to debug iteratively
6. Use Debug Mode to inspect the shared store after each code generation step

---
