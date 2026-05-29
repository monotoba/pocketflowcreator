# Part 21 — Hydrology and Water Resources Addon Nodes

Part 21 covers the eight hydrology and water resources addon nodes: **USGS Water Data**, **NWIS Query**, **StreamStats Basin**, **SWMM Run**, **EPANET Run**, **MODFLOW 6 Run**, **FloPy Model**, and **pyWatershed**. These nodes connect PocketFlow to the major US hydrologic data services and simulation engines used in watershed studies, water distribution design, stormwater management, and groundwater modelling.

> ⚠️ **Simulation nodes:** Nodes that run simulators locally (SWMM, EPANET, MODFLOW, FloPy, pyWatershed) require the respective software to be installed and on your system PATH. The data-fetching nodes (USGS Water Data, NWIS Query, StreamStats Basin) only require an internet connection.

---

## Tutorial T-N91: The USGS Water Data Node

### What it does

The **USGS Water Data Node** fetches instantaneous or daily streamflow (or other parameter) time-series data from the USGS National Water Information System (NWIS) REST API at `waterservices.usgs.gov`. Provide a USGS site number and a parameter code, and the node returns a list of value/timestamp pairs for the requested period. No API key is required.

### Use cases

- Pulling recent streamflow data to feed into a hydraulic model or flood warning system
- Downloading long-term daily discharge records for frequency analysis
- Monitoring gage height at a structure of interest as part of an automated alert pipeline
- Comparing measured flow at multiple gauges to calibrate a basin model

### What you'll build

A four-node flow — **Start → Seed Site & Params → USGS Water Data → Log Flow Summary → Stop** — that fetches the past 7 days of daily mean discharge from the Potomac River at Point of Rocks, MD (USGS site 01638500).

### Step-by-step

**Step 1: Create a new project**

Name it `gtkn_part21_water_data`.

**Step 2: Build the canvas**

Place: **Start** → **SeedSite** (Basic Node) → **USGS Water Data** → **LogFlow** (Basic Node) → **Stop**.

Wire all edges including the `error` port to Stop.

**Step 3: Configure the USGS Water Data Node**

In the **Object Inspector**:

- **site_key**: `usgs_site`
- **param_cd**: `00060` (discharge, cubic feet per second)
- **period**: `P7D` (7-day period)
- **stat_cd**: `00003` (daily mean; leave blank for instantaneous)
- **result_key**: `water_data`

**Step 4: Write SeedSite**

```python
from pocketflow import Node

class SeedSite(Node):
    """Seeds the USGS site number for the Potomac at Point of Rocks."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # USGS site 01638500 — Potomac River at Point of Rocks, MD
        shared["usgs_site"] = "01638500"
        return "default"
```

**Step 5: Write LogFlow**

```python
from pocketflow import Node

class LogFlow(Node):
    """Prints a summary of the retrieved streamflow time series."""

    def prep(self, shared):
        return shared.get("water_data", {})

    def exec(self, prep_res):
        data = prep_res
        site_name = data.get("site_name", "Unknown")
        values    = data.get("values", [])
        print(f"=== USGS Streamflow — {site_name} ===")
        print(f"  Parameter : {data.get('param_cd', '?')} — {data.get('param_name', '?')}")
        print(f"  Records   : {len(values)}")
        if values:
            recent = values[-3:]  # last 3 readings
            for v in recent:
                print(f"    {v.get('datetime', '?')}  {v.get('value', '?')} cfs")
        return data

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The **Run Log tab** will show the site name and the most recent daily mean discharge values. Try changing `param_cd` to `00065` to retrieve gage height instead of discharge.

### What you learned

- The USGS Water Data Node fetches NWIS time-series data — no API key needed
- `param_cd` selects the data type: `00060` = discharge (cfs), `00065` = gage height (ft)
- `period` is an ISO 8601 duration string: `P7D` = 7 days, `P1Y` = 1 year
- The result dict contains `site_name`, `param_name`, `param_cd`, and a `values` list
- Each value dict has `datetime` and `value` keys

---

## Tutorial T-N92: The NWIS Query Node

### What it does

The **NWIS Query Node** provides three query modes for the USGS National Water Information System: **site** (returns metadata for gauging stations matching state or county filters), **peak** (returns the annual peak flow record for a specific site), and **stat** (returns long-term statistical summaries of streamflow by month). This is the go-to node when you need to characterise a gauge or find all gauges in a region before fetching time-series data.

### Use cases

- Finding all active streamflow gauges in a state for a regional study
- Retrieving the annual peak flow record of a gauge for flood frequency analysis
- Getting the 75th-percentile monthly flow statistics for a gauge to assess low-flow conditions
- Identifying gauges with at least 30 years of record for long-term trend analysis

### What you'll build

A four-node flow — **Start → Seed Query → NWIS Query → Log Peak Flows → Stop** — that retrieves the annual peak flow record for the Colorado River at Lees Ferry, AZ (USGS site 09380000), the most-cited streamflow gauge in the American West.

### Step-by-step

**Step 1: Create a new project**

Name it `gtkn_part21_nwis_query`.

**Step 2: Build the canvas**

Place: **Start** → **SeedQuery** (Basic Node) → **NWIS Query** → **LogPeaks** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 3: Configure the NWIS Query Node**

In the **Object Inspector**:

- **query_type**: `peak`
- **site_key**: `usgs_site`
- **state_cd**: *(leave blank — unused in peak mode)*
- **result_key**: `nwis_result`

**Step 4: Write SeedQuery**

```python
from pocketflow import Node

