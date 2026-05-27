# Part 1 — Foundation Nodes: Start, Stop, and Basic

Every PocketFlow graph is built from the same three foundation nodes: a **Start Node** that kicks things off, a **Stop Node** that signals completion, and one or more **Basic Nodes** that do the actual work in between. Before you can build any of the more specialised nodes covered in later parts, you need to feel completely comfortable with these three — they appear in every single flow you will ever create.

Work through the three tutorials below in order. By the end of Part 1 you will have a working two-node flow, an extended flow with multiple exits, and a custom greeting flow that writes to the shared store.

---

## Tutorial T-N1: The Start Node

### What it does

The **Start Node** is the mandatory entry point for every PocketFlow graph. When the PocketFlow runner begins executing a graph it looks for the Start Node and calls its lifecycle methods first. The Start Node's `post()` method always returns the action string `"default"`, which drives the runner along the first edge out of the graph. You may optionally use the Start Node's `post()` method to seed the shared store with initial values your downstream nodes need.

### Use cases

- Initialising the shared store with default values before any other node runs
- Marking the single entry point of a graph so the runner knows where to begin
- Setting environment-level metadata (run ID, timestamp, user name) that all downstream nodes can read

### What you'll build

A minimal two-node flow — **Start → Stop** — that validates and runs successfully, producing a clean entry in the **Run Log tab**.

### Step-by-step

**Step 1: Create a new project**

Open PocketFlow Creator. If a temporary project is already open (the title bar shows `[temp]`) you can use it directly; otherwise go to **File > New Project**, give the project a name such as `gtkn_part1`, and choose a folder. A new blank graph named `main.pfcgraph.yaml` opens automatically on the **Canvas**. The **Project Explorer** on the left shows the project file tree.

> 💡 **Tip:** The blank project always opens with an empty canvas. If you see stray nodes from a previous session, press **Ctrl+A** to select all and **Delete** to remove them before starting.

**Step 2: Drag a Start Node onto the canvas**

Locate the **Component Palette** in the left dock. It lists every available node type grouped by category. Find **Start Node** under the **Flow Control** category and drag it onto the **Canvas**. Drop it near the left-centre of the canvas so there is room to the right for more nodes. The node tile appears with the title "Start Node", a left input port (which has no incoming edge for a Start Node), and a single right output port labelled `default`.

**Step 3: Inspect the Start Node**

Click the Start Node tile once to select it. The **Object Inspector** on the right dock now shows the node's properties. You will see a **Title** field (currently "Start Node") and very little else — the Start Node intentionally has no configurable properties beyond its title, because its only job is to mark the beginning of the flow and return `"default"` to the runner. This simplicity is by design: a Start Node should never contain business logic.

**Step 4: Drag a Stop Node onto the canvas**

Back in the **Component Palette**, find **Stop Node** (also under **Flow Control**) and drag it to the right of your Start Node, leaving a comfortable gap of about 150 pixels between them. The Stop Node tile appears with a left input port and no output ports — it is a terminal node with no outgoing edges.

**Step 5: Wire the Start Node to the Stop Node**

Hover your mouse over the right edge of the Start Node tile. A small filled circle appears on the `default` output port. Click and drag from that circle toward the Stop Node's left input port. When the cursor is close enough to the input port, the port highlights to indicate a valid connection. Release the mouse to create the edge. A directed arrow labelled `default` now connects the two nodes.

> ⚠️ **Note:** You must drag from the *output* port (right side, labelled action circle) to the *input* port (left side dot). Dragging in the other direction will not create an edge. If the arrow does not appear, try hovering more precisely over the output port circle until it turns solid, then drag.

**Step 6: Validate the flow**

Press **Ctrl+Shift+V** (or go to **Project > Validate**). The validation panel runs a series of checks: every graph must have exactly one Start Node, at least one Stop Node, and every output port must be wired. If everything is correct, a green banner reads "Validation passed — no issues found." If you see red error badges on nodes, re-read the error message, fix the issue, and validate again.

**Step 7: Run the flow**

Press **F5** (or go to **Run > Run Active Flow**). The runner executes the graph. Switch to the **Run Log tab** at the bottom of the screen. You should see log lines similar to:

```
[INFO] Starting flow: main
[INFO] Executing: Start Node → default
[INFO] Executing: Stop Node
[INFO] Flow complete.
```

The flow ran, moved from Start to Stop along the `default` edge, and exited cleanly.

### What you learned

- Every flow needs exactly one Start Node as its entry point
- The Start Node's output port is always labelled `default`
- Wiring is done by dragging from an output port circle to an input port dot
- Validation (Ctrl+Shift+V) checks the graph structure before running
- The **Run Log tab** shows the execution trace of the flow

---

## Tutorial T-N2: The Stop Node

### What it does

The **Stop Node** signals that the flow has reached a successful (or intentional) terminal state. When the runner reaches a Stop Node it halts execution and reports the flow as complete. A graph must have at least one Stop Node, but it may have many — different Stop Nodes can represent different outcomes, such as a success exit and an error exit. The Stop Node has no `exec()` logic; it is purely a structural marker that the runner recognises.

