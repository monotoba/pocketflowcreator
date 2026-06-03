from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any


def _coerce_bool(val: Any) -> bool:
    """Convert *val* to bool, treating common YAML-false strings as False.

    ``bool("false")`` would return ``True`` (non-empty string) — this helper
    recognises the strings "false", "no", "off", and "0" as False instead.
    """
    if isinstance(val, str):
        return val.lower() not in ("false", "no", "off", "0", "")
    return bool(val)


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
    def from_mapping(cls, data: dict[str, Any]) -> NodeTypeDefinition:
        """Construct from a mapping (e.g. loaded YAML dict).

        Iterates ``dataclasses.fields(cls)`` so that adding a new field to the
        dataclass automatically makes it available here without a second edit.
        Coercion rules are inferred from each field's default / default_factory.
        """
        required = ["node_type_id", "display_name", "category", "base_class"]
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Missing required node type fields: {', '.join(missing)}")

        kwargs: dict[str, Any] = {}
        for f in dataclasses.fields(cls):
            if f.name not in data:
                continue  # absent optional field — dataclass default applies
            val = data[f.name]
            if f.default_factory is not dataclasses.MISSING:  # type: ignore[misc]
                # list or dict field: coerce to the container type
                sample = f.default_factory()  # type: ignore[misc]
                if isinstance(sample, dict):
                    kwargs[f.name] = dict(val) if isinstance(val, dict) else {}
                else:
                    kwargs[f.name] = list(val) if val is not None else []
            elif f.default is not dataclasses.MISSING and isinstance(f.default, bool):
                # bool field: use _coerce_bool so "false" strings map to False
                kwargs[f.name] = _coerce_bool(val)
            elif val is not None:
                kwargs[f.name] = str(val)
            else:
                kwargs[f.name] = val  # None passthrough (optional str fields)
        return cls(**kwargs)