class SeedQuery(Node):
    """Seeds the site number for the Colorado River at Lees Ferry."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # USGS 09380000 — Colorado River at Lees Ferry, AZ
        # Continuous record since 1921; key gauge for Colorado Compact allocations
        shared["usgs_site"] = "09380000"
        return "default"
```

**Step 5: Write LogPeaks**

```python
from pocketflow import Node

class LogPeaks(Node):
    """Prints the ten largest annual peak flows on record."""

    def prep(self, shared):
        return shared.get("nwis_result", {})

    def exec(self, prep_res):
        data   = prep_res
        peaks  = data.get("peaks", [])
        # Sort by peak discharge descending
        sorted_peaks = sorted(peaks, key=lambda r: r.get("peak_va", 0), reverse=True)
        print(f"=== Annual Peak Flows — Colorado River at Lees Ferry ===")
        print(f"  Total years of record: {len(peaks)}")
        print(f"\n  Top 10 Peak Flows:")
        print(f"  {'Year':>6}  {'Peak Flow (cfs)':>18}  {'Gage Ht (ft)':>14}")
        print(f"  {'-'*6}  {'-'*18}  {'-'*14}")
        for row in sorted_peaks[:10]:
            yr  = row.get("peak_dt", "????")[:4]
            pq  = row.get("peak_va", "?")
            ght = row.get("gage_ht", "?")
            print(f"  {yr:>6}  {pq:>18,.0f}  {ght:>14}")
        return data

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The Run Log will show the ten largest peak flows ever recorded at Lees Ferry — the 1884 flood (~220,000 cfs) should appear near the top. This data is used for Colorado River Basin water management and dam operations.

### What you learned

- The NWIS Query Node supports three modes: `site` (metadata), `peak` (annual peak flows), `stat` (statistics)
- In `peak` mode, the result dict contains a `peaks` list — each item has `peak_dt`, `peak_va`, and `gage_ht`
- In `site` mode, set `state_cd` to a two-letter state code to retrieve all gauges in that state
- In `stat` mode, the result provides monthly flow percentiles for long-term characterisation

---

## Tutorial T-N93: The StreamStats Basin Node

### What it does

The **StreamStats Basin Node** calls the USGS StreamStats REST API to delineate a watershed upstream of a pour point (an outlet location defined by latitude/longitude) and compute basin characteristics such as drainage area, mean elevation, mean annual precipitation, and stream length. This is the same computation performed by the StreamStats web application, now available programmatically.

### Use cases

- Computing drainage area and basin characteristics for a bridge or culvert design point
- Automating watershed delineation for hundreds of pour points in a regional study
- Feeding basin characteristics (area, slope, precipitation) into a rational-method peak flow calculation
- Verifying computed basin statistics against field measurements for model calibration

### What you'll build

A four-node flow — **Start → Seed Pour Point → StreamStats Basin → Log Basin Stats → Stop** — that delineates the watershed draining to the USGS gauge on the North Fork Shenandoah River at Strasburg, VA.

### Step-by-step

**Step 1: Create a new project**

Name it `gtkn_part21_streamstats`.

**Step 2: Build the canvas**

Place: **Start** → **SeedPourPoint** (Basic Node) → **StreamStats Basin** → **LogStats** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 3: Configure the StreamStats Basin Node**

In the **Object Inspector**:

- **lat_key**: `lat`
- **lon_key**: `lon`
- **state_cd**: `VA`
- **result_key**: `basin_result`

**Step 4: Write SeedPourPoint**

```python
from pocketflow import Node

class SeedPourPoint(Node):
    """Seeds the pour point for the North Fork Shenandoah at Strasburg, VA."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # USGS gauge 01634000 — North Fork Shenandoah River at Strasburg, VA
        shared["lat"] = 38.9837
        shared["lon"] = -78.3603
        return "default"
