# Exercise C: Multi-Provider LLM Router

**Skills exercised:** Custom node types, Router Node, Inspector properties, validation

**Objective:** Route LLM requests to different providers based on task type.

1. Create a custom node type `llm_router_node`:
   - Properties: `fast_model` (string), `smart_model` (string), `threshold` (integer)
   - Actions: `fast, smart, fallback`
2. Build the graph: input → classify complexity → route to Fast LLM or Smart LLM → merge → output
3. Wire the Router based on complexity score (low → fast, high → smart, error → fallback)
4. Test validation — confirm all three action edges are required
5. Export and test each provider path

---
