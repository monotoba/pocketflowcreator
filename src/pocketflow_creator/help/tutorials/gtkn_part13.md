# Part 13 — Data Processing Nodes

This part covers six general-purpose data-transformation nodes: Map, Reduce,
Condition, Loop Counter, Transform, and Merge.

**Prerequisite:** Complete Part 1 (Start / Stop / Basic) before this part.

---

## Tutorial T-N44: Map Node

### What it does

The **Map Node** applies a transformation expression or a named Python function to
every element of a list in the shared store. The result is a new list of the same
length stored under `output_key`. It is the flow equivalent of Python's built-in
`map()`.

### Use cases

- Normalising a list of strings (strip whitespace, lowercase, truncate)
- Extracting a field from each dict in a list (e.g. pull `url` from search results)
- Applying a scoring function to a list of candidate answers

### What you'll build

A flow — **Start → PriceMapper → Stop** — that extracts the `price` field from a
list of product dicts.

### Step-by-step

**Step 1: Create project `gtkn_part13`.**

**Step 2: Drag a Map Node** named `PriceMapper`.

**Step 3: Set Inspector properties:**

| Property | Value |
|---|---|
| `input_key` | `products` |
| `output_key` | `prices` |
| `expression` | `item["price"]` |

**Step 4: Wire Start → PriceMapper → Stop.**

**Step 5: Paste the code:**

```python
from pocketflow import Node

class PriceMapper(Node):
    def prep(self, shared):
        return shared.get(
            "products",
            [
                {"name": "Widget", "price": 9.99},
                {"name": "Gadget", "price": 24.99},
                {"name": "Thingamajig", "price": 4.50},
            ],
        )

    def exec(self, prep_res):
        return [item["price"] for item in prep_res]

    def post(self, shared, prep_res, exec_res):
        shared["prices"] = exec_res
        return "default"
```

**Step 6: Run.** `prices` will be `[9.99, 24.99, 4.5]`.

### What you learned

- Map Nodes produce an output list with exactly the same length as the input list
- The `expression` Inspector field documents the transformation without requiring a code edit
- Chain Map → Reduce to first extract a field and then aggregate it

---

## Tutorial T-N45: Reduce Node

### What it does

The **Reduce Node** collapses a list to a single value using an accumulator function:
`sum`, `min`, `max`, `join`, `count`, or a custom expression. It is the flow
equivalent of Python's `functools.reduce()` or common aggregation functions.

### Use cases

- Summing prices after a Map Node extracts them
- Finding the highest-confidence score from a list of classifier results
- Concatenating a list of text chunks into a single document

### What you'll build

Continue from T-N44: add a Reduce Node that sums the price list.

### Step-by-step

**Step 1: Add a Reduce Node** named `PriceSummer` after `PriceMapper`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `input_key` | `prices` |
| `output_key` | `total_price` |
| `operation` | `sum` |

**Step 3: Wire PriceMapper → PriceSummer → Stop.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