```

**Step 5: Write LogStats**

```python
from pocketflow import Node

class LogStats(Node):
    """Logs the StreamStats basin characteristics."""

    def prep(self, shared):
        return shared.get("basin_result", {})

    def exec(self, prep_res):
        result = prep_res
        chars  = result.get("basin_characteristics", {})
        print("=== StreamStats Basin Delineation ===")
        print(f"  Workspace ID   : {result.get('workspace_id', '?')}")
        print(f"  Drainage Area  : {chars.get('DRNAREA', '?')} sq mi")
        print(f"  Mean Elevation : {chars.get('ELEV', '?')} ft")
        print(f"  Mean Ann. Precip: {chars.get('PRECIP', '?')} in")
        print(f"  Stream Length  : {chars.get('STRM', '?')} mi")
        return result

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. StreamStats delineation can take 15–60 seconds. The Run Log will print the basin drainage area and other characteristics. The `result_key` dict also contains a `workspace_id` that can be used to retrieve additional flow statistics from the StreamStats API in subsequent calls.

> ⚠️ **Note:** StreamStats coverage and available characteristics vary by state. Not all characteristic codes are available everywhere. If a characteristic is missing from the result, it is not computed for the selected state and basin.

### What you learned

- The StreamStats Basin Node delineates watersheds and computes basin characteristics via the USGS StreamStats REST API
- Supply a pour point lat/lon and a two-letter state code
- Basin characteristics are returned as a dict keyed by StreamStats parameter codes (e.g., `DRNAREA`, `ELEV`)
- Delineation takes up to 60 seconds — this is normal for the StreamStats web service
- The `workspace_id` in the result can be used for follow-up StreamStats API calls

---

## Tutorial T-N94: The SWMM Run Node

### What it does

The **SWMM Run Node** executes an EPA Storm Water Management Model (SWMM) 5 simulation using a local SWMM installation and a user-supplied `.inp` input file. It returns a summary dict containing peak junction overflow volumes, conduit peak flows, and subcatchment runoff totals parsed from the SWMM report file (`.rpt`). SWMM is the industry-standard model for urban stormwater system design and analysis.

### Use cases

- Running a SWMM model of a stormwater collection system and reporting peak flows for pipe sizing
- Automating sensitivity analyses by modifying input file parameters and re-running SWMM
- Comparing pre- and post-development runoff volumes from a green infrastructure retrofit
- Generating LID (Low-Impact Development) performance metrics for a subdivision design

### What you'll build

A four-node flow — **Start → Seed Input Path → SWMM Run → Log Peak Flows → Stop** — that runs a provided SWMM `.inp` file and reports the top-five highest peak conduit flow rates.

### Step-by-step

**Step 1: Install SWMM 5**

Download and install EPA SWMM 5.2 from https://www.epa.gov/water-research/storm-water-management-model-swmm. The `swmm5` executable must be on your system PATH. Verify with `swmm5 --version` in a terminal.

**Step 2: Prepare an input file**

Copy a SWMM `.inp` file into your project root. You can use any of the example files that ship with SWMM (e.g., `Example1.inp` from the SWMM 5.2 installation). Name it `stormwater.inp` in the project root.

**Step 3: Create a new project**

Name it `gtkn_part21_swmm`.

**Step 4: Build the canvas**

Place: **Start** → **SeedInputPath** (Basic Node) → **SWMM Run** → **LogPeakFlows** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 5: Configure the SWMM Run Node**

In the **Object Inspector**:

- **inp_path_key**: `swmm_inp_path`
- **report_key**: `swmm_rpt_path`
- **result_key**: `swmm_result`

**Step 6: Write SeedInputPath**

