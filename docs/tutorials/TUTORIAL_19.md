# Tutorial 19: Debug Mode and Breakpoints

**What you'll learn:** Step through a running flow node by node, inspect shared-store state at each point.

### Steps

1. Open the project from Tutorial 7 (Hello World)
2. Click the **Ask LLM** node to select it
3. Node > Toggle Breakpoint (F9) — a red dot appears in the node's corner
4. Run > Debug Active Flow (Shift+F5)
   - The flow runs until it reaches Ask LLM and pauses
5. Check the **Shared Store** tab — see values accumulated so far
6. Check the **Run Log** tab — steps completed are listed
7. Run > Resume (or click the Resume button) to continue
8. Run > Stop to abort the debug session

**Tip:** Set breakpoints on any node where you want to inspect state. Multiple breakpoints in a loop let you watch variables change on each iteration.

---
