# Boy Scout Code-Improvement Notes

> **No changes made.** This document records opportunities to improve readability
> and maintainability, grouped by file. Nothing here is a bug (bugs are fixed
> immediately); everything here is a "leave the campsite cleaner" suggestion.

---

## Priority Key

| Symbol | Meaning |
|--------|---------|
| 🔴 | High impact — meaningfully harms readability today |
| 🟡 | Medium — noticeable rough edge, easy fix |
| 🟢 | Low — polish / nice-to-have |

---

## Cross-Cutting Issues (affect multiple files)

### 🔴 `except Exception` instead of `except ImportError`
**Files:** `app/canvas.py:9`, `app/commands.py:8`, `app/editors.py:6`

The PySide6 try/import block uses bare `except Exception` which silently swallows
real errors (e.g. a syntax error inside PySide6 itself). Change to `except ImportError`.

### 🔴 Pyright "possibly unbound" false-positives from the try/import pattern
**Files:** `app/canvas.py`, `app/editors.py`

The `try: from PySide6... except: X = object` pattern fools Pyright into
reporting every Qt type as "possibly unbound." A cleaner approach is:

```python
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from PySide6.QtWidgets import QGraphicsItem, ...
```

combined with a runtime availability guard. This eliminates all the spurious
Pyright diagnostics without adding stubs.

### 🟡 No `__all__` in any public module
**Files:** `model/`, `generation/`, `validation/`, `runtime/`

Public-facing packages (`model`, `generation`, `validation`, `runtime`) have
no `__all__`. Adding it clarifies the intended public API and prevents accidental
re-export of implementation details.

### 🟡 Duplicate display-name data in two places
**Files:** `app/canvas.py` (`_PALETTE_ITEMS_EX`), `builtin_node_types.py` (`BUILTIN_NODE_TYPES`)

Both files list display names for all 20 built-in node types. `PaletteWidget`
could look up display names from `BUILTIN_NODE_TYPES` instead of maintaining a
parallel list, giving a single source of truth.

### 🟢 Missing docstrings on model dataclasses
**Files:** `model/graph_model.py`, `model/project.py`

`NodeModel`, `EdgeModel`, `GraphModel`, and `ProjectModel` have no class-level
docstrings. A one-line description of each class's role would help newcomers.

---

## `app/main.py` (2556 lines)

### 🔴 God-class / file too large
`MainWindow` is ~2300 lines of monolithic code spanning menus, file I/O, run
logic, debug logic, dialogs, and canvas event handlers. Consider splitting into:

| Suggested file | Contents |
|----------------|----------|
| `dialogs/provider_manager.py` | `_on_provider_manager` dialog (~90 lines) |
| `dialogs/shared_store_designer.py` | `_open_shared_store_designer` dialog (~140 lines) |
| `dialogs/auto_arrange_dialog.py` | `AutoArrangeDialog` class (~70 lines, already a class but buried) |
| `run_controller.py` | `_on_run_active_flow`, `_on_debug_active_flow`, input-callback wiring |

### 🔴 Provider-construction code duplicated verbatim
**Lines 1090–1101 and 1240–1251**

Identical 12-line block for building `OllamaProvider` vs `MockProvider` from
`QSettings`. Extract to a helper:

```python
def _build_provider(self) -> MockProvider | OllamaProvider: ...
```

### 🔴 Input-callback machinery duplicated verbatim
**Lines 1118–1145 (run) and 1262–1294 (debug)**

The `_RunSignals`/`_DbgSignals` inner classes, `_input_event`, `_input_result`,
the GUI slot, and the `input_cb` closure are nearly identical in both handlers.
Extract to a helper that wires a signal to a human-input dialog and returns the
callback.

### 🟡 `import` statements inside methods
**Lines 1103, 1114, 1134, 1194, 1253, 1264, 1395, 1407, 1629, 1738, 1815, 1828,
1836, 1854, 2134**

`import threading`, `import uuid`, `import re`, and several others appear inside
handler methods. These are stdlib modules — moving them to file-level imports is
cleaner and avoids repeated module-lookup overhead.

### 🟡 `_ensure_active_graph` always returns `True`, return type should be `None`
**Line 608**

The docstring says "Always returns True" and callers guard with
`if not self._ensure_active_graph(): return` which is dead code. Change return
type to `None` and remove the boolean returns; callers become simpler.

### 🟡 Magic QSettings key strings scattered everywhere
**Lines 197, 542, 556, 1090, 1184, 1240, 1956, 2205, 2262**

