# Part 3 — Flow Control and Human Interaction: Router, Human Review, Human Input

Parts 1 and 2 covered linear flows — nodes that execute one after the other in a fixed sequence. Real applications rarely work that way. Sometimes a flow needs to branch based on data; sometimes it needs to pause and ask a human whether to continue. Part 3 introduces the three nodes that add dynamic, human-aware behaviour to your graphs.

The **Router Node** examines the shared store and picks one of several paths. The **Human Review Node** pauses the flow and waits for a person to approve or reject what has been produced so far. The **Human Input Node** opens a text dialog at runtime and captures whatever the user types, storing it in the shared store for downstream nodes to use.

Complete Parts 1 and 2 before starting here.

---

## Tutorial T-N7: The Router Node

### What it does

The **Router Node** is a conditional branch point. Its `post()` method reads one or more values from the shared store, applies logic, and returns a different action string depending on what it finds. Each unique action string corresponds to a separate output port on the node tile, and each port is wired to a different downstream node. This is how PocketFlow flows implement if/else branching, multi-class dispatch, and state-machine transitions.

### Use cases

- Branching on a numeric threshold (e.g. score > 0.8 → "high", else → "low")
- Dispatching to different processing pipelines based on a content type flag
- Implementing retry logic: checking whether a result is acceptable and looping back if not
- Routing customer requests to different handlers based on intent classification

### What you'll build

A five-node flow — **Start → HumanInput → Router → Stop_Positive / Stop_Negative** — where the Router reads a numeric sentiment score from the shared store and routes "positive" (score > 0) or "negative" (score ≤ 0).

> ⚠️ **Note:** The **Human Input Node** is covered properly in T-N9, but we use a simplified version here — a Basic Node that simulates user input — so you can focus on the Router itself. Replace it with a real Human Input Node after completing T-N9.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part3_router`. A blank canvas opens.

**Step 2: Build the canvas**

Drag and arrange the following nodes left to right:

1. **Start Node**
2. **Basic Node** — rename to `SentimentInput` (simulates user input for now)
3. **Router Node** — from the **Component Palette**, Flow Control category
4. **Stop Node** — rename to `Stop_Positive`
5. **Stop Node** — rename to `Stop_Negative`

Place `Stop_Positive` above and to the right of the Router, and `Stop_Negative` below and to the right of the Router, so the branching shape is visually obvious on the canvas.

**Step 3: Add multiple actions to the Router Node**

Click the **Router Node** to select it. In the **Object Inspector**, find the **Actions** field. It likely starts with just `default`. Replace this with two actions:

- `positive`
- `negative`

After setting both actions, the Router Node tile on the canvas shows two output port circles: one labelled `positive` (top) and one labelled `negative` (bottom). Every declared action must be wired to a downstream node or validation will fail.

> 💡 **Tip:** The **Actions** field in the inspector is authoritative. Whatever action strings your `post()` method returns must appear in this field. PocketFlow Creator uses the Actions field to draw the output ports and to validate that all ports are wired. Adding a new action automatically adds a new port — you never need to manually create ports.

**Step 4: Wire the flow**

Connect the nodes:

1. Start →(default)→ SentimentInput
2. SentimentInput →(default)→ Router
3. Router →(positive)→ Stop_Positive
4. Router →(negative)→ Stop_Negative

When wiring from the Router, be sure to drag from the specific port circle labelled `positive` or `negative`, not just any point on the node's right edge.

**Step 5: Write the SentimentInput code**

Select **SentimentInput** and open the **Python editor tab**. This node simulates a user providing a sentiment score:

```python
from pocketflow import Node

