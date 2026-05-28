# Creating Custom Nodes

PocketFlow Creator gives you two ways to extend the Component Palette with your own node types.  Choose the approach that fits your workflow:

| Approach | Best for |
|---|---|
| **GUI Wizard** | Quickly registering a node that belongs to a specific project; low ceremony; definition stored inside the project folder |
| **Node Package** (`.py` file) | Reusable nodes you want available in every project; nodes you share with teammates; nodes developed in your own editor |

Both approaches produce a `NodeTypeDefinition` and make the new node draggable from the palette immediately.

---

## Approach 1 — Using the GUI Wizard

### 1.1  Open the wizard

Go to **Node → New Custom Node Type…**  
The **Node Type Wizard** opens with three tabs: **Definition**, **Actions**, and **Properties**.

### 1.2  Definition tab

| Field | What to enter |
|---|---|
| **Type ID** | A snake_case identifier unique within this project (e.g. `weather_fetch_node`) |
| **Display Name** | The label shown in the palette and on the canvas (e.g. `Weather Fetch`) |
| **Category** | The palette group this node appears under (e.g. `Web / Search`) |
| **Base Class** | Leave as `Node` unless you need async behaviour (`AsyncNode`, `BatchNode`, etc.) |
| **Description** | Optional one-line summary shown in the Node Type Library |

### 1.3  Actions tab

Actions are the named outputs that appear as connector labels on the node.  Click **Add** to insert a row and type the action name (e.g. `default`, `error`, `retry`).  The first action in the list is the default route.

Every node should have at least one action.  The canvas uses these names to label the connector handles on the right side of the node.

### 1.4  Properties tab

Properties appear in the **Object Inspector** when the node is selected on the canvas.  Each property has:

| Column | Meaning |
|---|---|
| **Key** | The Python attribute name (e.g. `city_key`) |
| **Type** | `string`, `integer`, `number`, `bool`, or `choice` |
| **Default** | The value pre-filled in the Inspector |
| **Description** | Tooltip text shown next to the field |

For `choice` type, enter the allowed values as a comma-separated list in the **Default** column (e.g. `celsius,fahrenheit`).

### 1.5  Click OK

Creator writes a YAML definition file into `node_types/` inside your project folder and adds it to `project.yaml`.  The node appears immediately in the palette under its category.

### 1.6  Write the implementation

Open the **Python editor** tab.  A skeleton class matching your type ID is already present.  Fill in `prep`, `exec`, and `post`:

```python
from pocketflow import Node

class WeatherFetchNode(Node):
    CITY_KEY = "city"       # overridden per-instance by the Inspector

    def prep(self, shared):
        return shared.get(self.CITY_KEY, "London")

    def exec(self, prep_res):
        # call your API here
        return {"city": prep_res, "temp_c": 18.5}

    def post(self, shared, prep_res, exec_res):
        shared["weather"] = exec_res
        return "default"
```

> **Tip:** Inspector properties declared in the wizard are injected as uppercase class attributes before `prep` runs, so `self.CITY_KEY` reflects whatever the user typed in the Inspector.

---

## Approach 2 — Writing a Node Package

A **node package** is a single `.py` file you write in any editor.  Drop it into the user nodes directory and it loads automatically next time Creator starts, or immediately via the Node Type Library.

### 2.1  Where packages live

```
~/.pocketflow_creator/nodes/
```