`"Monotoba"`, `"PocketFlowCreator"`, `"run/provider"`, `"ollama/base_url"` etc.
appear as literals in 9+ places. Define module-level constants:

```python
_ORG = "Monotoba"
_APP = "PocketFlowCreator"
_SKEY_PROVIDER = "run/provider"
_SKEY_OLLAMA_URL = "ollama/base_url"
# …etc.
```

### 🟡 f-strings passed into `self.tr()` defeat translation
**Lines 603, 861, 1861, 2020**

```python
self.statusBar().showMessage(self.tr(f"Project saved as: {name}"))
```

The string is formatted *before* `tr()` sees it, so the translated string can
never contain `{name}`. Use a translatable template and format after:

```python
self.statusBar().showMessage(self.tr("Project saved as: %s") % name)
```

### 🟡 `_stop_action` / `_resume_action` typed as `object`
**Lines 207–208, 1313–1314, 1337, 1344–1346**

Both are annotated `object` and accessed with `# type: ignore[attr-defined]`
every time. Annotate them as `QAction` (or the appropriate Qt type) to eliminate
the casts.

### 🟡 `_on_undo` and `_on_redo` are structurally identical
**Lines 2022–2028 and 2030–2036**

Both clear the same four attributes and call `undo()`/`redo()`. Extract the
shared cleanup to `_clear_selection_state()` and call it from both:

```python
def _clear_selection_state(self) -> None:
    self._current_node = self._current_node_item = self._current_edge = None
    self._inspector_snapshot = None
    self._inspector.clear()
```

### 🟡 `assert` used for runtime narrowing in production code
**Lines 1769–1770, 1834**

`assert self._active_graph_rel is not None` in production handlers will raise
`AssertionError` if assertions are disabled (`python -O`). Replace with an
explicit guard + early return.

### 🟢 Magic number `0xFF1A1A1A` in export handler
**Line 1028**

The dark background fill for PNG export is `0xFF1A1A1A`. Name it:

```python
_PNG_BACKGROUND_DARK = 0xFF1A1A1A
```

### 🟢 Redundant `_PALETTE_ITEMS` list
**Line 102**

`_PALETTE_ITEMS` is just `_PALETTE_ITEMS_EX` without the color column and is
only used in `PaletteWidget`. `PaletteWidget` could iterate `_PALETTE_ITEMS_EX`
directly (it already knows to ignore the color). The intermediate list can be removed.

---

## `app/canvas.py` (1404 lines)

### 🔴 File has too many unrelated responsibilities
`canvas.py` mixes: layout constants, 20 icon-drawing functions, the node-type
registry, `NodeItem`, `EdgeItem`, `GraphScene`, `GraphView`, and `PaletteWidget`.
Suggested split:

| Suggested file | Contents |
|----------------|----------|
| `canvas/icons.py` | `_ico_*` functions, `_ICON_DRAW`, `_paint_node_pixmap`, `make_node_icon` |
| `canvas/items.py` | `NodeItem`, `EdgeItem`, layout constants, `_node_height` |
| `canvas/scene.py` | `GraphScene` |
| `canvas/view.py` | `GraphView` |
| `canvas/palette.py` | `PaletteWidget`, `_PALETTE_ITEMS_EX`, `NODE_TYPE_COLOR` |

### 🟡 Drag-line Z-value should be a named constant
**Line 1265** (just fixed from `-1` to `1000`)

```python
_DRAG_LINE_Z = 1000  # render above all nodes while connector is being dragged
```

Using the literal `1000` directly leaves no explanation for future maintainers.

### 🟡 `scene._dark` accessed as a raw attribute from `NodeItem.paint`
**Line 659**

```python
dark = scene._dark if hasattr(scene, "_dark") else True
```

This breaks encapsulation and the `hasattr` check is a code smell. Add a
property to `GraphScene`:

```python
@property
def is_dark(self) -> bool:
    return self._dark
```

And call `scene.is_dark` from `NodeItem.paint`.

### 🟡 20 `_ico_*` functions with inconsistent signatures
**Lines 113–533**

Most have `(p, sz)` but three (`_ico_json_llm`, `_ico_document`, `_ico_file_writer`)
additionally require `bg: QColor`. The dispatch table `_ICON_DRAW` uses `None` as
a sentinel for the three special cases, forcing an `if/elif` in `_paint_node_pixmap`.
A uniform `(p, sz, bg)` signature for all functions would let `_ICON_DRAW` dispatch
uniformly, eliminating the special-case branch.

### 🟡 `_node_at_action_port` and `_node_at_input_port` share boilerplate
**Lines 1186–1219**

