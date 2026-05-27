# Part 2 — I/O and Tool Nodes: File Reader, File Writer, Python Tool

Part 1 established the three foundation nodes every flow needs. Part 2 introduces the three nodes that connect your flow to the outside world: **File Reader Node** reads files from disk, **File Writer Node** writes files to disk, and **Python Tool Node** calls a registered Python function. Together these three nodes turn an isolated computation graph into a practical data-processing pipeline that can ingest real inputs and produce persistent outputs.

Complete Part 1 before starting here — you will need confidence with the Basic Node's `prep/exec/post` pattern since the I/O nodes follow the same lifecycle.

---

## Tutorial T-N4: The File Reader Node

### What it does

The **File Reader Node** reads a file from the local filesystem and stores its contents as a string in the shared store. Its `exec()` method opens the file at the path configured in the `file_path` property and returns the file contents; its `post()` stores the contents under `output_key` in the shared store. This is the standard way to load text documents, configuration files, or any other disk-based input into a PocketFlow pipeline.

### Use cases

- Loading a text document for summarisation or analysis by a downstream LLM node
- Reading a configuration file that controls how the rest of the flow behaves
- Ingesting CSV or JSON data that will be parsed and processed by subsequent nodes
- Loading a prompt template from a `.md` file to be filled in later

### What you'll build

A four-node flow — **Start → FileReader → BasicPrinter → Stop** — where `FileReader` reads `input.txt` into `shared["content"]` and `BasicPrinter` logs that content to the **Run Log tab**.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part2_filereader`. Once the blank canvas opens, also create the input file you will read. In the **Project Explorer**, right-click the project root folder and choose **New File**. Name the file `input.txt` and type a few lines of sample text, for example:

```
Line 1: The quick brown fox jumps over the lazy dog.
Line 2: PocketFlow makes LLM pipelines visual and composable.
Line 3: This file was loaded by the File Reader Node.
```

Save the file with **Ctrl+S**.

> 💡 **Tip:** PocketFlow projects store files relative to the project root. When you set `file_path` to `input.txt` the runner looks for that file in the same folder as your project's `.pfcgraph.yaml`. For files in subdirectories, use forward-slash paths like `data/input.txt`.

**Step 2: Build the canvas**

Drag the following nodes onto the canvas and arrange them left to right:

1. **Start Node** — from the **Component Palette**, Flow Control category
2. **File Reader Node** — from the **Component Palette**, I/O category
3. **Basic Node** (rename to `BasicPrinter`) — from Core
4. **Stop Node** — from Flow Control

Wire them: Start →(default)→ FileReader →(default)→ BasicPrinter →(default)→ Stop.

**Step 3: Configure the File Reader Node**

Click the **File Reader Node** on the canvas to select it. In the **Object Inspector** you will see two key properties:

- **file_path**: Set this to `input.txt` (the filename relative to the project root).
- **output_key**: Set this to `content`. This is the shared store key under which the file contents will be stored.

These two properties are all you need to configure. The File Reader Node handles opening the file, reading it, and writing the result to the store — no custom code required.

**Step 4: Configure BasicPrinter to log the content**

Select the **BasicPrinter** node and open the **Python editor tab**. The File Reader Node already wrote the file contents to `shared["content"]`, so BasicPrinter just needs to read and print it:

```python
from pocketflow import Node

class BasicPrinter(Node):
    """Reads shared['content'] and logs it to the run log."""

    def prep(self, shared):
        # Pull the file content the File Reader Node stored.
        return shared.get("content", "(no content found)")

    def exec(self, prep_res):
        # Print the content. In PocketFlow, print() output
        # appears in the Run Log tab during execution.
        print("=== File Contents ===")
        print(prep_res)
        print("=== End of File ===")
        return prep_res

    def post(self, shared, prep_res, exec_res):
        # We are just logging, so no new store key is needed.
        # Return "default" to continue to the Stop node.
        return "default"
