"""Built-in node type definitions for all palette items.

These mirror the palette in canvas.py and provide property metadata for the
Object Inspector without requiring a project or custom YAML files.
"""
from __future__ import annotations

from pocketflow_creator.model.node_type import NodeTypeDefinition

# Each entry uses the same property-metadata dict format as custom YAML:
# { "type": str, "default": value, "description": str }

BUILTIN_NODE_TYPES: dict[str, NodeTypeDefinition] = {
    t.node_type_id: t
    for t in [
        NodeTypeDefinition(
            node_type_id="start_node",
            display_name="Start Node",
            category="Flow Control",
            base_class="Node",
            actions=["default"],
            properties={},
        ),
        NodeTypeDefinition(
            node_type_id="stop_node",
            display_name="Stop Node",
            category="Flow Control",
            base_class="Node",
            properties={},
        ),
        NodeTypeDefinition(
            node_type_id="basic_node",
            display_name="Basic Node",
            category="Core",
            base_class="Node",
            actions=["default"],
            properties={},
        ),
        NodeTypeDefinition(
            node_type_id="router_node",
            display_name="Router Node",
            category="Flow Control",
            base_class="Node",
            properties={
                "routes": {
                    "type": "string",
                    "default": "",
                    "description": "Comma-separated action names this router may return",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="llm_prompt_node",
            display_name="LLM Prompt Node",
            category="AI",
            base_class="Node",
            actions=["default"],
            allow_prompt_files=True,
            properties={
                "prompt_type": {
                    "type": "string",
                    "default": "string",
                    "choices": ["string", "path"],
                    "description": "'string' = literal prompt text, 'path' = relative path to a Markdown file",
                },
                "prompt_file": {
                    "type": "string",
                    "default": "",
                    "description": "Prompt text (if prompt_type=string) or relative file path (if prompt_type=path)",
                },
                "model": {
                    "type": "string",
                    "default": "",
                    "description": "LLM model name (blank = project default)",
                },
                "temperature": {
                    "type": "number",
                    "default": 0.7,
                    "description": "Sampling temperature 0–1",
                },
                "max_tokens": {
                    "type": "integer",
                    "default": 1024,
                    "description": "Maximum tokens in the response",
                },
                "system_prompt": {
                    "type": "string",
                    "default": "",
                    "description": "Optional system prompt override",
                },
                "input_key": {
                    "type": "string",
                    "default": "input",
                    "description": "Shared store key read by prep()",
                },
                "output_key": {
                    "type": "string",
                    "default": "output",
                    "description": "Shared store key written by post()",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="json_llm_node",
            display_name="JSON LLM Node",
            category="AI",
            base_class="Node",
            actions=["default"],
            allow_prompt_files=True,
            properties={
                "prompt_type": {
                    "type": "string",
                    "default": "string",
                    "choices": ["string", "path"],
                    "description": "'string' = literal prompt text, 'path' = relative file path",
                },
                "prompt_file": {
                    "type": "string",
                    "default": "",
                    "description": "Prompt text (if prompt_type=string) or relative file path (if prompt_type=path)",
                },
                "model": {
                    "type": "string",
                    "default": "",
                    "description": "LLM model name",
                },
                "temperature": {
                    "type": "number",
                    "default": 0.2,
                    "description": "Sampling temperature (lower = more deterministic JSON)",
                },
                "output_key": {
                    "type": "string",
                    "default": "result",
                    "description": "Shared store key to write the parsed JSON object to",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="classifier_node",
            display_name="Classifier Node",
            category="AI",
            base_class="Node",
            properties={
                "categories": {
                    "type": "string",
                    "default": "",
                    "description": "Comma-separated categories (also the action names)",
                },
                "model": {
                    "type": "string",
                    "default": "",
                    "description": "LLM model name",
                },
                "input_key": {
                    "type": "string",
                    "default": "input",
                    "description": "Shared store key containing the text to classify",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="python_tool_node",
            display_name="Python Tool Node",
            category="Code",
            base_class="Node",
            actions=["default"],
            properties={
                "tool_name": {
                    "type": "string",
                    "default": "",
                    "description": "Name of the @tool-decorated function to call",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="file_reader_node",
            display_name="File Reader Node",
            category="Data/IO",
            base_class="Node",
            actions=["default"],
            properties={
                "file_path": {
                    "type": "string",
                    "default": "",
                    "description": "Path to file (absolute or relative to project root)",
                },
                "encoding": {
                    "type": "string",
                    "default": "utf-8",
                    "description": "File character encoding",
                },
                "output_key": {
                    "type": "string",
                    "default": "content",
                    "description": "Shared store key to write the file contents to",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="file_writer_node",
            display_name="File Writer Node",
            category="Data/IO",
            base_class="Node",
            actions=["default"],
            properties={
                "file_path": {
                    "type": "string",
                    "default": "",
                    "description": "Path to the file to write",
                },
                "encoding": {
                    "type": "string",
                    "default": "utf-8",
                    "description": "File character encoding",
                },
                "mode": {
                    "type": "string",
                    "default": "write",
                    "description": "'write' to overwrite, 'append' to add to the end",
                },
                "input_key": {
                    "type": "string",
                    "default": "content",
                    "description": "Shared store key whose value is written to the file",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="human_review_node",
            display_name="Human Review Node",
            category="Human-in-the-Loop",
            base_class="Node",
            actions=["approved", "rejected"],
            properties={
                "prompt": {
                    "type": "string",
                    "default": "Please review the following and approve or reject:",
                    "description": "Message shown to the human reviewer",
                },
                "input_key": {
                    "type": "string",
                    "default": "content",
                    "description": "Shared store key whose value is shown for review",
                },
                "feedback_key": {
                    "type": "string",
                    "default": "feedback",
                    "description": "Shared store key to write reviewer feedback to",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="batch_node",
            display_name="Batch Node",
            category="Processing",
            base_class="BatchNode",
            actions=["default"],
            properties={
                "input_key": {
                    "type": "string",
                    "default": "items",
                    "description": "Shared store key containing the list to iterate over",
                },
                "output_key": {
                    "type": "string",
                    "default": "results",
                    "description": "Shared store key to write the list of results to",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="async_node",
            display_name="Async Node",
            category="Async",
            base_class="AsyncNode",
            actions=["default"],
            properties={
                "timeout": {
                    "type": "number",
                    "default": 30.0,
                    "description": "Async timeout in seconds",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="async_batch_node",
            display_name="Async Batch Node",
            category="Async",
            base_class="AsyncBatchNode",
            actions=["default"],
            properties={
                "input_key": {
                    "type": "string",
                    "default": "items",
                    "description": "Shared store key containing the list to iterate over",
                },
                "output_key": {
                    "type": "string",
                    "default": "results",
                    "description": "Shared store key to write results to",
                },
                "timeout": {
                    "type": "number",
                    "default": 30.0,
                    "description": "Async timeout per item in seconds",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="async_parallel_batch_node",
            display_name="Async Parallel Batch Node",
            category="Async",
            base_class="AsyncParallelBatchNode",
            actions=["default"],
            properties={
                "input_key": {
                    "type": "string",
                    "default": "items",
                    "description": "Shared store key containing the list to iterate over",
                },
                "output_key": {
                    "type": "string",
                    "default": "results",
                    "description": "Shared store key to write results to",
                },
                "max_workers": {
                    "type": "integer",
                    "default": 4,
                    "description": "Maximum number of concurrent async workers",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="agent_node",
            display_name="Agent Node",
            category="AI",
            base_class="Node",
            actions=["done", "continue"],
            properties={
                "max_steps": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of agent reasoning steps",
                },
                "model": {
                    "type": "string",
                    "default": "",
                    "description": "LLM model name",
                },
                "input_key": {
                    "type": "string",
                    "default": "task",
                    "description": "Shared store key containing the agent task description",
                },
                "output_key": {
                    "type": "string",
                    "default": "result",
                    "description": "Shared store key to write the final agent output to",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="rag_node",
            display_name="RAG Node",
            category="AI",
            base_class="Node",
            actions=["default"],
            properties={
                "index_path": {
                    "type": "string",
                    "default": "",
                    "description": "Path to the vector index directory",
                },
                "top_k": {
                    "type": "integer",
                    "default": 5,
                    "description": "Number of documents to retrieve",
                },
                "query_key": {
                    "type": "string",
                    "default": "query",
                    "description": "Shared store key containing the search query",
                },
                "output_key": {
                    "type": "string",
                    "default": "context",
                    "description": "Shared store key to write retrieved documents to",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="judge_node",
            display_name="Judge Node",
            category="AI",
            base_class="Node",
            actions=["pass", "fail"],
            properties={
                "model": {
                    "type": "string",
                    "default": "",
                    "description": "LLM model name",
                },
                "criteria": {
                    "type": "string",
                    "default": "",
                    "description": "Evaluation criteria description given to the LLM",
                },
                "threshold": {
                    "type": "number",
                    "default": 0.7,
                    "description": "Score threshold (0–1) above which the judgment is 'pass'",
                },
                "input_key": {
                    "type": "string",
                    "default": "content",
                    "description": "Shared store key containing the content to evaluate",
                },
            },
        ),
        NodeTypeDefinition(
            node_type_id="subflow_node",
            display_name="Subflow Node",
            category="Flow Control",
            base_class="Node",
            actions=["default"],
            properties={
                "subflow_ref": {
                    "type": "string",
                    "default": "",
                    "description": "Relative path to the subflow .pfcgraph.yaml file",
                },
            },
        ),
    ]
}
