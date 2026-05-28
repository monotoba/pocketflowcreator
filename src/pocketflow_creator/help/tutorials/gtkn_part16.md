# Part 16 — System, Shell, and Hardware Nodes

This part covers three nodes that interact directly with the host operating system and
hardware: running shell commands, communicating over a serial port, and reading or
writing spreadsheet files.

**Prerequisite:** Complete Part 1 (Start / Stop / Basic) before this part. A Linux,
macOS, or Windows host is required for live testing; all examples work with the
simulated runner for the tutorial exercises.

---

## Tutorial T-N65: Shell Command Node

### What it does

The **Shell Command Node** runs a shell command in a subprocess and captures `stdout`,
`stderr`, and the exit code. The shell is configurable: `bash`, `sh`, `zsh`, `powershell`,
`cmd`, or `auto` (which selects `bash` on Linux, `zsh` on macOS, and `powershell` on
Windows). The command string may include `{{key}}` placeholders that are expanded
from the shared store before execution.

### Use cases

- Running build scripts, linters, or test runners as part of a CI flow
- Executing system commands (e.g. `git status`, `df -h`) and feeding the output to an LLM
- Automating repetitive OS tasks from within a visual flow

### What you'll build

A flow — **Start → DiskInspector → Stop** — that runs `df -h /` (or the
equivalent on Windows) and stores the output in `disk_usage`.

### Step-by-step

**Step 1: Create project `gtkn_part16`.**

**Step 2: Drag a Shell Command Node** named `DiskInspector`.

**Step 3: Set Inspector properties:**

| Property | Value |
|---|---|
| `command_key` | `shell_command` |
| `shell` | `auto` |
| `timeout` | `10` |
| `stdout_key` | `disk_usage` |
| `stderr_key` | `shell_error` |

**Step 4: Wire Start → DiskInspector → Stop.**

**Step 5: Paste the code:**

```python
import subprocess
import sys
from pocketflow import Node

class DiskInspector(Node):
    TIMEOUT = 10

    def prep(self, shared):
        # Choose the right command for the platform.
        if sys.platform.startswith("win"):
            cmd = "Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free"
            shell_exe = "powershell"
        elif sys.platform == "darwin":
            cmd = "df -h /"
            shell_exe = "zsh"
        else:
            cmd = "df -h /"
            shell_exe = "bash"
        shared.setdefault("shell_command", cmd)
        return {"command": shared["shell_command"], "shell": shell_exe}

    def exec(self, prep_res):
        cmd = prep_res["command"]
        shell = prep_res["shell"]
        try:
            result = subprocess.run(
                [shell, "-c", cmd] if shell != "powershell" else ["powershell", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT,
            )
            return {
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Timeout", "exit_code": -1}

    def post(self, shared, prep_res, exec_res):
        shared["disk_usage"] = exec_res["stdout"]
        shared["shell_error"] = exec_res["stderr"]
        shared["shell_exit_code"] = exec_res["exit_code"]
        return "default"
```

**Step 6: Run.** `disk_usage` will contain the output of `df -h /` on your system.

**Step 7: Add a Condition Node** after `DiskInspector` that routes to `Stop_Error` when
`shell_exit_code != 0`.

### What you learned

- Shell Command Nodes abstract cross-platform differences via the `shell` property
- `auto` detection makes flows portable across Linux, macOS, and Windows with no code change
- Always wire an error path — non-zero exit codes should trigger a different branch

---

## Tutorial T-N66: TTY Serial Node

### What it does

The **TTY Serial Node** communicates with devices connected over a serial (UART) port —
Arduino microcontrollers, Raspberry Pi GPIO, GPS modules, industrial PLCs, and other
MCU-based hardware. Operations include `open`, `close`, `read`, `readline`, and
`write`. The open port object is stored in the shared store so multiple nodes can
reuse it.

### Use cases

- Reading sensor data (temperature, humidity, distance) from an Arduino over USB serial
- Sending commands to a motor controller or relay board
- Logging MCU telemetry into a flow for LLM analysis

### What you'll build

A flow that opens a serial port, reads one line of sensor data, and stores the parsed
reading.

### Step-by-step

**Step 1: Add three nodes:** `PortOpener` (TTY Serial, `open`), `SensorReader` (TTY
Serial, `readline`), and `PortCloser` (TTY Serial, `close`).

**Step 2: Set Inspector properties:**

For `PortOpener`:

| Property | Value |
|---|---|
| `operation` | `open` |
| `port_key` | `serial_port_obj` |
| `baud_rate` | `9600` |
| `encoding` | `utf-8` |

Set `port` to `/dev/ttyUSB0` (Linux) or `COM3` (Windows) in the Inspector's
`port` field.

**Step 3: Wire: Start → PortOpener → SensorReader → PortCloser → Stop.**

**Step 4: Paste the code:**

```python
# PortOpener
from pocketflow import Node

class PortOpener(Node):
    PORT = "/dev/ttyUSB0"
    BAUD = 9600

    def prep(self, shared):
        return {"port": self.PORT, "baud": self.BAUD}

    def exec(self, prep_res):
        # Production: import serial; return serial.Serial(port, baud, timeout=1)
        # Simulation: return a mock object
        class MockSerial:
            def readline(self):
                return b"T=23.4,H=61.2,D=42\n"
            def write(self, data):
                pass
            def close(self):
                pass
        return MockSerial()

    def post(self, shared, prep_res, exec_res):
        shared["serial_port_obj"] = exec_res
        return "default"
```