class SentimentInput(Node):
    """Simulates a user providing a sentiment score for routing."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        # In a real flow this would come from a Human Input Node
        # or from an LLM Classifier. Here we hard-code a value
        # so you can test both branches by changing this number.
        return 1  # Try changing to -1 to test the negative branch.

    def post(self, shared, prep_res, exec_res):
        # Store the sentiment score so the Router can read it.
        shared["sentiment_score"] = exec_res
        return "default"
```

**Step 6: Write the Router Node code**

Select the **Router Node** and open the **Python editor tab**. The router reads the sentiment score and returns an action string:

```python
from pocketflow import Node

class RouterNode(Node):
    """Routes the flow based on the sentiment score in the shared store."""

    def prep(self, shared):
        # Read the sentiment score placed by SentimentInput.
        return shared.get("sentiment_score", 0)

    def exec(self, prep_res):
        # Decide which branch to take. The router does not
        # need to compute anything complex — just inspect the value.
        if prep_res > 0:
            return "positive"
        else:
            return "negative"

    def post(self, shared, prep_res, exec_res):
        # exec_res is already the action string we want.
        # Store the routing decision for audit purposes.
        shared["routing_decision"] = exec_res
        # Return the action string to tell the runner which edge to follow.
        return exec_res
```

Save both files with **Ctrl+S**.

**Step 7: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The flow should follow the `positive` branch (since `exec_res = 1`). The **Run Log tab** will show the routing decision. Switch to the **Shared Store tab** and confirm:

```
sentiment_score: 1
routing_decision: "positive"
```

**Step 8: Test the negative branch**

Change the return value in `SentimentInput.exec()` from `1` to `-1`, save, and run again. The flow will now follow the `negative` branch, reaching `Stop_Negative` instead. Confirm in the Run Log and Shared Store.

### What you learned

- The Router Node returns different action strings from `post()` to follow different edges
- Each action in the **Actions** inspector field creates a corresponding output port on the canvas
- All declared actions must be wired to downstream nodes or validation fails
- The router pattern is the primary way to implement branching logic in PocketFlow
- You can store the routing decision in the shared store for debugging and audit trails

---

## Tutorial T-N8: The Human Review Node

### What it does

The **Human Review Node** pauses the flow at runtime and displays the content stored under a specified shared store key in a dialog box. The human reading the dialog can click **Approve** or **Reject**. The node then returns `"approved"` or `"rejected"` as its action string, routing the flow to the corresponding downstream node. This is the standard way to implement quality-control checkpoints in automated pipelines — the flow does its work, then pauses for a human to verify the result before proceeding.

### Use cases

- Reviewing LLM-generated content before publishing or emailing it
- Approving extracted data before writing it to a database
- Providing a safety checkpoint in an autonomous agent pipeline
- Allowing a human editor to reject and trigger revision of draft text

### What you'll build

A six-node flow — **Start → ContentGenerator → HumanReview → (approved: Publisher, rejected: Reviser → loop back to HumanReview)**. The ContentGenerator produces a draft; the HumanReview node asks a human whether to publish or revise it.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part3_review`.

**Step 2: Build the canvas**

Drag and position the following nodes:

1. **Start Node** — far left
2. **Basic Node** — rename to `ContentGenerator`
3. **Human Review Node** — from the **Component Palette**, Human Interaction category
4. **Stop Node** — rename to `Publisher` — upper right (the "approved" exit)
5. **Basic Node** — rename to `Reviser` — lower right
6. Loop: `Reviser` routes back to `HumanReview`

For the loop, you will wire `Reviser →(default)→ HumanReview`, creating a cycle in the graph.

> ⚠️ **Note:** PocketFlow's validator allows loops (cycles) in graphs as long as every node's output ports are wired. Loops are common in review-and-revise patterns. Be careful not to create an infinite loop — your `Reviser` logic should modify the draft each iteration so that eventually a human approves it (or add a maximum-iterations counter).

**Step 3: Configure the Human Review Node**

Click the **Human Review Node** to select it. In the **Object Inspector**:

- **input_key**: Set to `draft`. The node will display `shared["draft"]` in the review dialog.
- **Actions**: Confirm they are `approved` and `rejected` (these should be the defaults for this node type).

**Step 4: Wire the flow**

Connect the nodes:

1. Start →(default)→ ContentGenerator
2. ContentGenerator →(default)→ HumanReview
3. HumanReview →(approved)→ Publisher
4. HumanReview →(rejected)→ Reviser
5. Reviser →(default)→ HumanReview  ← this creates the loop

**Step 5: Write the ContentGenerator code**

```python
from pocketflow import Node

class ContentGenerator(Node):
    """Generates a draft text for human review."""

    def prep(self, shared):
        # Read an existing draft iteration count, defaulting to 0.
        return shared.get("iteration", 0)

    def exec(self, prep_res):
        iteration = prep_res
        if iteration == 0:
            return "First draft: PocketFlow Creator is a visual LLM pipeline designer."
        else:
            return (
                f"Revised draft (iteration {iteration}): "
                "PocketFlow Creator is an intuitive visual designer for building "
                "and running LLM-powered workflows. It supports real-time editing, "
                "validation, and execution of complex AI pipelines."
            )

    def post(self, shared, prep_res, exec_res):
        shared["draft"] = exec_res
        return "default"
```

**Step 6: Write the Reviser code**

```python
from pocketflow import Node

class Reviser(Node):
    """Records the rejection and increments the iteration counter."""

    def prep(self, shared):
        return shared.get("iteration", 0)

    def exec(self, prep_res):
        # Increment the iteration counter so ContentGenerator
        # produces an improved draft on the next pass.
        return prep_res + 1

    def post(self, shared, prep_res, exec_res):
        shared["iteration"] = exec_res
        print(f"Draft rejected. Starting revision iteration {exec_res}.")
        return "default"
```

Save all files with **Ctrl+S**.

> 💡 **Tip:** In a production flow, the `Reviser` node might also call an LLM to automatically improve the draft based on the human's rejection, rather than just incrementing a counter. The Human Review Node captures the *decision* (approve/reject) while an LLM node handles the actual revision. Combining these creates a powerful human-in-the-loop refinement loop.

**Step 7: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. When the flow reaches the Human Review Node, a dialog window opens showing the content of `shared["draft"]`. Read the draft, then click either **Approve** (the flow proceeds to Publisher) or **Reject** (the flow loops through Reviser and ContentGenerator to produce an improved draft, then pauses for review again).

**Step 8: Observe the loop in the Run Log**

Click **Reject** the first time, then **Approve** on the second review. The **Run Log tab** shows the full execution trace including both iterations. The **Shared Store tab** shows `iteration: 1` and the revised draft text.

### What you learned

- The Human Review Node pauses the flow and displays `shared[input_key]` to a human
- The human's Approve/Reject choice routes the flow along the `"approved"` or `"rejected"` port
- Loops (cycles) in the graph are valid as long as all ports are wired
- Combining Human Review with a Reviser node creates a human-in-the-loop refinement pattern
- The iteration counter pattern prevents unlimited looping in simple flows

---

## Tutorial T-N9: The Human Input Node

### What it does

The **Human Input Node** opens a text input dialog at runtime and waits for the user to type something and press **OK**. The entered text is stored in the shared store under `output_key`. Unlike the Human Review Node (which shows existing content and asks for a binary decision), the Human Input Node *captures new information* from the user mid-flow. It is the primary mechanism for interactive flows that need live user-provided data.

### Use cases

- Capturing a search query or question from the user before sending it to an LLM
- Prompting the user for a file path, an API key, or configuration values at run time
- Building conversational flows where each turn requires fresh user input
- Collecting user preferences or parameters that should not be hard-coded

### What you'll build

A four-node flow — **Start → HumanInput → Greeter → Stop** — where `HumanInput` captures the user's name and `Greeter` uses that name to write a personalised greeting to `shared["message"]`.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part3_input`.

**Step 2: Build the canvas**

Drag and wire the following nodes:

1. **Start Node**
2. **Human Input Node** — from the **Component Palette**, Human Interaction category
3. **Basic Node** — rename to `Greeter`
4. **Stop Node**

Wire: Start →(default)→ HumanInput →(default)→ Greeter →(default)→ Stop.

**Step 3: Configure the Human Input Node**

Click the **Human Input Node** to select it. In the **Object Inspector**:

- **prompt**: Set to `Please enter your name:`. This text appears as the label above the input field in the dialog.
- **output_key**: Set to `name`. The text the user types will be stored in `shared["name"]`.

No custom code is required for the Human Input Node — all its behaviour is defined by these two properties.

> 💡 **Tip:** The **prompt** text in the inspector is what the user sees in the dialog box. Make it as clear and specific as possible. Vague prompts like "Enter value:" lead to user confusion. Good prompts like "Enter the topic you want to research:" set clear expectations.

**Step 4: Write the Greeter code**

Select the **Greeter** node and open the **Python editor tab**:

```python
from pocketflow import Node

class Greeter(Node):
    """Reads the user's name and writes a personalised greeting."""

    def prep(self, shared):
        # The Human Input Node stored the user's name under "name".
        # We read it here and return it to exec().
        name = shared.get("name", "").strip()
        if not name:
            # Fall back gracefully if the user submitted an empty string.
            name = "Friend"
        return name

    def exec(self, prep_res):
        # Build a personalised greeting using the user's name.
        # prep_res is the name string returned by prep().
        greeting = f"Hello, {prep_res}! Welcome to PocketFlow Creator."
        return greeting

    def post(self, shared, prep_res, exec_res):
        # Store the greeting in the shared store.
        shared["message"] = exec_res
        # Also print it so it appears in the Run Log tab.
        print(exec_res)
        return "default"