Both iterate all nodes and do a hit-test with a radius threshold. Extract a
shared `_nearest_port(scene_pos, port_fn, hit_r)` helper to reduce duplication.

### 🟢 `_edge_rubber` instance variable lacks a type annotation
**Line 1184**

`self._edge_rubber: QGraphicsLineItem | None = None` is missing in `__init__`,
making the type implicit. Adding it makes IDE navigation and Pyright happy.

---

## `app/commands.py`

### 🟢 First-redo skip mechanism deserves a comment
**Lines 47–49**

The `_first_redo` flag is an established Qt undo/redo pattern (skip re-applying
on push), but it's non-obvious. A brief comment would help:

```python
def redo(self) -> None:
    # Qt calls redo() immediately on push(); skip that first call since the
    # mutation was already applied live before the command was created.
    if self._first_redo:
        self._first_redo = False
        return
```

---

## `app/editors.py`

### 🟡 `PythonHighlighter` and `YamlHighlighter` share identical structure
**Lines 12–83**

Both classes build `_rules: list[tuple[QRegularExpression, QTextCharFormat]]`
and have the same `highlightBlock` implementation. A common base class
`_RulesHighlighter(QSyntaxHighlighter)` would remove the duplication:

```python
class _RulesHighlighter(QSyntaxHighlighter):
    _rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)
```

### 🟢 Highlight rules rebuilt on every instance construction
**Lines 22–42 and 56–76**

The `QRegularExpression` and `QTextCharFormat` objects are immutable once set
and identical across all instances. Define them as `ClassVar` so they're shared:

```python
class PythonHighlighter(_RulesHighlighter):
    _rules: ClassVar[list[...]] = [...]  # built once at class definition time
```

---

## `model/graph_model.py`

### 🟡 `position: dict[str, float]` should be a typed structure
**Line 12**

The position dict always has exactly keys `"x"` and `"y"`. A `TypedDict`:

```python
class Position(TypedDict):
    x: float
    y: float
```

…or a simple `@dataclass(slots=True) class Position` would make intent explicit
and enable type-checked access (`node.position.x` vs `node.position["x"]`).

### 🟡 `find_node` is O(n) and called in tight loops
**Line 39**

`graph.find_node(edge.from_node)` is called in the validator and generator for
every edge. Document the O(n) complexity with a comment, or add a `_node_index`
cached property for callers that need repeated lookup.

---

## `model/node_type.py`

### 🟡 `from_mapping` lists field names in two places
**Lines 31–48**

The `required` list and the `cls(...)` call both enumerate every field. Adding
a new field requires updating both. A more DRY approach builds `kwargs` from
the mapping using the dataclass fields as the schema.

### 🟢 YAML `"false"` string would coerce to `True`
**Lines 47–48**

```python
allow_python_hooks=bool(data.get("allow_python_hooks", False)),
```

In YAML, unquoted `false` deserialises to `False` (correct), but a quoted
`"false"` string would coerce to `True` via `bool("false")`. An explicit check
or `yaml.safe_load` round-trip is safer:

```python
allow_python_hooks = data.get("allow_python_hooks", False) is True
```

---

## `model/project.py`

### 🟢 `auto_arrange: dict` is untyped
**Line 18**

Use `dict[str, Any]` or a dedicated `TypedDict`:

```python
class AutoArrangeSettings(TypedDict, total=False):
    algorithm: str
    connector_style: str
    h_gap: int
    v_gap: int
    max_cols: int
```

---

## `graph_io.py`

### 🟡 `_parse_node` and `_parse_edge` should be `@staticmethod`
**Lines 31–50**

Neither method uses `self`. Marking them `@staticmethod` communicates that they
are pure data-transformation functions with no dependency on instance state.

### 🟡 Same for `GraphSaver._node_to_dict` and `_edge_to_dict`
**Lines 68–91**

Same reason — no `self` usage.

### 🟢 Schema version mismatch raises immediately with no migration note
**Lines 18–21**

A comment noting this is intentional ("no backwards compat — files must match")
would stop future maintainers from thinking it's an oversight.

---

## `project_io.py`

### 🟡 Same `@staticmethod` opportunity
Same as `graph_io.py` — `ProjectLoader.load` is a single inline method that
could be decomposed into `@staticmethod` helpers symmetric to `GraphLoader`.

---

## `validation/graph_validator.py`

### 🔴 Duplicate error code `PFCE2102`
**Lines 114 and 123**