```python
import os
from pocketflow import Node

class SeedInputPath(Node):
    """Seeds the path to the SWMM input file."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        shared["swmm_inp_path"] = os.path.join(project_dir, "stormwater.inp")
        shared["swmm_rpt_path"] = os.path.join(project_dir, "stormwater.rpt")
        return "default"
```

**Step 7: Write LogPeakFlows**

```python
from pocketflow import Node

class LogPeakFlows(Node):
    """Reports the top-5 conduit peak flows from the SWMM run."""

    def prep(self, shared):
        return shared.get("swmm_result", {})

    def exec(self, prep_res):
        result    = prep_res
        conduits  = result.get("conduit_peak_flows", {})
        junctions = result.get("junction_flooding", {})

        print("=== SWMM Simulation Results ===")
        print(f"  Simulation status : {result.get('status', '?')}")

        # Top-5 conduit peak flows
        sorted_conds = sorted(
            conduits.items(), key=lambda kv: kv[1], reverse=True
        )
        print(f"\n  Top-5 Conduit Peak Flows (CFS):")
        for name, flow in sorted_conds[:5]:
            print(f"    {name:20s}  {flow:8.2f} cfs")

        # Flooding junctions (if any)
        flooded = {k: v for k, v in junctions.items() if v > 0}
        if flooded:
            print(f"\n  ⚠️  {len(flooded)} junction(s) flooded:")
            for jname, vol in sorted(flooded.items(), key=lambda kv: kv[1], reverse=True)[:5]:
                print(f"    {jname:20s}  {vol:8.3f} acre-ft overflow")
        else:
            print(f"\n  ✅ No junctions flooded.")
        return result

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The SWMM executable will run; the Run Log will show its output. After completion, `LogPeakFlows` prints the top conduit flows and any flooding summary. The full SWMM report is written to `stormwater.rpt` in the project root.

### What you learned

- The SWMM Run Node requires SWMM 5 installed and `swmm5` on the system PATH
- Supply `.inp` and `.rpt` file paths via shared store keys
- The result dict contains `conduit_peak_flows` and `junction_flooding` dicts
- Check `result.get("status")` for `"normal"` to confirm a successful run
- Use this node in a loop with parameter variations to perform automated sensitivity analyses

---

## Tutorial T-N95: The EPANET Run Node

### What it does

The **EPANET Run Node** runs an EPA EPANET 2 water distribution network simulation using a local EPANET installation and a `.inp` network file. It returns nodal pressures, pipe flow rates, and velocity summaries parsed from the EPANET binary output file. EPANET is the standard model for steady-state and extended-period simulation of water distribution systems.

### Use cases

- Checking whether all nodes in a distribution network meet minimum pressure requirements
- Simulating diurnal demand patterns to identify pressure-deficient periods
- Sizing pipes for a new subdivision connection to an existing distribution network
- Performing a water quality simulation (chlorine decay, age) through the network

### What you'll build

A four-node flow — **Start → Seed Network Path → EPANET Run → Check Pressures → Stop** — that runs the EPANET Net3 example network and flags any node where simulated pressure falls below 20 psi.

### Step-by-step

**Step 1: Install EPANET**

Download EPANET from https://www.epa.gov/water-research/epanet. Copy the EPANET example file `Net3.inp` from the EPANET installation into your project root, or use any other EPANET `.inp` file you have available.

**Step 2: Create a new project**

Name it `gtkn_part21_epanet`.

**Step 3: Build the canvas**

Place: **Start** → **SeedNetworkPath** (Basic Node) → **EPANET Run** → **CheckPressures** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 4: Configure the EPANET Run Node**

In the **Object Inspector**:

- **inp_path_key**: `epanet_inp_path`
- **result_key**: `epanet_result`

**Step 5: Write SeedNetworkPath**

```python
import os
from pocketflow import Node

