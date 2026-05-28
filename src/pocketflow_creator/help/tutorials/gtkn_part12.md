# Part 12 — Code Execution Nodes

This part covers three nodes that form a complete code-generation and testing pipeline:
generating code from a specification, executing it in an isolated environment, and
generating unit tests for the result.

**Prerequisite:** Complete Part 4 (LLM Nodes) — these nodes all call an LLM internally.

---

## Tutorial T-N41: Code Gen Node

### What it does

The **Code Gen Node** sends a natural-language specification to an LLM and returns a
code string in the requested language. The prompt template includes the language,
coding style, and any existing type signatures or context from the shared store.

### Use cases

- Generating utility functions from docstrings during a code-assist flow
- Auto-generating SQL, JSON Schema, or Jinja2 templates from plain descriptions
- Prototyping algorithm implementations to benchmark before hand-tuning

### What you'll build

A flow — **Start → CodeWriter → Stop** — that generates a Python function
`add_numbers(a, b)` from a one-line description.

### Step-by-step

**Step 1: Create project `gtkn_part12`.**

**Step 2: Drag a Code Gen Node** named `CodeWriter`.

**Step 3: Set Inspector properties:**

| Property | Value |
|---|---|
| `spec_key` | `code_spec` |
| `output_key` | `generated_code` |
| `language` | `python` |
| `model` | _(leave empty — uses mock provider)_ |

**Step 4: Wire Start → CodeWriter → Stop.**

**Step 5: Paste the code:**

```python
from pocketflow import Node

class CodeWriter(Node):
    def prep(self, shared):
        return shared.get(
            "code_spec",
            "Write a Python function add_numbers(a, b) that returns a + b.",
        )

    def exec(self, prep_res):
        # Production: call an LLM with the spec.
        # Simulation: generate deterministic code for this spec.
        spec = prep_res
        if "add_numbers" in spec:
            return (
                "def add_numbers(a, b):\n"
                '    """Return the sum of a and b."""\n'
                "    return a + b\n"
            )
        return "# Code generation placeholder\ndef generated_function():\n    pass\n"

    def post(self, shared, prep_res, exec_res):
        shared["generated_code"] = exec_res
        return "default"
```

**Step 6: Run and inspect `generated_code`:**

```python
def add_numbers(a, b):
    """Return the sum of a and b."""
    return a + b
```

### What you learned

- Code Gen Nodes decouple the specification (shared store) from the generation call
- `language` constrains the LLM to the correct syntax — also works for JavaScript, SQL, Bash, etc.
- The generated string is stored raw; a downstream Code Exec Node can run it, or a Test Gen Node can write tests for it

---

## Tutorial T-N42: Code Exec Node

### What it does

The **Code Exec Node** executes a Python code string in a subprocess sandbox and
captures `stdout`, `stderr`, the exit code, and a timeout flag. The output is stored
in the shared store for inspection or downstream decision-making.

### Use cases

- Running LLM-generated code to verify it works before committing
- Evaluating mathematical expressions inside a flow
- Executing data transformation scripts produced by an AI coding assistant

### What you'll build

Extend the flow from T-N41: add a Code Exec Node that runs the generated
`add_numbers` function and checks the output.

### Step-by-step

**Step 1: Add a Code Exec Node** named `CodeRunner` after `CodeWriter`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `code_key` | `generated_code` |
| `output_key` | `exec_result` |
| `timeout` | `5` |
| `sandbox` | `subprocess` |

**Step 3: Re-wire: CodeWriter → CodeRunner → Stop.**

**Step 4: Paste the code:**

```python
import subprocess
import textwrap
from pocketflow import Node

class CodeRunner(Node):
    TIMEOUT = 5

    def prep(self, shared):
        base_code = shared.get("generated_code", "")
        # Append a small harness to actually call the function.
        harness = "\nprint(add_numbers(3, 4))\n"
        return base_code + harness

    def exec(self, prep_res):
        try:
            result = subprocess.run(
                ["python", "-c", prep_res],
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT,
            )
            return {
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Timeout", "exit_code": -1, "timed_out": True}

    def post(self, shared, prep_res, exec_res):
        shared["exec_result"] = exec_res
        return "default"
```

**Step 5: Run.** `exec_result` will contain:

```
{"stdout": "7", "stderr": "", "exit_code": 0, "timed_out": false}
```

### What you learned

- Code Exec Nodes always run in an isolated subprocess — they cannot directly access the flow's Python process
- `timeout` prevents runaway code from blocking the flow indefinitely
- Check `exit_code == 0` and `stderr == ""` in a downstream Router Node to gate success/failure paths

---

## Tutorial T-N43: Test Gen Node

### What it does

The **Test Gen Node** takes a code string and generates a `pytest`-compatible test
module for it. The model analyses the function signatures and docstrings and writes
test cases covering normal inputs, edge cases, and error conditions.

### Use cases

- Automatically writing regression tests for LLM-generated code before deploying it
- Bootstrapping a test suite for legacy code with no existing tests
- Generating property-based test skeletons that a developer can then fill in

### What you'll build

Complete the pipeline from T-N41/T-N42: add a Test Gen Node that writes tests for
`add_numbers` and stores them as a test file.

### Step-by-step

**Step 1: Add a Test Gen Node** named `TestWriter` after `CodeRunner`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `code_key` | `generated_code` |
| `output_key` | `generated_tests` |
| `framework` | `pytest` |
| `model` | _(leave empty — uses mock provider)_ |

**Step 3: Wire CodeRunner → TestWriter → Stop.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

class TestWriter(Node):
    def prep(self, shared):
        return shared.get("generated_code", "")

    def exec(self, prep_res):
        code = prep_res
        # Production: send code to an LLM to generate tests.
        # Simulation: pattern-match function names and generate tests.
        if "add_numbers" in code:
            return (
                "import pytest\n"
                "from generated_code import add_numbers\n\n"
                "def test_add_positive():\n"
                "    assert add_numbers(3, 4) == 7\n\n"
                "def test_add_negative():\n"
                "    assert add_numbers(-1, -2) == -3\n\n"
                "def test_add_zero():\n"
                "    assert add_numbers(0, 5) == 5\n"
            )
        return "# No tests generated\n"

    def post(self, shared, prep_res, exec_res):
        shared["generated_tests"] = exec_res
        # Optionally write the tests to disk.
        with open("test_generated.py", "w") as f:
            f.write(exec_res)
        return "default"
```

**Step 5: Run.** `generated_tests` holds a ready-to-run pytest file, and
`test_generated.py` is written to disk.

**Step 6: In the terminal, run** `pytest test_generated.py -v` to confirm all three
generated tests pass.

### What you learned

- The full code-assistance pipeline is: **CodeWriter → CodeRunner → TestWriter**
- Test Gen Nodes produce pytest-compatible files you can run immediately
- Feed `exec_result.stdout` back into the LLM as context if code fails, to trigger a fix-and-retry loop

---

[↑ Series Index](gtkn_index.md)
[← Part 11](gtkn_part11.md)
[→ Part 13: Data Processing Nodes](gtkn_part13.md)
