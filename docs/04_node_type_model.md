# Node Type Model

PocketFlow Creator distinguishes between node types and node instances.

A **node type** is a reusable component available in the palette.

A **node instance** is a placed node in a graph.

## Inheritance

Custom node types may inherit from:

- PocketFlow base classes such as `Node`, `BatchNode`, `AsyncNode`, `Flow`, and async/batch variants.
- Standard Creator node types such as LLM Prompt Node, JSON LLM Node, Router Node, Tool Node, Human Review Node, and Batch Node.
- Other custom node types.

## Example Metadata

```yaml
schema_version: 0.1
node_type_id: verified_json_llm
display_name: Verified JSON LLM Node
category: LLM
base_class: llm_prompt_node
python_class: VerifiedJsonLLMNode
module: document_summarizer.custom.verified_json_llm

description: Calls an LLM, parses JSON, validates schema, and routes by result.

properties:
  model:
    type: string
    default: qwen2.5-coder:14b
    required: true
  output_schema:
    type: yaml
    required: true

actions:
  - success
  - invalid_json
  - schema_error
  - error

reads:
  - prompt.input
writes:
  - result.json
  - result.errors

allow_python_hooks: true
allow_prompt_files: true
```

## Code Modes

1. Property-only generated nodes.
2. Lifecycle hook nodes with custom `prep`, `exec`, `post`, or async equivalents.
3. Full custom Python class nodes.

## Protection Rule

Generated files may be overwritten. User custom files must never be overwritten automatically.
