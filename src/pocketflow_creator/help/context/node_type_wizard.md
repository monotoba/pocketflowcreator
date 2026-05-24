# Custom Node Type Wizard

**Node > New Custom Node Type…** opens the wizard for defining a reusable node type.

## Fields

### Identification

| Field | Description | Example |
|---|---|---|
| **Node Type ID** | Unique snake_case identifier used in YAML and code | `sentiment_node` |
| **Display Name** | Human-readable name shown in the Component Palette | `Sentiment Analyser` |
| **Category** | Palette group this type appears under | `Analysis` |
| **Base Class** | PocketFlow base class to inherit from | `Node`, `BatchNode`, `AsyncNode` |

### Actions

List the output action strings this node can return from `post()`.
Separate with commas or enter one per line.

Example: `positive, negative, neutral`

The validator uses this list to check that wired edges have valid action labels.

### Properties

Custom properties appear in the Object Inspector when this node type is selected.

| Column | Description |
|---|---|
| **Name** | Property key (snake_case) |
| **Type** | Data type: `string`, `integer`, `number`, `boolean` |
| **Default** | Value pre-filled in the Inspector when the node is added |

### Flags

| Flag | Effect |
|---|---|
| **Is Abstract** | Type cannot be placed directly; only used as a base class for other types |
| **Allow Unknown Actions** | Skips validator check for undeclared action names |

## What the Wizard Creates

When you click **Create**:

1. `node_types/<type_id>.yaml` — the type definition (editable YAML)
2. `custom/<type_id>.py` — a Python skeleton with `prep`, `exec`, `post` stubs

The new type appears in the Component Palette after the project reloads.

## Editing an Existing Type

Open `node_types/<type_id>.yaml` from the Project Explorer. Edit it directly in the YAML editor.
Changes take effect after saving and reloading the project.

[← Help Index](../index.md) | [Tutorial 5: Creating a Custom Node Type](../tutorials/part1_fundamentals.md)
