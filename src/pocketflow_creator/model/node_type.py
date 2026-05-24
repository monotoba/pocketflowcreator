from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class NodeTypeDefinition:
    """Reusable visual component metadata.

    Standard and custom node types should use the same metadata model so custom
    nodes can inherit from built-in types just as Delphi/VB components do.
    """

    node_type_id: str
    display_name: str
    category: str
    base_class: str
    python_class: str | None = None
    module: str | None = None
    description: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    actions: list[str] = field(default_factory=list)
    reads: list[str] = field(default_factory=list)
    writes: list[str] = field(default_factory=list)
    allow_python_hooks: bool = False
    allow_prompt_files: bool = False

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "NodeTypeDefinition":
        required = ["node_type_id", "display_name", "category", "base_class"]
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Missing required node type fields: {', '.join(missing)}")
        return cls(
            node_type_id=str(data["node_type_id"]),
            display_name=str(data["display_name"]),
            category=str(data["category"]),
            base_class=str(data["base_class"]),
            python_class=data.get("python_class"),
            module=data.get("module"),
            description=str(data.get("description", "")),
            properties=dict(data.get("properties", {})),
            actions=list(data.get("actions", [])),
            reads=list(data.get("reads", [])),
            writes=list(data.get("writes", [])),
            allow_python_hooks=bool(data.get("allow_python_hooks", False)),
            allow_prompt_files=bool(data.get("allow_prompt_files", False)),
        )