```

Save with **Ctrl+S**.

**Step 5: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. When the flow reaches the Human Input Node, a dialog appears with the prompt "Please enter your name:". Type your name and click **OK**. The flow continues to the Greeter node, which reads `shared["name"]` and constructs the greeting.

**Step 6: Check the results**

After the flow completes, check the **Run Log tab** for the printed greeting, and the **Shared Store tab** for:

```
name: "Your Name"
message: "Hello, Your Name! Welcome to PocketFlow Creator."
```

> ⚠️ **Note:** If the user clicks **Cancel** on the Human Input dialog, the node stores an empty string in `shared[output_key]`. Your downstream nodes should always handle the empty string case gracefully, as shown in the Greeter's `prep()` method above with the `"Friend"` fallback.

**Step 7: Compare Human Input vs pre-populated shared store**

In some flows you might want to pre-seed the shared store from the command line or from a calling parent flow rather than asking the user at runtime. The choice depends on your use case:

- Use **Human Input Node** when the flow is *interactive* — you want to prompt a live user at a specific point in execution.
- Use the **Start Node's `post()`** to pre-populate when the flow is *automated* — running in a batch pipeline or called from another flow with known inputs.
- Use a **Subflow Node** (covered in Part 6) when the inputs come from a parent flow's shared store, because the parent store is automatically available to the subflow.

The Human Input Node is intentionally simple — it captures one string at a time. For multi-field forms, chain multiple Human Input Nodes or use a single Basic Node with a custom dialog.

### What you learned

- The Human Input Node opens a dialog and stores the user's text in `shared[output_key]`
- The `prompt` inspector property sets the label the user sees in the dialog
- No custom code is needed — configure via the inspector
- Always handle the empty-string case downstream in case the user clicks Cancel
- Human Input is for interactive flows; pre-populate the shared store for automated flows

---

[← Previous Part: Foundation Nodes](gtkn_part1.md)  
[→ Next Part: LLM Nodes](gtkn_part4.md)  
[↑ Series Index](gtkn_index.md)  
[↑ Tutorials Index](index.md)