```python
# SensorReader
from pocketflow import Node

class SensorReader(Node):
    def prep(self, shared):
        return shared.get("serial_port_obj")

    def exec(self, prep_res):
        port = prep_res
        if port is None:
            return {}
        raw = port.readline().decode("utf-8").strip()
        # Parse "T=23.4,H=61.2,D=42"
        parts = {}
        for item in raw.split(","):
            if "=" in item:
                k, v = item.split("=", 1)
                parts[k] = float(v)
        return parts

    def post(self, shared, prep_res, exec_res):
        shared["sensor_reading"] = exec_res
        return "default"
```

```python
# PortCloser
from pocketflow import Node

class PortCloser(Node):
    def prep(self, shared):
        return shared.get("serial_port_obj")

    def exec(self, prep_res):
        if prep_res is not None:
            prep_res.close()
        return "closed"

    def post(self, shared, prep_res, exec_res):
        shared.pop("serial_port_obj", None)
        return "default"
```

**Step 5: Run.** `sensor_reading` will contain:

```
{"T": 23.4, "H": 61.2, "D": 42.0}
```

### What you learned

- Open/Read/Close is the standard three-node pattern for serial communication
- The port object lives in the shared store — any node in the flow can write to it
- `encoding: bytes` skips decoding for binary protocols; `encoding: utf-8` or `ascii` for text

---

## Tutorial T-N67: Spreadsheet Node

### What it does

The **Spreadsheet Node** reads from or writes to CSV, TSV, and Excel files. The
`format` property accepts `auto` (detect from file extension), `csv`, `tsv`, or
`excel`. Additional properties control the delimiter, quoting style, header row,
sheet name (for Excel), and encoding.

### Use cases

- Loading a customer list from CSV for batch processing
- Writing LLM-generated reports to Excel for stakeholder review
- Converting between CSV and TSV formats as part of a data-pipeline flow

### What you'll build

A flow that reads a CSV of product records, filters rows with a Map Node, and writes
the filtered rows to a new CSV.

### Step-by-step

**Step 1: Add two Spreadsheet Nodes:** `CSVReader` (operation `read`) and
`CSVWriter` (operation `write`).

**Step 2: Configure `CSVReader`:**

| Property | Value |
|---|---|
| `operation` | `read` |
| `file_key` | `input_csv` |
| `output_key` | `csv_rows` |
| `format` | `auto` |
| `has_header` | `true` |
| `encoding` | `utf-8` |

**Step 3: Configure `CSVWriter`:**

| Property | Value |
|---|---|
| `operation` | `write` |
| `file_key` | `output_csv` |
| `input_key` | `filtered_rows` |
| `format` | `csv` |
| `has_header` | `true` |
| `quoting` | `minimal` |

**Step 4: Wire: Start → CSVReader → FilterMapper → CSVWriter → Stop.**
(`FilterMapper` is a Map Node from Part 13.)

**Step 5: Paste the code:**

```python
# CSVReader
import csv, io
from pocketflow import Node

SAMPLE_CSV = (
    "name,price,in_stock\n"
    "Widget,9.99,true\n"
    "Gadget,24.99,false\n"
    "Thingamajig,4.50,true\n"
)

class CSVReader(Node):
    def prep(self, shared):
        return shared.get("input_csv", None)

    def exec(self, prep_res):
        # Production: open(prep_res, encoding="utf-8")
        # Simulation: use embedded string
        reader = csv.DictReader(io.StringIO(SAMPLE_CSV))
        return list(reader)

    def post(self, shared, prep_res, exec_res):
        shared["csv_rows"] = exec_res
        return "default"
```

```python
# FilterMapper — keep only in-stock items
from pocketflow import Node

class FilterMapper(Node):
    def prep(self, shared):
        return shared.get("csv_rows", [])

    def exec(self, prep_res):
        return [row for row in prep_res if row.get("in_stock") == "true"]

    def post(self, shared, prep_res, exec_res):
        shared["filtered_rows"] = exec_res
        return "default"
```

```python
# CSVWriter
import csv, io
from pocketflow import Node

class CSVWriter(Node):
    def prep(self, shared):
        return {
            "rows": shared.get("filtered_rows", []),
            "path": shared.get("output_csv", "output.csv"),
        }

    def exec(self, prep_res):
        rows = prep_res["rows"]
        path = prep_res["path"]
        if not rows:
            return path
        fieldnames = list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def post(self, shared, prep_res, exec_res):
        shared["output_csv_path"] = exec_res
        return "default"
```

**Step 6: Run.** `output.csv` is written with only the two in-stock rows.

### What you learned

- Spreadsheet Nodes abstract the CSV/TSV/Excel difference — the rest of your flow sees a uniform list of dicts
- `has_header: true` means the first row becomes dict keys; `false` returns rows as lists
- Chain CSVReader → Map/Filter Nodes → CSVWriter for a lightweight data-transformation pipeline

---

[↑ Series Index](gtkn_index.md)
[← Part 15](gtkn_part15.md)
[→ Part 17: Networking Nodes](gtkn_part17.md)