```

Save with **Ctrl+S**.

**Step 5: Validate and run**

Press **Ctrl+Shift+V**. If `input.txt` is missing, the validator may warn you — ensure the file exists in the project folder. Press **F5** to run. Switch to the **Run Log tab** and verify that the three lines from `input.txt` appear between the `=== File Contents ===` banners.

> ⚠️ **Note:** If the File Reader Node cannot find the file, it raises a `FileNotFoundError` at runtime and the flow aborts. Always validate that the `file_path` property points to a file that actually exists before running in production. Use absolute paths for files that live outside the project folder.

**Step 6: Inspect the shared store**

Switch to the **Shared Store tab** after the run. You should see:

```
content: "Line 1: The quick brown fox...\nLine 2: PocketFlow...\nLine 3: ..."
```

The full file contents are a single string, with newlines represented as `\n`. Downstream nodes can split, parse, or pass this string to an LLM node as-is.

### What you learned

- The File Reader Node reads a file and stores it in the shared store under `output_key`
- `file_path` is relative to the project root by default
- No custom code is needed — just set `file_path` and `output_key` in the inspector
- The **Shared Store tab** shows the file contents as a string after the run
- `FileNotFoundError` is the most common runtime failure — validate the path first

---

## Tutorial T-N5: The File Writer Node

### What it does

The **File Writer Node** is the counterpart of the File Reader Node. It reads a value from the shared store under `input_key` and writes it to a file on disk at the path specified by `file_path`. If the file already exists it is overwritten; if intermediate directories do not exist, the node creates them. Like the File Reader Node, it requires no custom code — all behaviour is configured through the **Object Inspector**.

### Use cases

- Saving LLM output or summarised text to a file for later use
- Writing transformed or cleaned data to a new file as part of a batch pipeline
- Persisting flow results so that a subsequent flow run or external tool can pick them up
- Generating output files (reports, logs, YAML configs) from structured flow data

### What you'll build

You will extend the T-N4 flow by adding a **Transform** node that uppercases the file content, then a **File Writer Node** that saves the result to `output.txt`. The complete flow is: **Start → FileReader → Transform → FileWriter → Stop**.

### Step-by-step

**Step 1: Open or recreate the T-N4 project**

Open the `gtkn_part2_filereader` project. You should see the Start → FileReader → BasicPrinter → Stop canvas from T-N4. You will modify this flow, so delete the BasicPrinter node (select it, press **Delete**) and also delete both edges that connected to it. You should now have Start → FileReader (unconnected) and a floating Stop Node.

**Step 2: Add a Transform node**

Drag a **Basic Node** from the **Component Palette** onto the canvas between the File Reader Node and the Stop Node. Rename it `Transform` in the **Object Inspector**.

**Step 3: Add a File Writer Node**

Drag a **File Writer Node** from the **Component Palette** (I/O category) onto the canvas to the right of the Transform node, and to the left of the Stop Node. Your left-to-right order should be: Start → FileReader → Transform → FileWriter → Stop.

**Step 4: Wire the flow**

Connect the nodes in order:

1. Start →(default)→ FileReader
2. FileReader →(default)→ Transform
3. Transform →(default)→ FileWriter
4. FileWriter →(default)→ Stop

**Step 5: Configure the File Writer Node**

Click the **File Writer Node** to select it. In the **Object Inspector**:

- **input_key**: Set to `result`. This is the shared store key whose value will be written to the file. The Transform node (which you will code in the next step) stores the uppercased content under `shared["result"]`.
- **file_path**: Set to `output.txt`. This file will be created in the project root when the flow runs.

> 💡 **Tip:** You can write to subdirectories by including the path in `file_path`, for example `output/processed.txt`. PocketFlow Creator will create the `output/` directory automatically if it does not exist.

**Step 6: Write the Transform node code**

Select the **Transform** node and open the **Python editor tab**. The Transform node reads `shared["content"]` (written by the File Reader), converts it to uppercase, and stores it in `shared["result"]` for the File Writer to pick up:

```python
from pocketflow import Node

class Transform(Node):
    """Uppercases the file content and stores it as shared['result']."""

    def prep(self, shared):
        # Read the content the File Reader loaded.
        # Use .get() with a fallback so the node does not crash
        # if content is missing (e.g. during isolated testing).
        return shared.get("content", "")

    def exec(self, prep_res):
        # Transform: convert the entire text to uppercase.
        # You could replace this with any text transformation:
        # JSON parsing, CSV splitting, regex extraction, etc.
        return prep_res.upper()

    def post(self, shared, prep_res, exec_res):
        # Store the transformed text under "result" so the
        # File Writer Node can find it via its input_key property.
        shared["result"] = exec_res
        return "default"
```

Save with **Ctrl+S**.

**Step 7: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. After the flow completes:

1. Check the **Shared Store tab** — you should see both `content` (original) and `result` (uppercased).
2. Open the **Project Explorer** and look for `output.txt` in the project root. Double-click it to open it in the editor — it should contain the uppercased text.

> ⚠️ **Note:** The File Writer Node overwrites the destination file every time the flow runs. If you need to append rather than overwrite, use a Basic Node with a custom `exec()` that opens the file in append mode (`open(path, "a")`). The File Writer Node is deliberately simple — it covers the most common case of writing the final result of a flow.

**Step 8: Review the data flow**

Trace the data through the flow: `input.txt` → File Reader writes to `shared["content"]` → Transform reads `shared["content"]`, writes `shared["result"]` → File Writer reads `shared["result"]`, writes `output.txt`. This is the canonical PocketFlow data-flow pattern: each node reads a named key from the shared store and writes a named key, creating a clear chain of custody for the data.

### What you learned

- The File Writer Node reads from `input_key` and writes to `file_path`
- `file_path` can include subdirectories, which are created automatically
- The shared store creates a clean handoff chain: each node reads what the previous wrote
- The File Writer Node always overwrites; for append behaviour, use a Basic Node
- After a run, output files appear in the **Project Explorer** immediately

---

## Tutorial T-N6: The Python Tool Node

### What it does

The **Python Tool Node** calls a registered Python function decorated with `@tool` and stores the result in the shared store. Rather than encoding utility logic directly in a node's `exec()` method, the `@tool` pattern lets you write reusable functions in a separate `tools/` file and call them by name from any Python Tool Node in any graph. This promotes code reuse and keeps your node code focused on orchestration rather than implementation.

### Use cases

- Calling a reusable utility function (string processing, data parsing, math, formatting) from multiple nodes or flows
- Integrating a third-party library function without writing a full Basic Node
- Exposing domain-specific functions to the flow layer as named tools
- Building a library of tested helper functions that Agent Nodes can also call

### What you'll build

A three-node flow — **Start → ToolCaller → Stop** — where `ToolCaller` is a Python Tool Node that calls a `word_count` tool function. The function counts the words in `shared["text"]` and stores the count in `shared["count"]`.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part2_tool`. A blank canvas opens.

