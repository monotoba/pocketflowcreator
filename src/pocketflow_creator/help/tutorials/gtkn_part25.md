# Part 25 — Wind Energy, Scientific Computing, and Data Catalog Addon Nodes

Part 25 covers the final five addon nodes: **OpenFAST**, **KiteFAST**, **MATLAB Engine**, **Octave Script**, and **USGS Data Catalog Search**. The wind energy nodes (OpenFAST, KiteFAST) wrap NREL's aero-elastic simulation tools. The scientific computing nodes (MATLAB Engine, Octave Script) integrate the two leading numerical computing environments — one commercial, one open-source — into PocketFlow pipelines. The data catalog node (USGS Data Catalog Search) enables dataset discovery across the USGS ScienceBase repository.

This is the final part of the Addon Nodes series. By completing it you will have worked through all 34 addon node types.

---

## Tutorial T-N113: The OpenFAST Node

### What it does

The **OpenFAST Node** runs an NREL OpenFAST aero-elastic wind turbine simulation. OpenFAST is the successor to FAST and is the reference simulation tool for wind turbine structural dynamics, aerodynamics, and control analysis developed at the US National Renewable Energy Laboratory (NREL). It reads a `.fst` primary input file that references module input files for aerodynamics (AeroDyn), structure (ElastoDyn), control (ServoDyn), and optionally waves (HydroDyn, MoorDyn). The node runs `openfast` in a subprocess, waits for completion, and returns a summary of key output channels (rotor power, thrust, blade loads).

### Use cases

- Computing power output and rotor loads for a turbine at a specific wind speed
- Generating a power curve by sweeping wind speed from cut-in to cut-out in a Batch Node loop
- Validating turbine controller settings by comparing simulated power with target values
- Assessing structural loads for fatigue lifetime estimation at an IEC design load case

### What you'll build

A four-node flow — **Start → Seed FST Path → OpenFAST → Log Performance → Stop** — that runs the NREL 5 MW reference turbine at 11 m/s wind speed (near rated power) and logs rotor power, thrust, and tip speed ratio.

### Step-by-step

**Step 1: Install OpenFAST**

Download pre-compiled binaries from https://github.com/OpenFAST/openfast/releases or compile from source. Confirm `openfast --version` (or `openfast.exe` on Windows) is on your PATH.

**Step 2: Obtain the NREL 5 MW reference turbine input files**

Clone or download the OpenFAST `r-test` repository:

```bash
git clone https://github.com/OpenFAST/r-test.git
```

Navigate to `r-test/glue-codes/openfast/5MW_Land_DLL_WTurb/`. Copy this entire directory into your project root as `5MW_turbine/`. It contains the complete set of `.fst`, `ElastoDyn.dat`, `AeroDyn.dat`, `ServoDyn.dat`, and inflow wind files needed to run OpenFAST.

**Step 3: Create a new project**

Name it `gtkn_part25_openfast`.

**Step 4: Build the canvas**

Place: **Start** → **SeedFSTPath** (Basic Node) → **OpenFAST** → **LogPerformance** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 5: Configure the OpenFAST Node**

In the **Object Inspector**:

- **fst_path_key**: `openfast_fst_path`
- **result_key**: `openfast_result`

**Step 6: Write SeedFSTPath**

```python
import os
from pocketflow import Node

class SeedFSTPath(Node):
    """Seeds the OpenFAST .fst input file path."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        # Path to the primary .fst file for the NREL 5 MW reference turbine
        shared["openfast_fst_path"] = os.path.join(
            project_dir, "5MW_turbine", "5MW_Land_DLL_WTurb.fst"
        )
        return "default"
```

**Step 7: Write LogPerformance**

