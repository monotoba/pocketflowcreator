# Requirements

## Functional Requirements

| ID | Requirement |
|---|---|
| FR-001 | The app shall create and save PocketFlow Creator projects. |
| FR-002 | The app shall provide a graph designer where users place node instances. |
| FR-003 | The app shall provide a component palette of built-in and custom node types. |
| FR-004 | The app shall provide an object inspector for every selectable object. |
| FR-005 | The app shall allow users to edit node properties before or after wiring nodes. |
| FR-006 | The app shall expose node actions as action output ports. |
| FR-007 | The app shall allow action ports to be wired visually to destination nodes. |
| FR-008 | The app shall allow action destinations to be edited from the inspector. |
| FR-009 | The app shall validate graph structure before running or exporting. |
| FR-010 | The app shall support standard node types including Start, Stop, Basic, Router, LLM Prompt, JSON LLM, Tool, Human Review, Batch, and Subflow nodes. |
| FR-011 | The app shall support custom node types. |
| FR-012 | Custom node types shall inherit from PocketFlow base classes, standard node types, or other custom node types. |
| FR-013 | The app shall support Python editing for custom node code. |
| FR-014 | The app shall support Markdown editing for prompts. |
| FR-015 | The app shall support YAML editing for metadata, schemas, tools, and node type definitions. |
| FR-016 | The app shall separate generated code from user-owned custom code. |
| FR-017 | The app shall never overwrite user-owned custom code during regeneration. |
| FR-018 | The app shall generate readable Python PocketFlow project code. |
| FR-019 | The app shall generate basic tests for exported projects and custom nodes. |
| FR-020 | The app shall support Ollama as a first-class local provider profile. |
| FR-021 | The app shall support a mock provider for deterministic tests. |
| FR-022 | The app shall provide run/debug views including shared-store inspection, prompt preview, run log, and selected actions. |
| FR-023 | The app shall support project templates and reusable node templates. |
| FR-024 | The app shall support exporting graph images and project reports. |

## Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-001 | Project files shall be plain text and version-control friendly. |
| NFR-002 | Generated code shall remain hand-readable and hand-editable after export. |
| NFR-003 | Local workflows shall not require cloud services. |
| NFR-004 | Provider credentials shall not be stored in project files by default. |
| NFR-005 | Dangerous tool permissions shall be explicit and visible. |
| NFR-006 | The graph designer should remain responsive with at least 200 nodes. |
| NFR-007 | Generated project output should be reproducible from saved metadata. |
| NFR-008 | Linux should be supported first, with Windows and macOS scripts included. |
| NFR-009 | The app shall be testable without real LLM calls. |
| NFR-010 | The app shall keep GUI model, validation model, and generated runtime model cleanly separated. |
