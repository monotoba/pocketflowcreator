from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

_SCHEMA_YAML = """\
document:
  path:
    type: string
  text:
    type: string
project:
  audience:
    type: string
    default: hobbyist
"""


def _parse_flat(raw: dict) -> list[tuple[str, str, str, str]]:
    flat: list[tuple[str, str, str, str]] = []
    for ns, keys in raw.items():
        if not isinstance(keys, dict):
            continue
        for key, props in keys.items():
            if not isinstance(props, dict):
                continue
            type_str = str(props.get("type", ""))
            default_str = str(props["default"]) if "default" in props else ""
            flat.append((str(ns), str(key), type_str, default_str))
    return flat


def _serialize(flat: list[tuple[str, str, str, str]]) -> dict:
    schema: dict[str, dict[str, dict[str, object]]] = {}
    for ns, key, type_str, default_str in flat:
        if not ns or not key or not type_str:
            continue
        schema.setdefault(ns, {})
        entry: dict[str, object] = {"type": type_str}
        if default_str:
            entry["default"] = default_str
        schema[ns][key] = entry
    return schema


def test_parse_schema_row_count() -> None:
    raw = yaml.safe_load(_SCHEMA_YAML)
    flat = _parse_flat(raw)
    assert len(flat) == 3


def test_parse_schema_default_captured() -> None:
    raw = yaml.safe_load(_SCHEMA_YAML)
    flat = _parse_flat(raw)
    audience_row = next(r for r in flat if r[1] == "audience")
    assert audience_row == ("project", "audience", "string", "hobbyist")


def test_parse_schema_no_default_empty_string() -> None:
    raw = yaml.safe_load(_SCHEMA_YAML)
    flat = _parse_flat(raw)
    path_row = next(r for r in flat if r[1] == "path")
    assert path_row == ("document", "path", "string", "")


def test_roundtrip_preserves_data() -> None:
    raw = yaml.safe_load(_SCHEMA_YAML)
    flat = _parse_flat(raw)
    schema = _serialize(flat)
    assert schema["document"]["path"] == {"type": "string"}
    assert schema["project"]["audience"] == {"type": "string", "default": "hobbyist"}


def test_serialize_skips_empty_rows() -> None:
    flat = [("", "key", "string", ""), ("ns", "", "string", ""), ("ns", "k", "", "")]
    result = _serialize(flat)
    assert result == {}


def test_roundtrip_write_and_read() -> None:
    raw = yaml.safe_load(_SCHEMA_YAML)
    flat = _parse_flat(raw)
    schema = _serialize(flat)
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        tmp = Path(f.name)
        f.write(yaml.dump(schema, default_flow_style=False))
    try:
        reloaded = yaml.safe_load(tmp.read_text(encoding="utf-8"))
        assert reloaded["document"]["text"]["type"] == "string"
        assert reloaded["project"]["audience"]["default"] == "hobbyist"
    finally:
        tmp.unlink()
