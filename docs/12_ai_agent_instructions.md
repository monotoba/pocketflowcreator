# AI Agent Instructions

When using Codex, Aider, Claude Code, OpenCode, or other AI coding agents with this project:

1. Do not rewrite the entire project unless explicitly instructed.
2. Prefer small, testable refactors.
3. Add or update tests for every behavior change.
4. Keep generated code separate from custom code.
5. Do not remove docs or scripts unless replacing them with better equivalents.
6. Preserve the RAD interaction model: select node type, edit properties, wire actions.
7. Preserve custom node inheritance support.
8. Keep project files deterministic and version-control friendly.
9. Do not add network calls to tests.
10. Use mock providers for LLM-dependent tests.

Suggested first task for an agent:

```text
Implement YAML project loading and saving for GraphModel and NodeTypeDefinition, then add tests using the example project files.
```