```python
from pocketflow import Node

class LogPerformance(Node):
    """Logs the OpenFAST rotor performance summary."""

    def prep(self, shared):
        return shared.get("openfast_result", {})

    def exec(self, prep_res):
        r = prep_res
        print("=== OpenFAST Simulation Results — NREL 5 MW ===")
        print(f"  Run status      : {r.get('status', '?')}")
        print(f"  Sim duration    : {r.get('sim_time_s', '?')} s")
        print(f"  Elapsed (wall)  : {r.get('elapsed_wall_s', '?'):.1f} s")
        print()

        perf = r.get("performance_summary", {})
        if perf:
            power_mw    = perf.get("RtAeroCp_mean", None)
            power_kw    = perf.get("GenPwr_mean_kW", None)
            thrust_kn   = perf.get("RtAeroFxh_mean_kN", None)
            tsr         = perf.get("RtTSR_mean", None)
            rpm         = perf.get("RotSpeed_mean_rpm", None)

            print(f"  Mean Power      : {power_kw:.0f} kW" if isinstance(power_kw, float) else f"  Mean Power      : {power_kw}")
            print(f"  Mean Thrust     : {thrust_kn:.0f} kN" if isinstance(thrust_kn, float) else f"  Mean Thrust     : {thrust_kn}")
            print(f"  Mean Tip Speed  : {tsr:.2f} (TSR)" if isinstance(tsr, float) else f"  TSR             : {tsr}")
            print(f"  Rotor Speed     : {rpm:.2f} rpm" if isinstance(rpm, float) else f"  Rotor Speed     : {rpm}")
        else:
            print("  (No performance data — check Run Log for OpenFAST errors)")
        return r

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. OpenFAST simulates the turbine for the duration specified in the `.fst` file (typically 630 s including a 30-s start-up transient). Runtime is typically 2–5 minutes for a 600-second land-based turbine simulation. The Run Log shows OpenFAST stdout, and `LogPerformance` reports mean power (≈ 5,000 kW at rated wind speed), thrust, and rotor speed.

**Step 9: Build a power curve using a Batch Node**

To generate a power curve from 3–25 m/s:

1. In `SeedFSTPath`, write `shared["wind_speeds"] = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 25]`.
2. Wrap `SeedFSTPath → OpenFAST` in a **Batch Node** that iterates over `wind_speeds`.
3. Before each OpenFAST call, update the InflowWind input file's wind speed using a **Shell Command Node** or **Python Tool Node** with `sed` or `re.sub()`.
4. Collect `GenPwr_mean_kW` in a Reduce Node and write the power curve to a CSV.

### What you learned

- The OpenFAST Node runs NREL OpenFAST from a `.fst` primary input file
- The result dict contains `status`, `sim_time_s`, `elapsed_wall_s`, and `performance_summary`
- `performance_summary` includes mean power (`GenPwr_mean_kW`), thrust, TSR, and rotor speed
- Simulate a power curve by wrapping the node in a Batch Node and varying wind speed in the inflow file
- OpenFAST full-length runs take several minutes — use `TMax` in the `.fst` file to control run duration

---

## Tutorial T-N114: The KiteFAST Node

### What it does

The **KiteFAST Node** runs an NREL KiteFAST airborne-wind-energy (AWE) simulation. KiteFAST is an aero-elastic simulation code for crosswind airborne wind energy systems (kite turbines), built on the OpenFAST framework. It simulates kite flight dynamics, tether loads, and on-board power generation. The node runs the KiteFAST executable with a provided input file and returns summary results including mean tether tension, mean electrical power output, and flight cycle statistics.

### Use cases

- Evaluating tether tension and kite power output for a new AWE system design
- Comparing crosswind flight strategies (figure-eight vs circular) for power maximisation
- Assessing structural loads on kite airframe components for fatigue analysis
- Automating sensitivity studies over kite wing area and rated power using a Batch Node

### What you'll build

A four-node flow — **Start → Seed Input Path → KiteFAST → Log Results → Stop** — that runs a KiteFAST simulation using the bundled example inputs and logs mean tether tension and electrical power output.

### Step-by-step

**Step 1: Install KiteFAST**

KiteFAST source code is available at https://github.com/OpenFAST/KiteFAST. Clone the repository, build the `kitefast` executable following the build instructions, and place it on your PATH.

**Step 2: Obtain KiteFAST example inputs**

The KiteFAST repository contains example cases in `examples/`. Copy the `M600_Case01/` example directory into your project root as `kitefast_case/`. The primary input file is `kitefast_case/KiteFAST_M600.kfst`.

**Step 3: Create a new project**

Name it `gtkn_part25_kitefast`.

**Step 4: Build the canvas**

Place: **Start** → **SeedInputPath** (Basic Node) → **KiteFAST** → **LogResults** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 5: Configure the KiteFAST Node**

In the **Object Inspector**:

- **input_path_key**: `kitefast_input_path`
- **result_key**: `kitefast_result`

**Step 6: Write SeedInputPath**

```python
import os
from pocketflow import Node