class SeedNetworkPath(Node):
    """Seeds the path to the EPANET input file."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        shared["epanet_inp_path"] = os.path.join(project_dir, "Net3.inp")
        return "default"
```

**Step 6: Write CheckPressures**

```python
from pocketflow import Node

class CheckPressures(Node):
    """Reports low-pressure nodes (< 20 psi) from the EPANET simulation."""

    MIN_PSI = 20.0

    def prep(self, shared):
        return shared.get("epanet_result", {})

    def exec(self, prep_res):
        result    = prep_res
        pressures = result.get("node_pressures", {})

        low_pressure = {
            node: psi for node, psi in pressures.items()
            if psi < self.MIN_PSI
        }

        print("=== EPANET Pressure Check ===")
        print(f"  Total nodes simulated : {len(pressures)}")
        print(f"  Nodes below {self.MIN_PSI} psi   : {len(low_pressure)}")
        if low_pressure:
            print(f"\n  ⚠️  Low-pressure nodes:")
            for node, psi in sorted(low_pressure.items(), key=lambda kv: kv[1]):
                print(f"    Node {node:10s}  {psi:6.1f} psi")
        else:
            print(f"\n  ✅ All nodes meet minimum pressure ({self.MIN_PSI} psi).")
        return result

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 7: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The EPANET simulation runs and `CheckPressures` prints the pressure summary. Adjust the `MIN_PSI` threshold to explore different pressure standards.

### What you learned

- The EPANET Run Node requires EPANET 2 installed and accessible
- The result dict contains `node_pressures` (dict: node ID → psi), `pipe_flows`, and `pipe_velocities`
- Use a Condition Node or Basic Node downstream to branch on pressure violations
- EPANET `.inp` files can be generated programmatically and passed to this node for automated design-iteration workflows

---

## Tutorial T-N96: The MODFLOW 6 Run Node

### What it does

The **MODFLOW 6 Run Node** executes a USGS MODFLOW 6 groundwater flow simulation. It expects a pre-configured MODFLOW 6 simulation directory (containing `mfsim.nam` and associated package files) and runs the `mf6` executable. On completion it parses the listing file (`mfsim.lst`) and returns a status summary, convergence information, and head statistics. MODFLOW 6 is the current-generation USGS groundwater modelling code.

### Use cases

- Running a steady-state groundwater model to compute water table elevations in an aquifer
- Simulating transient aquifer response to pumping for a wellfield design
- Automating a MODFLOW calibration loop by modifying hydraulic conductivity and re-running
- Checking model convergence and listing-file warnings as part of a QA pipeline

### What you'll build

A four-node flow — **Start → Seed Simulation Directory → MODFLOW 6 Run → Log Results → Stop** — that runs a pre-built MODFLOW 6 simulation and reports the convergence status and head statistics.

### Step-by-step

**Step 1: Install MODFLOW 6**

Download `mf6` from https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model and place it on your PATH. Verify with `mf6 --version`.

**Step 2: Prepare a simulation directory**

Create a folder `mf6_sim/` in the project root containing a complete MODFLOW 6 simulation. The simplest option is to copy one of the MODFLOW 6 distribution examples (e.g., `ex-gwf-twri01`) into your project root and rename the folder `mf6_sim/`.

**Step 3: Create a new project**

Name it `gtkn_part21_modflow6`.

**Step 4: Build the canvas**

Place: **Start** → **SeedSimDir** (Basic Node) → **MODFLOW 6 Run** → **LogResults** (Basic Node) → **Stop**.

Wire all ports.

**Step 5: Configure the MODFLOW 6 Run Node**

In the **Object Inspector**:

- **sim_dir_key**: `mf6_sim_dir`
- **result_key**: `mf6_result`

**Step 6: Write SeedSimDir**

```python
import os
from pocketflow import Node

class SeedSimDir(Node):
    """Seeds the path to the MODFLOW 6 simulation directory."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        shared["mf6_sim_dir"] = os.path.join(project_dir, "mf6_sim")
        return "default"
```

**Step 7: Write LogResults**

```python
from pocketflow import Node

class LogResults(Node):
    """Logs MODFLOW 6 run status and head statistics."""

    def prep(self, shared):
        return shared.get("mf6_result", {})

    def exec(self, prep_res):
        result = prep_res
        print("=== MODFLOW 6 Run Results ===")
        print(f"  Status       : {result.get('status', '?')}")
        print(f"  Converged    : {result.get('converged', '?')}")
        print(f"  Iterations   : {result.get('iterations', '?')}")
        head = result.get("head_stats", {})
        if head:
            print(f"\n  Head Statistics (m):")
            print(f"    Min  : {head.get('min', '?'):.3f}")
            print(f"    Max  : {head.get('max', '?'):.3f}")
            print(f"    Mean : {head.get('mean', '?'):.3f}")
        return result

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. MODFLOW 6 will execute and write its listing file to the simulation directory. The Run Log shows convergence status and head statistics.

### What you learned