**Step 2: Create the tools file**

In the **Project Explorer**, right-click the project root and choose **New File**. Name the file `tools.py`. This is the conventional location for `@tool`-decorated functions. Open it in the editor and write the `word_count` tool:

```python
from pocketflow import tool

@tool
def word_count(text: str) -> int:
    """Count the number of words in a text string.

    Args:
        text: The input text to count words in.

    Returns:
        The number of whitespace-delimited words.
    """
    if not text or not text.strip():
        return 0
    return len(text.split())
```

Save with **Ctrl+S**. The `@tool` decorator registers `word_count` in the Tool Registry under the name `"word_count"`. The Tool Registry is a global dictionary that PocketFlow populates by importing all `tools.py` files it finds in the project. The Python Tool Node looks up functions in this registry by name at runtime.

> 💡 **Tip:** You can have multiple `@tool` functions in a single `tools.py` file, and you can have multiple `tools.py` files in subdirectories — PocketFlow discovers them all. Give your tool functions clear, specific names because the name you use here is what you type into the **tool_name** property in the inspector.

**Step 3: Build the canvas**

Drag onto the canvas and wire in order:

1. **Start Node**
2. **Python Tool Node** — from the **Component Palette**, Tools category
3. **Stop Node**

Wire: Start →(default)→ ToolCaller →(default)→ Stop.

**Step 4: Rename the Python Tool Node**

Select the Python Tool Node and set its **Title** to `ToolCaller` in the **Object Inspector**.

**Step 5: Configure the Python Tool Node properties**

With `ToolCaller` selected, set the following properties in the **Object Inspector**:

- **tool_name**: `word_count` — the exact name of the `@tool`-decorated function
- **input_key**: `text` — the shared store key whose value will be passed to the function
- **output_key**: `count` — the shared store key where the function's return value is stored

These three properties are the complete configuration. The Python Tool Node's generated code looks up `shared[input_key]`, calls `registry[tool_name](value)`, and stores the result in `shared[output_key]`. You do not need to write any custom node code.

> ⚠️ **Note:** The **tool_name** must match the function name *exactly*, including capitalisation. If the function is decorated with `@tool` but the registry cannot find it at runtime (because the `tools.py` file is in an unexpected location or has a syntax error), the node raises a `KeyError`. Check the **Run Log tab** for the full traceback.

**Step 6: Seed the shared store with test text**

The Python Tool Node will read `shared["text"]`, but nothing in this simple flow writes `"text"` to the store before `ToolCaller` runs. Use the Start Node to seed it. Select the Start Node, open the **Python editor tab**, and write:

```python
from pocketflow import Node

class StartNode(Node):

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # Seed the shared store with the text to count.
        shared["text"] = (
            "The quick brown fox jumps over the lazy dog. "
            "PocketFlow makes building LLM pipelines visual and fun."
        )
        return "default"
```

Save with **Ctrl+S**.

**Step 7: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. After the flow completes, open the **Shared Store tab**. You should see:

```
text: "The quick brown fox jumps over the lazy dog. ..."
count: 22
```

The `word_count` function correctly counted the words in `shared["text"]` and stored the integer result in `shared["count"]`.

**Step 8: Understand the Tool Registry pattern**

The `@tool` decorator is not only used by Python Tool Nodes — it is also the mechanism by which **Agent Nodes** (covered in Part 6) discover which functions they can call autonomously. By writing your utilities as `@tool` functions you make them available to both explicit Python Tool Node calls and autonomous Agent decision-making, with zero additional configuration. This makes the `@tool` pattern a powerful architectural choice for any function that might need to be invoked from multiple places in a pipeline.

### What you learned

- The Python Tool Node calls a registered `@tool` function by name and stores the result
- `@tool` functions are written in `tools.py` files and discovered automatically
- The three inspector properties — `tool_name`, `input_key`, `output_key` — are all the configuration needed
- `@tool` functions are also usable by Agent Nodes, making them a reusable building block
- `tool_name` must match the function name exactly, including capitalisation

---

[← Previous Part: Foundation Nodes](gtkn_part1.md)  
[→ Next Part: Flow Control and Human Interaction](gtkn_part3.md)  
[↑ Series Index](gtkn_index.md)  
[↑ Tutorials Index](index.md)