class SeedInputPath(Node):
    """Seeds the KiteFAST primary input file path."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        shared["kitefast_input_path"] = os.path.join(
            project_dir, "kitefast_case", "KiteFAST_M600.kfst"
        )
        return "default"
```

**Step 7: Write LogResults**

```python
from pocketflow import Node

class LogResults(Node):
    """Logs KiteFAST simulation results."""

    def prep(self, shared):
        return shared.get("kitefast_result", {})

    def exec(self, prep_res):
        r = prep_res
        print("=== KiteFAST AWE Simulation Results ===")
        print(f"  Status              : {r.get('status', '?')}")
        print(f"  Sim duration        : {r.get('sim_time_s', '?')} s")
        print()

        summary = r.get("summary", {})
        if summary:
            tether_kn = summary.get("mean_tether_tension_kN", "?")
            power_kw  = summary.get("mean_electrical_power_kW", "?")
            cycles    = summary.get("flight_cycles", "?")
            alt_m     = summary.get("mean_altitude_m", "?")

            print(f"  Mean Tether Tension : {tether_kn:.1f} kN" if isinstance(tether_kn, float) else f"  Mean Tether Tension : {tether_kn}")
            print(f"  Mean Elec. Power    : {power_kw:.0f} kW" if isinstance(power_kw, float) else f"  Mean Elec. Power    : {power_kw}")
            print(f"  Flight Cycles       : {cycles}")
            print(f"  Mean Altitude       : {alt_m:.0f} m" if isinstance(alt_m, float) else f"  Mean Altitude       : {alt_m}")
        else:
            print("  (No summary data — check Run Log for KiteFAST errors)")
        return r

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. KiteFAST simulates multiple crosswind flight cycles. Runtime depends on the simulation duration and timestep. The Run Log streams KiteFAST output, and `LogResults` reports tether tension, electrical power, and cycle count.

### What you learned

- The KiteFAST Node runs NREL KiteFAST for airborne wind energy systems
- Supply the primary `.kfst` input file path; KiteFAST manages all referenced module files
- The result dict contains `status`, `sim_time_s`, and a `summary` dict with mean tether tension, power, and flight cycles
- Use with a Batch Node to sweep kite wing area, rated power, or wind speed for system sizing trade studies

---

## Tutorial T-N115: The MATLAB Engine Node

### What it does

The **MATLAB Engine Node** calls a MATLAB function or executes a MATLAB script via the `matlab.engine` Python interface. You pass the function name (or script path) and any positional arguments through the shared store; the node starts (or reuses) a MATLAB engine session, calls the function, and returns the specified output variables. This allows MATLAB code to participate in PocketFlow pipelines as first-class nodes, without requiring you to port MATLAB algorithms to Python.

### Use cases

- Calling a validated MATLAB analysis function that is too complex or expensive to rewrite in Python
- Running legacy MATLAB simulation code as part of a larger PocketFlow pipeline
- Accessing MATLAB toolboxes (Signal Processing, Control System, Optimization) from Python flows
- Rapid prototyping: develop the algorithm in MATLAB, then orchestrate multiple calls in PocketFlow

### What you'll build

A four-node flow — **Start → Seed MATLAB Call → MATLAB Engine → Log FFT Result → Stop** — that calls a MATLAB function to compute the FFT of a sine wave and returns the dominant frequency.

### Step-by-step

**Step 1: Install the MATLAB Engine for Python**

From your MATLAB installation directory, run:

```bash
cd /path/to/MATLAB/R2023b/extern/engines/python
python setup.py install
```

Verify: `python -c "import matlab.engine; print('OK')"`.

> ⚠️ **Note:** The MATLAB Engine for Python requires a licensed MATLAB installation on the same machine. MATLAB Runtime (MCR) alone is not sufficient — you need the full MATLAB application.

**Step 2: Create the MATLAB function**

Create `find_dominant_freq.m` in your project root:

```matlab
function dominant_freq = find_dominant_freq(signal, fs)
% FIND_DOMINANT_FREQ  Find the dominant frequency of a signal.
%   dominant_freq = find_dominant_freq(signal, fs)
%   signal : column vector of samples
%   fs     : sample rate in Hz
%   returns: dominant frequency in Hz

N = length(signal);
Y = fft(signal);
P2 = abs(Y / N);
P1 = P2(1:floor(N/2)+1);
P1(2:end-1) = 2*P1(2:end-1);
f = fs * (0:floor(N/2)) / N;
[~, idx] = max(P1);
dominant_freq = f(idx);
end
```

**Step 3: Create a new project**

Name it `gtkn_part25_matlab`.

**Step 4: Build the canvas**

Place: **Start** → **SeedMATLABCall** (Basic Node) → **MATLAB Engine** → **LogFFTResult** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 5: Configure the MATLAB Engine Node**

In the **Object Inspector**:

- **script_key**: `matlab_script`
- **args_key**: `matlab_args`
- **result_key**: `matlab_result`

**Step 6: Write SeedMATLABCall**

```python
import numpy as np
from pocketflow import Node

class SeedMATLABCall(Node):
    """Seeds the MATLAB function call and signal data."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # Generate a 440 Hz sine wave sampled at 8000 Hz for 1 second
        fs = 8000
        t  = np.linspace(0, 1.0, fs, endpoint=False)
        signal = np.sin(2 * np.pi * 440 * t) + 0.3 * np.sin(2 * np.pi * 1760 * t)

        # MATLAB function to call (must be on the MATLAB path)
        shared["matlab_script"] = "find_dominant_freq"
        # Arguments: pass signal as a column vector and sample rate
        shared["matlab_args"]   = [signal.tolist(), float(fs)]

        return "default"