### Use cases

- Marking the normal successful end of a flow
- Providing separate exit points for different outcomes (e.g. `Stop_Ok` and `Stop_Error`)
- Clearly communicating flow topology to other developers reading the canvas

### What you'll build

You will extend the two-node flow from T-N1 by adding a second **Stop Node** labelled "Error Exit", wired to the Start Node via a second action port. This demonstrates how multiple exit points work before you need them in earnest.

### Step-by-step

**Step 1: Open the flow from T-N1**

If you closed PocketFlow Creator since T-N1, reopen the `gtkn_part1` project. The `main.pfcgraph.yaml` graph should be visible on the **Canvas** with a Start Node wired to a single Stop Node.

**Step 2: Add a second Stop Node**

Drag a second **Stop Node** from the **Component Palette** onto the **Canvas**, positioning it below the existing Stop Node. You now have two Stop Nodes side by side on the right of the canvas.

**Step 3: Rename the Stop Nodes for clarity**

Click the original Stop Node to select it. In the **Object Inspector**, change the **Title** field to `Stop — Success`. Click the new Stop Node and change its **Title** to `Stop — Error`. Node titles appear in the tile header on the canvas, making the intent of each exit immediately visible to anyone reading the graph.

> 💡 **Tip:** Descriptive Stop Node titles are especially valuable in complex flows with five or more exits. A title like "Stop — Rate Limited" tells future readers exactly why the flow ended there without requiring them to trace back through the graph logic.

**Step 4: Add an "error" action to the Start Node**

Click the **Start Node** to select it. In the **Object Inspector**, locate the **Actions** field. By default it contains only `default`. Click the **+** button (or the **Add Action** link, depending on your version) to add a second action. Type `error` and confirm. The Start Node tile on the canvas now shows two output port circles: `default` (top) and `error` (bottom). This step is artificial — a real Start Node would never return `"error"` — but it lets us demonstrate the wiring mechanism cleanly.

**Step 5: Wire the error port to the error Stop Node**

Hover over the `error` output port on the Start Node and drag to the `Stop — Error` node's input port. You now have two edges leaving the Start Node: `default → Stop — Success` and `error → Stop — Error`. The canvas now clearly shows a flow with two possible outcomes.

**Step 6: Validate and run**

Press **Ctrl+Shift+V** to validate. Both Stop Nodes are reachable, so the flow passes validation. Press **F5** to run. The runner always executes the `"default"` action path (because the generated Start Node code returns `"default"`), so you will see the flow reach `Stop — Success`. The `Stop — Error` exit exists in the graph topology but is not reachable until a real upstream node returns `"error"`.

> ⚠️ **Note:** PocketFlow's validator checks that all *declared* actions have wired edges — it does not check whether those edges can actually be reached at runtime. Adding unreachable Stop Nodes is valid and is a common pattern when you want to reserve exit ports for future logic.

**Step 7: Clean up for T-N3**

Remove the `error` action you added to the Start Node (select it, click the action in the Inspector, press **Delete**) and delete the `Stop — Error` node (select it, press **Delete**). Rename the remaining Stop Node back to "Stop Node". You should end with the minimal Start → Stop flow again. Save with **Ctrl+S**.

### What you learned

- A graph can have multiple Stop Nodes representing different flow outcomes
- Descriptive titles on Stop Nodes make the graph self-documenting
- Each declared action on a node creates a new output port that must be wired
- PocketFlow validates that all declared actions have wired edges

---

## Tutorial T-N3: The Basic Node

### What it does

The **Basic Node** is the general-purpose workhorse of PocketFlow. It implements three lifecycle methods that together cover every common processing task: `prep(shared)` reads data from the shared store and prepares it for processing; `exec(prep_res)` does the core work — computation, transformation, external API calls — and returns a result; and `post(shared, prep_res, exec_res)` writes results back to the shared store and returns an action string that tells the runner which edge to follow next. Most flows are built primarily from Basic Nodes, with specialised nodes used only where their built-in behaviour provides a meaningful shortcut.

### Use cases

- Transforming data already in the shared store (format conversion, string manipulation, parsing)
- Calling external APIs or libraries and storing the result
- Making decisions based on shared store state and branching accordingly
- Logging, metrics collection, or side effects that do not fit a specialised node

### What you'll build

A three-node flow — **Start → BasicGreeter → Stop** — where `BasicGreeter` writes a greeting message to `shared["message"]`. You will view the result in the **Shared Store tab** after running.

### Step-by-step

**Step 1: Ensure you have the clean Start → Stop flow**

Your canvas should show the Start Node wired to a single Stop Node from the cleanup at the end of T-N2. If not, recreate that flow now (drag a Start Node, drag a Stop Node, wire them).

**Step 2: Drag a Basic Node onto the canvas**

Find **Basic Node** in the **Component Palette** under the **Core** category and drag it onto the canvas between the Start Node and the Stop Node. You may need to move the Stop Node to the right to make room. Place the Basic Node so the left-to-right order is: Start → Basic → Stop.