Two distinct errors share the same code:
- `PFCE2102`: "has no subflow_ref property" (line 114)
- `PFCE2102`: "references missing graph" (line 123)

The second should be a new code, e.g. `PFCE2103`.

### 🟡 All `_validate_*` helpers should be `@staticmethod`
**Lines 33–129**

None of the `_validate_*` methods use `self`. Mark them `@staticmethod` to make
their purity explicit.

### 🟡 `node_ids()` set computed redundantly
**Lines 59 and 47**

`_validate_edges` calls `graph.node_ids()` and `_validate_start_node` also calls
it. `validate()` could compute it once and pass it as a parameter to sub-methods.

---

## `runtime/runner.py`

### 🔴 `FlowRunner.steps` is a 160-line method with a long if/elif chain
**Lines 158–298**

Each node-type handler is 10–30 lines embedded in a `while` loop. Extract each
into its own private method:

```python
def _handle_llm_node(self, node, provider, shared_store, project_root) -> tuple[str, str, str]: ...
def _handle_classifier_node(self, node, provider, available_actions, shared_store, project_root) -> tuple[str, str, str]: ...
def _handle_judge_node(...) -> ...: ...
def _handle_agent_node(...) -> ...: ...
def _handle_human_input_node(...) -> ...: ...
```

This makes each handler independently testable and the main loop scannable.

### 🟡 `on_step` and `input_callback` typed as `object` instead of `Callable`
**Lines 143, 309, 330**

```python
on_step: object = None
input_callback: object = None
```

Use proper callable types:

```python
from collections.abc import Callable
on_step: Callable[[RunStep], None] | None = None
input_callback: Callable[[dict, dict], object] | None = None
```

This lets type checkers verify call sites and removes the `# type: ignore[operator]`
comment on line 356.

### 🟡 `bp = breakpoints or set()` is falsy-ambiguous
**Line 344**

An empty `set()` is falsy, so `breakpoints or set()` would replace an explicitly
passed `set()` with a new `set()`. The intent is "default if None":

```python
bp: set[str] = breakpoints if breakpoints is not None else set()
```

### 🟢 `# noqa: UP028` suppresses a valid Pythonic suggestion
**Lines 177, 184**

The inner subflow loop is:
```python
inner_steps = list(self.steps(...))
for inner_step in inner_steps:
    yield inner_step
```

UP028 suggests `yield from` — but the list materialisation is intentional (to
read `inner_steps[-1]` after the loop). A comment explaining *why* `list()` is
needed would be clearer than a noqa suppression.

---

## `runtime/providers.py`

### 🟡 `OllamaProvider` only catches `URLError`; other exceptions leak
**Lines 41–42**

`json.JSONDecodeError` (malformed response), `socket.timeout`, and `OSError`
would propagate as-is. Broaden the catch or add explicit handlers for
`json.JSONDecodeError`:

```python
except (urllib.error.URLError, json.JSONDecodeError) as exc:
    raise RuntimeError(f"Ollama request failed: {exc}") from exc
```

### 🟢 `LLMProvider` Protocol method body should have a docstring
**Line 11**

The protocol's `complete` method has `...` as its body. A one-line docstring
describing the expected contract (returns the model's completion string) would
help when implementing custom providers.

---

## `generation/python_generator.py`

### 🟡 `_class_name` and `_var_name` should be `@staticmethod`
**Lines 64–69**

Neither uses `self`. Mark them `@staticmethod` for clarity.

### 🟡 `_node_ctx` return type is untyped `dict`
**Line 53**

Use `dict[str, Any]` or a `TypedDict`:

```python
class _NodeCtx(TypedDict):
    class_name: str
    var_name: str
    title: str
    reads: list[str]
    writes: list[str]
    action: str
```

---

## `app/code_manager.py`

### 🟡 `add_node` reads the file twice when the marker already exists
**Lines 93–98**

When the `start_marker` is already present, the function reads the file with
`read_text()` and then scans the lines to find the marker. It already has the
text in memory — reuse it instead of calling `read_text()` a second time.

### 🟢 `_stem_from_rel` second `.replace` is too broad
**Line 53**

```python
name.replace(".pfcgraph.yaml", "").replace(".yaml", "")
```

The second `.replace(".yaml", "")` would incorrectly strip `.yaml` from a file
named `foo.bar.yaml` (not a `.pfcgraph.yaml` file). More precise:

```python
stem = Path(graph_rel).name
return stem[: -len(".pfcgraph.yaml")] if stem.endswith(".pfcgraph.yaml") else Path(stem).stem
```

---

*End of Boy Scout Notes — 2026-05-27*