```

**Step 7: Write LogFFTResult**

```python
from pocketflow import Node

class LogFFTResult(Node):
    """Logs the dominant frequency returned by MATLAB."""

    def prep(self, shared):
        return shared.get("matlab_result", {})

    def exec(self, prep_res):
        r = prep_res
        print("=== MATLAB Engine FFT Result ===")
        print(f"  Status           : {r.get('status', '?')}")
        print(f"  MATLAB version   : {r.get('matlab_version', '?')}")

        output = r.get("output", None)
        if output is not None:
            print(f"  Dominant freq    : {output:.1f} Hz")
            print(f"  (Expected: 440 Hz — the fundamental of our sine wave)")
        else:
            print("  No output returned — check Run Log")
        return r

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The MATLAB Engine Node starts a MATLAB session (takes 15–30 seconds on first call; subsequent calls reuse the session), calls `find_dominant_freq`, and returns the dominant frequency — expected to be 440 Hz (the strongest component of our synthesised signal). The Run Log shows the MATLAB engine startup and function call timing.

> 💡 **Tip:** Starting a MATLAB engine is expensive (15–30 s). In production pipelines with many MATLAB calls, use a single engine session that is started once at the beginning of the flow and reused across multiple MATLAB Engine Nodes by keeping the session object in the shared store.

### What you learned