- The MODFLOW 6 Run Node requires `mf6` on the system PATH and a complete simulation directory
- The simulation directory must contain `mfsim.nam` and all package files
- The result dict includes `status`, `converged`, `iterations`, and `head_stats`
- Use with a Condition Node to halt a calibration loop when the model fails to converge

---

## Tutorial T-N97: The FloPy Model Node

### What it does

The **FloPy Model Node** runs a MODFLOW simulation managed by a Python FloPy model or simulation object. Instead of pointing to an existing simulation directory, you construct the model programmatically in a **Python Tool Node** or Basic Node using the `flopy` Python library, then pass the configured model object via the shared store. The FloPy Model Node then calls `model.run_model()` and returns head arrays and budget statistics.

### Use cases

- Building a MODFLOW model entirely in Python and running it within a PocketFlow graph
- Wrapping FloPy-based parameter studies in a Batch Node loop
- Automating model construction, run, and result extraction in a single pipeline
- Prototyping MODFLOW models without managing simulation files manually

### What you'll build

A four-node flow — **Start → Build FloPy Model → FloPy Model Node → Log Head Results → Stop** — that constructs a minimal 3-layer MODFLOW 6 steady-state model using FloPy and runs it inline.

### Step-by-step

**Step 1: Install FloPy**

```bash
pip install flopy
```

Verify: `python -c "import flopy; print(flopy.__version__)"`.

**Step 2: Create a new project**

Name it `gtkn_part21_flopy`. Create a `flopy_workspace/` folder in the project root.

**Step 3: Build the canvas**

Place: **Start** → **BuildModel** (Basic Node) → **FloPy Model** → **LogHeads** (Basic Node) → **Stop**.

Wire all ports.

**Step 4: Configure the FloPy Model Node**

In the **Object Inspector**:

- **model_key**: `flopy_model`
- **exe_name**: `mf6`
- **result_key**: `flopy_result`

**Step 5: Write BuildModel**

```python
import os
import flopy
from pocketflow import Node

class BuildModel(Node):
    """Builds a minimal MODFLOW 6 steady-state model with FloPy."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        ws = os.path.join(project_dir, "flopy_workspace")
        os.makedirs(ws, exist_ok=True)

        # --- Build a simple 1-layer, 10×10 grid steady-state model ---
        sim = flopy.mf6.MFSimulation(
            sim_name="simple", version="mf6", exe_name="mf6", sim_ws=ws
        )
        tdis = flopy.mf6.ModflowTdis(sim, nper=1)
        ims  = flopy.mf6.ModflowIms(sim, print_option="SUMMARY")

        gwf = flopy.mf6.ModflowGwf(sim, modelname="simple", save_flows=True)

        dis = flopy.mf6.ModflowGwfdis(
            gwf, nlay=1, nrow=10, ncol=10,
            delr=100.0, delc=100.0, top=10.0, botm=0.0
        )
        ic  = flopy.mf6.ModflowGwfic(gwf, strt=10.0)
        npf = flopy.mf6.ModflowGwfnpf(gwf, k=10.0)

        # Constant head: left column = 10 m, right column = 5 m
        chd_list = (
            [[(0, i, 0), 10.0] for i in range(10)] +
            [[(0, i, 9),  5.0] for i in range(10)]
        )
        chd = flopy.mf6.ModflowGwfchd(gwf, stress_period_data=chd_list)

        oc = flopy.mf6.ModflowGwfoc(
            gwf,
            head_filerecord="simple.hds",
            budget_filerecord="simple.bud",
            saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")]
        )
        sim.write_simulation()
        return sim

    def post(self, shared, prep_res, exec_res):
        shared["flopy_model"] = exec_res   # the MFSimulation object
        return "default"
```

**Step 6: Write LogHeads**