On Windows this resolves to `C:\Users\<you>\.pocketflow_creator\nodes\`.  
Creator creates the folder on first launch; you can also open it from  
**Tools → Node Type Library → Open nodes folder**.

### 2.2  File naming

Name the file after your node class in snake_case:

```
weather_fetch_node.py   ✓
WeatherFetch.py         ✓  (works, but convention is snake_case)
_helper.py              ✗  (leading underscore — skipped by the loader)
__init__.py             ✗  (skipped)
```

### 2.3  The `__node_meta__` dict

Every package must contain a module-level `__node_meta__` dict.  It carries all identity, package, and behaviour metadata in one place — no special syntax, just a plain Python dict:

```python
__node_meta__ = {
    # ── Identity ──────────────────────────────────────────────────────────
    "node":     "Weather Fetch",       # display name shown in the palette
    "category": "Web / Search",        # palette / toolbar group

    # ── Package info  (all optional) ──────────────────────────────────────
    "version":             "1.0.0",
    "author":              "Your Name",
    "website":             "https://yoursite.example.com",
    "repo":                "https://github.com/you/weather-fetch-node",
    "description":         "Fetches current temperature for a city.",
    "tags":                ["weather", "api", "http"],
    "license":             "MIT",
    "min_creator_version": "0.2.0",

    # ── Node behaviour ────────────────────────────────────────────────────
    "actions":    ["default", "error"],
    "properties": {
        "city_key": {
            "type":        "string",
            "default":     "city",
            "description": "Shared-store key for the target city name.",
        },
        "result_key": {
            "type":        "string",
            "default":     "weather",
            "description": "Shared-store key to write the result dict into.",
        },
    },

    # ── Visual ────────────────────────────────────────────────────────────
    "color": "#0277bd",   # hex background colour for the palette icon
}
```

#### Required keys

| Key | Type | Description |
|---|---|---|
| `node` | `str` | Display name |
| `category` | `str` | Palette group (can be an existing category or a new one) |

#### Optional keys

| Key | Type | Default | Description |
|---|---|---|---|
| `version` | `str` | `"0.0.0"` | Semantic version |
| `author` | `str` | `""` | Author name |
| `website` | `str` | `""` | Author or project website URL |
| `repo` | `str` | `""` | Source repository URL |
| `description` | `str` | `""` | One-line summary |
| `tags` | `list[str]` or comma-separated `str` | `[]` | Search keywords |
| `license` | `str` | `""` | SPDX identifier (e.g. `"MIT"`) |
| `min_creator_version` | `str` | `""` | Minimum Creator version required |
| `actions` | `list[str]` | `["default"]` | Named output connectors |
| `properties` | `dict` | `{}` | Inspector properties (same schema as the wizard) |
| `color` | `str` | `"#555555"` | Hex background colour for the auto-generated icon |

### 2.4  The Node class

Put exactly one class in the file that either:

- **Extends `pocketflow.Node`** (or `AsyncNode`, `BatchNode`, `AsyncBatchNode`, `AsyncParallelBatchNode`), or
- **Has `prep`, `exec`, and `post` methods** (duck-typed — no import required if PocketFlow is not installed in your editor's environment)

The class name is converted to a `type_id` automatically:

| Class name | Derived `type_id` |
|---|---|
| `WeatherFetchNode` | `weather_fetch_node` |
| `SQLRunner` | `sql_runner_node` |
| `MyNode` | `my_node` |

> **Rule of thumb:** if the class name already ends in `Node` or `_node` the suffix is not doubled.

### 2.5  Custom icon (optional)

Set `__node_icon__` to a callable with the signature `(p: QPainter, sz: float, bg: QColor) -> None`.  The function receives a prepared `QPainter` with antialiasing enabled and the background already filled.  Draw white shapes on top.

```python
def _draw_my_icon(p, sz, bg):
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QPolygonF, QColor, QBrush
    from PySide6.QtCore import Qt
    # Example: a filled diamond
    half = sz * 0.38
    cx, cy = sz / 2, sz / 2
    pts = QPolygonF([
        QPointF(cx,         cy - half),
        QPointF(cx + half,  cy),
        QPointF(cx,         cy + half),
        QPointF(cx - half,  cy),
    ])
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawPolygon(pts)

__node_icon__ = _draw_my_icon
```

When `__node_icon__` is absent or `None`, Creator automatically generates a two-letter initials icon using the `color` from `__node_meta__`.

### 2.6  Complete example

Save the following as `~/.pocketflow_creator/nodes/weather_fetch_node.py`:

```python
"""Fetches current conditions from the Open-Meteo API (no API key needed)."""

__node_meta__ = {
    "node":        "Weather Fetch",
    "category":    "Web / Search",
    "version":     "1.0.0",
    "author":      "Your Name",
    "website":     "https://open-meteo.com",
    "description": "Returns temperature and weather code for any city.",
    "tags":        ["weather", "api", "http"],
    "license":     "MIT",
    "actions":     ["default", "error"],
    "properties": {
        "city_key": {
            "type":        "string",
            "default":     "city",
            "description": "Shared-store key holding the target city name.",
        },
        "result_key": {
            "type":        "string",
            "default":     "weather",
            "description": "Shared-store key to write the result dict into.",
        },
    },
    "color": "#0277bd",
}

__node_icon__ = None   # use auto-generated initials icon


class WeatherFetchNode:
    """Resolve a city name to coordinates, then fetch current weather."""

    def prep(self, shared):
        return {
            "city":       shared.get("city", "London"),
            "result_key": "weather",
        }

    def exec(self, prep_res):
        city = prep_res["city"]
        import json, urllib.request

        # Step 1: geocode
        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search"
            f"?name={city}&count=1&language=en&format=json"
        )
        with urllib.request.urlopen(geo_url, timeout=10) as r:
            geo = json.loads(r.read())
        if not geo.get("results"):
            return {"city": city, "error": f"City not found: {city!r}"}
        loc = geo["results"][0]

        # Step 2: current weather
        wx_url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={loc['latitude']}&longitude={loc['longitude']}"
            "&current=temperature_2m,weather_code"
        )
        with urllib.request.urlopen(wx_url, timeout=10) as r:
            wx = json.loads(r.read())
        c = wx["current"]
        return {
            "city":          city,
            "latitude":      loc["latitude"],
            "longitude":     loc["longitude"],
            "temperature_c": c["temperature_2m"],
            "weather_code":  c["weather_code"],
        }

    def post(self, shared, prep_res, exec_res):
        shared[prep_res["result_key"]] = exec_res
        return "error" if "error" in exec_res else "default"