- The MATLAB Engine Node uses `matlab.engine` to call MATLAB functions from Python
- Requires a licensed MATLAB installation (not just MCR) with the Python engine installed
- Supply `matlab_script` (function name) and `matlab_args` (list of positional arguments) via the shared store
- The result dict contains `output` (the function's first return value), `matlab_version`, and `status`
- Starting a MATLAB engine takes 15–30 seconds; plan for this in time-sensitive pipelines

---

## Tutorial T-N116: The Octave Script Node

### What it does

The **Octave Script Node** executes a GNU Octave script or inline Octave expression and returns workspace variable values. GNU Octave is a free, open-source numerical computing environment largely compatible with MATLAB syntax. The node invokes Octave in batch mode (`octave --no-gui --no-window-system`), runs the specified script or inline code, and captures the output of named variables. It requires no Python-side Octave interface — just the `octave` command on the PATH.

### Use cases

- Running MATLAB-compatible numerical code without a MATLAB licence
- Calling Octave for signal processing, linear algebra, or ODE solving in a PocketFlow pipeline
- Rapid prototyping of numerical algorithms in Octave before porting to Python or MATLAB
- Running existing `.m` script libraries that work under Octave compatibility

### What you'll build

A four-node flow — **Start → Seed Octave Code → Octave Script → Log ODE Result → Stop** — that solves the Lorenz attractor ODE system using Octave's `lsode` solver and returns the final state vector.

### Step-by-step

**Step 1: Install GNU Octave**

Download from https://octave.org/download or install via your package manager:

```bash
# Ubuntu/Debian
sudo apt-get install octave

# macOS (Homebrew)
brew install octave
```

Verify: `octave --version`.

**Step 2: Create a new project**

Name it `gtkn_part25_octave`.

**Step 3: Build the canvas**

Place: **Start** → **SeedOctaveCode** (Basic Node) → **Octave Script** → **LogODEResult** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 4: Configure the Octave Script Node**

In the **Object Inspector**:

- **script_path_key**: `octave_script_path` *(leave blank for inline code)*
- **inline_code_key**: `octave_code`
- **result_var**: `final_state`
- **result_key**: `octave_result`

**Step 5: Write SeedOctaveCode**

```python
from pocketflow import Node

class SeedOctaveCode(Node):
    """Seeds inline Octave code for the Lorenz attractor ODE."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # Lorenz attractor parameters and ODE
        octave_code = """
sigma = 10.0;
rho   = 28.0;
beta  = 8.0/3.0;

function dydt = lorenz(y, t)
  sigma = 10.0; rho = 28.0; beta = 8.0/3.0;
  dydt = [
    sigma * (y(2) - y(1));
    y(1) * (rho - y(3)) - y(2);
    y(1) * y(2) - beta * y(3)
  ];
end

t = linspace(0, 25, 5000);
y0 = [1.0; 0.0; 0.0];

y = lsode(@lorenz, y0, t);

% Extract final state for return
final_state = y(end, :);

printf('Lorenz attractor solved for t=0..25\\n');
printf('Final state: x=%.4f  y=%.4f  z=%.4f\\n', ...
       final_state(1), final_state(2), final_state(3));
"""
        shared["octave_code"]        = octave_code
        shared["octave_script_path"] = ""  # use inline code
        return "default"
```

**Step 6: Write LogODEResult**

```python
from pocketflow import Node

class LogODEResult(Node):
    """Logs the Lorenz attractor final state returned from Octave."""

    def prep(self, shared):
        return shared.get("octave_result", {})

    def exec(self, prep_res):
        r = prep_res
        print("=== Octave Lorenz Attractor ODE Result ===")
        print(f"  Status       : {r.get('status', '?')}")
        print(f"  Octave stdout:\n{r.get('stdout', '(none)')}")

        final_state = r.get("result_var_value", None)
        if final_state is not None:
            if isinstance(final_state, (list, tuple)) and len(final_state) == 3:
                print(f"\n  Final state at t=25:")
                print(f"    x = {final_state[0]:.4f}")
                print(f"    y = {final_state[1]:.4f}")
                print(f"    z = {final_state[2]:.4f}")
            else:
                print(f"\n  final_state = {final_state}")
        else:
            print("  (No result variable returned)")
        return r

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 7: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. Octave solves the Lorenz system over 5000 time steps (typically < 2 seconds). The Run Log shows Octave's stdout output (the `printf` lines from the script) and `LogODEResult` prints the final state vector — a chaotic trajectory in the Lorenz attractor's butterfly-shaped basin.

**Step 8: Use a script file instead of inline code**

For longer or more complex Octave programs, write the code to a `.m` file:

1. In the **Project Explorer**, create `lorenz_attractor.m` in the project root and paste the Octave code body into it.
2. In `SeedOctaveCode`, set `shared["octave_script_path"] = "lorenz_attractor.m"` and clear `shared["octave_code"] = ""`.
3. Re-run — the node switches to file mode and executes the `.m` file directly.

### What you learned

- The Octave Script Node runs GNU Octave in batch mode — only `octave` on the PATH is required, no Python interface
- Use `inline_code_key` for short scripts and `script_path_key` for longer `.m` files
- The `result_var` property names the Octave workspace variable to extract and return in `result_var_value`
- The result dict contains `stdout`, `status`, and `result_var_value`
- Octave is a cost-free, open-source alternative to the MATLAB Engine Node for numerical computing

---

## Tutorial T-N117: The USGS Data Catalog Search Node

### What it does

The **USGS Data Catalog Search Node** searches the USGS ScienceBase Catalog — the primary data discovery and management platform for USGS scientific data releases — by keyword. It returns a list of catalog item records, each including a title, summary, publication date, digital object identifier (DOI), and direct download link. This node is the starting point for any data discovery pipeline that needs to find USGS datasets programmatically.

### Use cases

- Finding USGS datasets relevant to a study area or topic before downloading them
- Automating dataset discovery for a data pipeline that runs on a schedule (e.g., daily new releases)
- Building a data catalogue browser that surfaces the most relevant USGS releases for a keyword
- Combining with an LLM Prompt Node to rank search results and recommend the best dataset for a need

### What you'll build

A five-node flow — **Start → Seed Query → USGS Data Catalog Search → LLM Prompt (Recommend) → File Writer → Stop** — that searches ScienceBase for "LiDAR point cloud" datasets, passes the top results to an LLM, and writes a Markdown recommendations file.

### Step-by-step

**Step 1: Create a new project**

Name it `gtkn_part25_data_catalog`.

**Step 2: Build the canvas**

Place: **Start** → **SeedQuery** (Basic Node) → **USGS Data Catalog Search** → **PrepLLMInput** (Basic Node) → **LLM Prompt Node** (AI) → **File Writer Node** (Data/IO) → **Stop**.

Wire all ports including `error` from the USGS Data Catalog Search node to the Stop Node.

**Step 3: Configure the USGS Data Catalog Search Node**

In the **Object Inspector**:

- **query_key**: `sciencebase_query`
- **max_results**: `10`
- **fields**: `id,title,summary,link`
- **result_key**: `sb_results`

**Step 4: Configure the LLM Prompt Node**

- **Title**: `Recommend Dataset`
- **prompt_type**: `string`
- **system_prompt**: `You are a geospatial data expert. Given a list of USGS ScienceBase datasets, recommend the top 3 most useful ones and explain why, formatted as a Markdown list.`
- **input_key**: `llm_input`
- **output_key**: `recommendations`
- **model**: *(leave blank for project default)*

**Step 5: Configure the File Writer Node**

- **input_key**: `recommendations`
- **file_path**: `dataset_recommendations.md`

**Step 6: Write SeedQuery**

```python
from pocketflow import Node

class SeedQuery(Node):
    """Seeds the ScienceBase keyword query."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # Search for LiDAR point cloud datasets — a common geospatial data need
        shared["sciencebase_query"] = "LiDAR point cloud 3DEP"
        return "default"
```

**Step 7: Write PrepLLMInput**

```python
from pocketflow import Node

class PrepLLMInput(Node):
    """Formats the ScienceBase results as an LLM prompt."""

    def prep(self, shared):
        return shared.get("sb_results", {})

    def exec(self, prep_res):
        items = prep_res.get("items", [])
        total = prep_res.get("total_count", 0)

        prompt = (
            f"I searched the USGS ScienceBase Catalog for 'LiDAR point cloud 3DEP' "
            f"and found {total} total items. Here are the top {len(items)} results:\n\n"
        )
        for i, item in enumerate(items, 1):
            title   = item.get("title", "(no title)")
            summary = item.get("summary", "")[:200]
            doi     = item.get("doi", "")
            link    = item.get("link", {}).get("url", "")

            prompt += f"**{i}. {title}**\n"
            if summary:
                prompt += f"Summary: {summary}...\n"
            if doi:
                prompt += f"DOI: {doi}\n"
            if link:
                prompt += f"URL: {link}\n"
            prompt += "\n"

        prompt += (
            "\nBased on these results, recommend the top 3 most useful datasets "
            "for a user who needs high-resolution terrain data for watershed delineation. "
            "Include the dataset title, DOI (if available), and a one-sentence reason."
        )
        return prompt

    def post(self, shared, prep_res, exec_res):
        shared["llm_input"] = exec_res
        return "default"
```

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The flow:

1. Searches ScienceBase for "LiDAR point cloud 3DEP" and retrieves up to 10 results.
2. `PrepLLMInput` formats the dataset list as a ranked-recommendation prompt.
3. The LLM Prompt Node generates a Markdown recommendation report.
4. The File Writer Node saves it to `dataset_recommendations.md`.

Open `dataset_recommendations.md` in the **Project Explorer** to read the AI-curated dataset recommendations.

**Step 9: Schedule as an automated pipeline**

USGS continuously publishes new data releases to ScienceBase. To stay current, use the **Schedule** skill (`/schedule`) to run this flow daily and email the recommendations using an **Email Send Node** at the end of the graph instead of a File Writer.

### What you learned

- The USGS Data Catalog Search Node queries ScienceBase by keyword — no API key needed
- Configure `query_key`, `max_results`, and `result_key`; the `fields` property controls which metadata fields to return
- The result dict contains `items` (list of dataset records) and `total_count`
- Chain with an LLM Prompt Node for AI-curated dataset recommendations — a powerful pattern for automated data discovery
- ScienceBase is the home for all USGS data releases; any USGS dataset with a DOI is discoverable here

---

## Addon Node Series Complete

You have now completed all 34 addon node tutorials, working through:

| Part | Nodes |
|---|---|
| [Part 20](gtkn_part20.md) | Geospatial (7): USGS Elevation Point, 3DEP, National Map, Earthquake Catalog, Landsat, ShakeMap Fetch, ShakeMap Scenario |
| [Part 21](gtkn_part21.md) | Hydrology (8): USGS Water Data, NWIS Query, StreamStats, SWMM, EPANET, MODFLOW 6, FloPy, pyWatershed |
| [Part 22](gtkn_part22.md) | Weather & Building Energy (3): NOAA Weather, WRF Model, EnergyPlus |
| [Part 23](gtkn_part23.md) | Aerospace CFD & Geometry (5): Open VSP, VSPAERO, SU2 CFD, Cart3D, FUN3D |
| [Part 24](gtkn_part24.md) | Aerospace Propulsion, MDO & Mission (6): NASA CEA, RocketPy, GMAT, OpenMDAO, Optimization, Trick |
| [Part 25](gtkn_part25.md) | Wind Energy, Scientific Computing & Data (5): OpenFAST, KiteFAST, MATLAB Engine, Octave Script, USGS Data Catalog |

Together with the original 19 parts (83 builtin nodes), you have now seen every node type in PocketFlow Creator — 117 nodes in total — each demonstrated through a concrete, runnable mini-flow.

---

[← Previous Part: Aerospace Propulsion, MDO and Mission](gtkn_part24.md)  
[↑ Series Index](gtkn_index.md)  
[↑ Tutorials Index](index.md)