```python
from pocketflow import Node

class LogHeads(Node):
    """Logs the head statistics from the FloPy run."""

    def prep(self, shared):
        return shared.get("flopy_result", {})

    def exec(self, prep_res):
        result = prep_res
        print("=== FloPy / MODFLOW 6 Results ===")
        print(f"  Success     : {result.get('success', '?')}")
        head = result.get("head_stats", {})
        if head:
            print(f"  Min head    : {head.get('min', '?'):.3f} m")
            print(f"  Max head    : {head.get('max', '?'):.3f} m")
            print(f"  Mean head   : {head.get('mean', '?'):.3f} m")
        return result

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 7: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. FloPy writes the simulation files to `flopy_workspace/`, runs MODFLOW 6, and returns the head array. The Run Log shows the head gradient from 10 m (left) to 5 m (right) as expected for a horizontal-flow problem.

### What you learned

- The FloPy Model Node accepts a `flopy.mf6.MFSimulation` (or `flopy.modflow.Modflow`) object via the shared store
- Build the model in a preceding Basic Node using the standard FloPy API
- The result dict includes `success`, `head_stats`, and the path to the head file
- This pattern lets you parameterise the model in FloPy and run it inside a Batch Node for sensitivity studies

---

## Tutorial T-N98: The pyWatershed Node

### What it does

The **pyWatershed Node** runs a USGS National Hydrologic Model (NHM) simulation using the `pywatershed` Python package. It expects a domain directory (containing NHM parameter and climate input files) and an optional control file. The node runs the simulation, collects output time series (e.g., streamflow at HRU outlets, soil moisture, snow water equivalent), and returns a summary dict with key output variables.

### Use cases

- Simulating daily streamflow for a set of Hydrologic Response Units (HRUs) in the NHM domain
- Comparing simulated vs observed streamflow during a historical calibration period
- Assessing the hydrologic impact of climate scenarios by substituting modified climate inputs
- Building an operational forecast pipeline that runs pywatershed on updated climate inputs daily

### What you'll build

A four-node flow — **Start → Seed Domain → pyWatershed → Log Outputs → Stop** — that runs a small NHM subdomain simulation and logs mean daily streamflow at the basin outlet HRU.

### Step-by-step

**Step 1: Install pywatershed**

```bash
pip install pywatershed
```

You will also need an NHM domain directory. The pywatershed repository includes example domains at `test_data/`. Download the repo and locate the `sagehen_creek` example domain, or use any small NHM sub-domain you have.

**Step 2: Create a new project**

Name it `gtkn_part21_pywatershed`.

**Step 3: Build the canvas**

Place: **Start** → **SeedDomain** (Basic Node) → **pyWatershed** → **LogOutputs** (Basic Node) → **Stop**.

Wire all ports.

**Step 4: Configure the pyWatershed Node**

In the **Object Inspector**:

- **domain_dir_key**: `pws_domain_dir`
- **control_file_key**: `pws_control_file`
- **result_key**: `pws_result`

**Step 5: Write SeedDomain**

```python
import os
from pocketflow import Node

class SeedDomain(Node):
    """Seeds the pywatershed domain directory path."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        # Path to the NHM domain directory (must contain parameter files + climate inputs)
        shared["pws_domain_dir"]    = os.path.join(project_dir, "nhm_domain")
        shared["pws_control_file"]  = ""   # blank = use default control.yml
        return "default"
```

**Step 6: Write LogOutputs**

```python
from pocketflow import Node

class LogOutputs(Node):
    """Logs pywatershed streamflow summary."""

    def prep(self, shared):
        return shared.get("pws_result", {})

    def exec(self, prep_res):
        result  = prep_res
        q_stats = result.get("streamflow_stats", {})
        print("=== pyWatershed NHM Simulation Results ===")
        print(f"  Status          : {result.get('status', '?')}")
        print(f"  HRUs simulated  : {result.get('n_hru', '?')}")
        print(f"  Simulation days : {result.get('n_days', '?')}")
        if q_stats:
            print(f"\n  Outlet Streamflow Summary (mm/day):")
            print(f"    Mean : {q_stats.get('mean', '?'):.3f}")
            print(f"    Max  : {q_stats.get('max', '?'):.3f}")
            print(f"    Min  : {q_stats.get('min', '?'):.3f}")
        return result

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 7: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The pywatershed simulation runs over the period defined in the control file. The Run Log reports streamflow statistics at the basin outlet. Run time scales with the number of HRUs and the simulation period length.

### What you learned

- The pyWatershed Node runs USGS NHM simulations via the `pywatershed` Python package
- The domain directory must contain NHM parameter files and climate input NetCDF files
- Leave `control_file_key` pointing to an empty string to use the default `control.yml` in the domain directory
- The result dict includes `status`, `n_hru`, `n_days`, and `streamflow_stats`
- Use this node in a Batch Node loop with different climate input files for scenario analysis

---

[← Previous Part: Geospatial Addon Nodes](gtkn_part20.md)  
[→ Next Part: Weather, Atmosphere and Building Energy](gtkn_part22.md)  
[↑ Series Index](gtkn_index.md)  
[↑ Tutorials Index](index.md)