class PriceSummer(Node):
    def prep(self, shared):
        return shared.get("prices", [])

    def exec(self, prep_res):
        return sum(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["total_price"] = exec_res
        return "default"
```

**Step 5: Run and check:**

```
prices: [9.99, 24.99, 4.5]
total_price: 39.48
```

### What you learned

- Reduce Nodes follow Map Nodes naturally to implement a Map-Reduce pattern
- Built-in `operation` values (`sum`, `min`, `max`, `join`, `count`) cover the most common cases
- For custom logic, override `exec()` with any Python accumulation expression

---

## Tutorial T-N46: Condition Node

### What it does

The **Condition Node** evaluates a Boolean expression against a shared-store value and
routes to `true` or `false`. It is a lightweight alternative to a full Router Node
when you only need a binary decision.

### Use cases

- Checking whether a total exceeds a threshold before triggering an alert
- Branching on whether an API response was successful (status 200)
- Skipping an expensive LLM step when cached results are available

### What you'll build

Extend the shopping-cart flow: a Condition Node that routes to a "discount" branch
when `total_price > 30`.

### Step-by-step

**Step 1: Add a Condition Node** named `DiscountGate` after `PriceSummer`.

**Step 2: Declare actions:** `true`, `false`.

**Step 3: Set Inspector properties:**

| Property | Value |
|---|---|
| `input_key` | `total_price` |
| `expression` | `value > 30` |

**Step 4: Wire:**

```
PriceSummer →(default)→ DiscountGate
DiscountGate →(true)→ Stop_Discount
DiscountGate →(false)→ Stop_NoDiscount
```

**Step 5: Paste the code:**

```python
from pocketflow import Node

class DiscountGate(Node):
    THRESHOLD = 30.0

    def prep(self, shared):
        return shared.get("total_price", 0.0)

    def exec(self, prep_res):
        return prep_res > self.THRESHOLD

    def post(self, shared, prep_res, exec_res):
        shared["discount_eligible"] = exec_res
        return "true" if exec_res else "false"
```

**Step 6: Run.** With `total_price = 39.48`, routes to `Stop_Discount`.

### What you learned

- Condition Nodes are the simplest two-way router — use them for single Boolean tests
- `post()` returns `"true"` or `"false"` as strings that match edge action labels
- The result is also stored in the shared store for downstream logging or display

---

## Tutorial T-N47: Loop Counter Node

### What it does

The **Loop Counter Node** increments (or decrements) an integer counter in the shared
store on each pass and routes to `continue` while the count is below a limit, then to
`done` when the limit is reached. It is the standard way to add a bounded loop to a
flow without a Supervisor Node.

### Use cases

- Running a polling loop N times before giving up
- Iterating over a fixed batch of items when a Batch Node is not needed
- Adding retry logic with a simple iteration cap

### What you'll build

A loop that prints "Hello from iteration N" three times before exiting.

### Step-by-step

**Step 1: Add a Loop Counter Node** named `LoopCtrl` and a Basic Node named `LoopBody`.

**Step 2: Declare actions on `LoopCtrl`:** `continue`, `done`.

**Step 3: Set Inspector properties:**

| Property | Value |
|---|---|
| `counter_key` | `loop_iter` |
| `limit` | `3` |

**Step 4: Wire:**

```
Start →(default)→ LoopCtrl
LoopCtrl →(continue)→ LoopBody
LoopBody →(default)→ LoopCtrl
LoopCtrl →(done)→ Stop
```

**Step 5: Paste the code for each node:**

```python
# LoopCtrl
from pocketflow import Node

class LoopCtrl(Node):
    LIMIT = 3

    def prep(self, shared):
        return shared.get("loop_iter", 0)

    def exec(self, prep_res):
        return prep_res + 1

    def post(self, shared, prep_res, exec_res):
        shared["loop_iter"] = exec_res
        return "continue" if exec_res <= self.LIMIT else "done"
```

```python
# LoopBody
from pocketflow import Node

class LoopBody(Node):
    def prep(self, shared):
        return shared.get("loop_iter", 0)

    def exec(self, prep_res):
        return f"Hello from iteration {prep_res}"

    def post(self, shared, prep_res, exec_res):
        msgs = shared.get("messages", [])
        msgs.append(exec_res)
        shared["messages"] = msgs
        return "default"
```

**Step 6: Run and inspect:**

```
loop_iter: 4   (incremented past limit to trigger "done")
messages: ["Hello from iteration 1", "Hello from iteration 2", "Hello from iteration 3"]
```

### What you learned

- Loop Counter Nodes create bounded loops without a full Supervisor — simpler when you just need `for i in range(N)`
- The counter persists across iterations in the shared store
- Wire `done` to any exit node; the `continue` edge loops back to any earlier node

---

## Tutorial T-N48: Transform Node

### What it does

The **Transform Node** applies a Python expression to a single shared-store value and
writes the result to an output key. It is a lightweight alternative to writing a full
Basic Node when the transformation is a one-liner.

### Use cases

- Converting a string to uppercase, JSON, or a number
- Extracting a nested field: `value["results"][0]["title"]`
- Reformatting a date string from ISO to display format

### What you'll build

A Transform Node that converts a raw price float to a formatted currency string.

### Step-by-step

**Step 1: Add a Transform Node** named `PriceFormatter`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `input_key` | `total_price` |
| `output_key` | `price_display` |
| `expression` | `f"${value:.2f}"` |

**Step 3: Wire Start → PriceFormatter → Stop** (or add it after `PriceSummer` from T-N45).

**Step 4: Paste the code:**

```python
from pocketflow import Node

class PriceFormatter(Node):
    def prep(self, shared):
        return shared.get("total_price", 0.0)

    def exec(self, prep_res):
        return f"${prep_res:.2f}"

    def post(self, shared, prep_res, exec_res):
        shared["price_display"] = exec_res
        return "default"
```

**Step 5: Run:**

```
price_display: "$39.48"
```

### What you learned

- Transform Nodes are single-expression adapters — keep them for simple, stateless transformations
- For multi-step or stateful logic, use a Basic Node instead
- The `expression` Inspector field doubles as inline documentation

---

## Tutorial T-N49: Merge Node

### What it does

The **Merge Node** combines values from multiple shared-store keys into a single
output. Merge strategies include `dict_merge` (deep merge of dicts), `list_concat`
(concatenate lists), and `string_join` (join strings with a separator).

### Use cases

- Combining results from two parallel branches before a final summary
- Merging a user profile with LLM-generated recommendations into one response dict
- Concatenating retrieved context chunks into a single prompt string

### What you'll build

A Merge Node that combines `pro_argument` and `con_argument` (from Part 7's debate
pipeline) into a single `debate_summary` string.

### Step-by-step

**Step 1: Add a Merge Node** named `DebateMerger`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `input_keys` | `pro_argument,con_argument` |
| `output_key` | `debate_summary` |
| `strategy` | `string_join` |
| `separator` | `\n\n--- VS ---\n\n` |

**Step 3: Wire after the two Advocate Nodes from Part 7, or wire Start → DebateMerger → Stop
after seeding both keys in `prep()`.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

SEPARATOR = "\n\n--- VS ---\n\n"

class DebateMerger(Node):
    def prep(self, shared):
        # Seed demo values if not present.
        shared.setdefault(
            "pro_argument",
            "FOR: Higher focus, no commute, global talent pool.",
        )
        shared.setdefault(
            "con_argument",
            "AGAINST: Collaboration suffers, junior staff lose mentorship.",
        )
        return [
            shared.get("pro_argument", ""),
            shared.get("con_argument", ""),
        ]

    def exec(self, prep_res):
        return SEPARATOR.join(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["debate_summary"] = exec_res
        return "default"
```

**Step 5: Run and inspect `debate_summary`:**

```
FOR: Higher focus, no commute, global talent pool.

--- VS ---

AGAINST: Collaboration suffers, junior staff lose mentorship.
```

### What you learned

- Merge Nodes are the natural endpoint for parallel branches — they collect multiple keys into one
- `strategy: string_join` is ideal for building LLM prompts from multiple context fragments
- `strategy: dict_merge` is ideal when two nodes write complementary fields to a shared record

---

[↑ Series Index](gtkn_index.md)
[← Part 12](gtkn_part12.md)
[→ Part 14: Calendar and Agent Protocol Nodes](gtkn_part14.md)