**Step 3: Rename the Basic Node**

Click the Basic Node to select it. In the **Object Inspector**, change the **Title** to `BasicGreeter`. This title appears in the node header on the canvas and also becomes the class name in the generated Python code, so choose something meaningful. Class names are generated in PascalCase from the title, so "BasicGreeter" will produce a class called `BasicGreeter`.

**Step 4: Set the output key**

In the **Object Inspector** (with BasicGreeter selected), find the **Output Key** field and set it to `message`. This documents that this node writes to `shared["message"]`. Setting these keys in the inspector does not automatically generate code to use them — it documents the data contract and allows the validator to flag mismatches — but you will reference `"message"` in the code you write shortly.

**Step 5: Wire the edges**

First, delete the existing Start → Stop edge (click the edge to select it, then press **Delete**). Then:

1. Drag from the Start Node's `default` output port to the BasicGreeter's input port.
2. Drag from the BasicGreeter's `default` output port to the Stop Node's input port.

The canvas now shows: Start →(default)→ BasicGreeter →(default)→ Stop.

> 💡 **Tip:** Use **View > Auto Arrange… (Ctrl+Shift+L)** after placing nodes to snap them into a clean left-to-right layout automatically. The Layered algorithm (the default) works well for linear flows like this one.

**Step 6: Open the Python editor and write the node code**

Select the BasicGreeter node on the canvas. At the bottom of the IDE, click the **Python editor tab**. The editor shows the generated skeleton for the selected node. Replace the skeleton with the following complete implementation:

```python
from pocketflow import Node

class BasicGreeter(Node):
    """Writes a greeting to shared['message']."""

    def prep(self, shared):
        # Read any input we need from the shared store.
        # For this simple node we do not need any existing values,
        # so we just return None to signal that exec() needs no input.
        return None

    def exec(self, prep_res):
        # Do the main work. prep_res is whatever prep() returned.
        # Here we simply build a greeting string.
        greeting = "Hello from PocketFlow Creator! The shared store is working."
        return greeting

    def post(self, shared, prep_res, exec_res):
        # exec_res is whatever exec() returned — our greeting string.
        # We store it in the shared store under the key "message".
        shared["message"] = exec_res
        # Return the action string that determines which edge to follow.
        return "default"
```

Press **Ctrl+S** to save the code.

**Step 7: Understand the three lifecycle methods**

Take a moment to read the code carefully before running it. `prep(shared)` receives the full shared store dict and returns data that `exec()` will need. Keeping `prep()` and `exec()` separate is deliberate: `exec()` can be retried in isolation (if an API call fails, for example) without re-reading the store, because all inputs were captured by `prep()`. `post(shared, prep_res, exec_res)` is where you write results *back* to the shared store and decide which path to take next by returning an action string.

> ⚠️ **Note:** The action string returned by `post()` must match one of the declared actions in the **Object Inspector**. If `post()` returns `"default"` but the node's Actions field contains only `"yes"` and `"no"`, the runner will raise an error at runtime. Keep the Actions field and your `post()` return values in sync.

**Step 8: Validate and run**

Press **Ctrl+Shift+V** to validate. Then press **F5** to run. Watch the **Run Log tab** for the execution trace. After the flow completes, click the **Shared Store tab** at the bottom. You should see:

```
message: "Hello from PocketFlow Creator! The shared store is working."
```

This confirms that BasicGreeter's `post()` method successfully wrote to the shared store, and the value is now available for any downstream node that reads `shared["message"]`.

**Step 9: Experiment with reading from the shared store**

To see data flow in action, update `BasicGreeter.prep()` to read a value that was placed in the store by the Start Node. In real flows, the Start Node's `post()` is the natural place to seed initial values. For now, edit the Start Node's generated code — select the Start Node, open the **Python editor tab**, and add:

```python
def post(self, shared, prep_res, exec_res):
    shared["name"] = "PocketFlow learner"
    return "default"
```

Then update `BasicGreeter`:

```python
def prep(self, shared):
    # Read the name placed by the Start Node.
    return shared.get("name", "World")

def exec(self, prep_res):
    # prep_res is the name string.
    return f"Hello, {prep_res}! Welcome to PocketFlow."

def post(self, shared, prep_res, exec_res):
    shared["message"] = exec_res
    return "default"
```

Run again. The **Shared Store tab** will now show:

```
name: "PocketFlow learner"
message: "Hello, PocketFlow learner! Welcome to PocketFlow."
```

### What you learned

- The Basic Node has three lifecycle methods: `prep()`, `exec()`, and `post()`
- `prep()` reads from the shared store; `exec()` does the work; `post()` writes results and returns the next action
- The **Output Key** field in the inspector documents which shared store key this node writes to
- The **Shared Store tab** shows all key/value pairs after a flow run
- `post()` must return an action string that matches one of the node's declared actions
- The Start Node's `post()` is the natural place to seed the shared store with initial values

---

[↑ Series Index](gtkn_index.md)  
[↑ Tutorials Index](index.md)  
[→ Next Part: I/O and Tool Nodes](gtkn_part2.md)