```

---

## Installing a Package via the GUI

If you received a `.py` node package from a colleague or downloaded one:

1. Go to **Tools → Node Type Library**.
2. Click the **Installed Custom** tab.
3. Click **Install node package (.py)…**
4. Select the `.py` file.
5. If a node with the same filename is already installed Creator asks whether to replace it.
6. After a successful install the node appears immediately in the **Component Palette** under its category.  The toolbar shows the node after the next application restart.

> **To remove a package** open the nodes folder (**Open nodes folder** button), delete the `.py` file, and restart Creator.

---

## The Node Type Library Dialog

**Tools → Node Type Library** has three tabs:

| Tab | Contents |
|---|---|
| **Built-in** | All 83 built-in nodes with ID, display name, and category |
| **Installed Custom** | Every loaded node package — version, author, license, source file; click a row to see description, tags, website, and repo |
| **⚠ Errors** | Packages that failed to load, with the filename and error message.  Fix the file and restart to retry |

---

## Load Order and the `type_id` Namespace

- Built-in nodes are registered first.
- User packages are loaded in filename alphabetical order from the nodes directory.
- If a package declares a `type_id` that collides with a built-in (e.g. a file that produces `start_node`), the **built-in wins** — the package definition is silently skipped and an error is recorded in the **⚠ Errors** tab.
- Within user packages, a later file silently overwrites an earlier file with the same `type_id`.  Rename one of them to resolve the conflict.

---

## Sharing Your Node Package

A node package is a single self-contained `.py` file — send it by email, post it in a GitHub Gist, or publish it on PyPI.  Recipients install it through **Tools → Node Type Library → Install node package (.py)…** or by copying the file directly into `~/.pocketflow_creator/nodes/`.

Suggested `__node_meta__` fields to fill in before sharing:

- `version` — bump on every update so users know they have the latest
- `author` + `website` — lets users reach you
- `repo` — allows users to report issues and contribute improvements
- `description` + `tags` — makes the node discoverable in the Library dialog
- `license` — required for open-source distribution; `"MIT"` is the most permissive common choice

---

## Developing a Package in an External Editor

### Recommended workflow

1. Create the file in `~/.pocketflow_creator/nodes/` so it auto-loads on the next start.  
2. Edit in your preferred editor (VS Code, PyCharm, etc.).  
3. When you change the file, restart Creator (or use **Tools → Node Type Library → Install node package (.py)…** on the same file to hot-reload it).

### Type hints and editor support

`pocketflow.Node` is available via `pip install pocketflow`.  Adding it as a base class gives your editor full auto-complete on `prep`, `exec`, and `post`:

```python
from pocketflow import Node

class WeatherFetchNode(Node):
    def prep(self, shared: dict) -> dict: ...
    def exec(self, prep_res: dict) -> dict: ...
    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str: ...
```

If you do not want to install PocketFlow in your editor environment, duck-typing works fine — just define the three methods and the loader accepts the class.

### Keeping secrets out of the package

Never hard-code API keys in the package.  Use a **Secret Node** upstream to load credentials from environment variables or a `.env` file, and read them from the shared store in `prep`:

```python
def prep(self, shared: dict) -> dict:
    return {
        "api_key": shared.get("openai_api_key", ""),   # loaded by Secret Node
        "city":    shared.get("city", "London"),
    }
```

### Testing outside Creator

Because the class has no Creator-specific dependencies, you can unit-test it with plain pytest:

```python
# test_weather_fetch_node.py
import importlib.util, sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "weather_pkg",
    Path.home() / ".pocketflow_creator/nodes/weather_fetch_node.py",
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test_exec_returns_temperature():
    node = mod.WeatherFetchNode()
    prep_res = {"city": "London", "result_key": "weather"}
    result = node.exec(prep_res)
    assert "temperature_c" in result
    assert result["city"] == "London"
```

---

## Quick Reference

### Minimal package skeleton

```python
__node_meta__ = {
    "node":     "My Node",
    "category": "Custom",
    "actions":  ["default"],
}

class MyNode:
    def prep(self, shared):   return None
    def exec(self, prep_res): return None
    def post(self, shared, prep_res, exec_res):
        return "default"
```

### `__node_meta__` key reference

| Key | Required | Type | Description |
|---|---|---|---|
| `node` | ✓ | `str` | Display name |
| `category` | ✓ | `str` | Palette group |
| `version` | | `str` | Semantic version |
| `author` | | `str` | Your name |
| `website` | | `str` | Your website URL |
| `repo` | | `str` | Source repository URL |
| `description` | | `str` | One-line summary |
| `tags` | | `list[str]` | Search keywords |
| `license` | | `str` | SPDX identifier |
| `min_creator_version` | | `str` | Minimum Creator version |
| `actions` | | `list[str]` | Output connector names (default: `["default"]`) |
| `properties` | | `dict` | Inspector property definitions |
| `color` | | `str` | Hex icon background colour |

### Property definition schema

```python
"my_property": {
    "type":        "string",    # string | integer | number | bool | choice
    "default":     "value",
    "description": "Shown as a tooltip in the Inspector.",
    # For type "choice" only:
    "choices":     ["option_a", "option_b", "option_c"],
}
```

---

[↑ Tutorials Index](index.md)
