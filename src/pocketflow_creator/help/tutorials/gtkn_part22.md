# Part 22 — Weather, Atmosphere, and Building Energy Addon Nodes

Part 22 covers three addon nodes that bring atmospheric and building energy simulation into PocketFlow: **NOAA Weather**, **WRF Model**, and **EnergyPlus Run**. The NOAA Weather Node fetches live US National Weather Service observations and forecasts from a free public API. The WRF Model Node drives a local Weather Research and Forecasting (WRF) numerical weather prediction installation. The EnergyPlus Run Node runs a DOE EnergyPlus building energy simulation and returns annual energy use summaries.

---

## Tutorial T-N99: The NOAA Weather Node

### What it does

The **NOAA Weather Node** calls two endpoints of the US National Weather Service (NWS) REST API at `api.weather.gov` to return current surface observations and a 7-day hourly forecast for any latitude/longitude point within the contiguous US, Alaska, and Hawaii. It performs the two-step NWS API lookup automatically — first resolving the grid point, then fetching observations and the forecast grid — and returns a unified result dict. No API key or account is required.

### Use cases

- Fetching site weather conditions before triggering an outdoor construction or inspection task
- Providing current temperature, wind speed, and precipitation for an energy model pre-processor
- Building a daily weather briefing pipeline that formats NWS data into a readable report
- Integrating live forecast data into a flow that adjusts irrigation schedules or HVAC setpoints

### What you'll build

A four-node flow — **Start → Seed Location → NOAA Weather → Format & Print Forecast → Stop** — that retrieves the current conditions and 7-day high/low temperature forecast for Denver International Airport (39.8561 °N, 104.6737 °W).

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part22_noaa_weather`.

**Step 2: Build the canvas**

Drag the following nodes onto the canvas in left-to-right order:

1. **Start Node** (Flow Control)
2. **Basic Node** — rename to `SeedLocation`
3. **NOAA Weather Node** (Weather / Atmosphere)
4. **Basic Node** — rename to `FormatForecast`
5. **Stop Node**

Wire: Start →(default)→ SeedLocation →(default)→ NOAA Weather →(default)→ FormatForecast →(default)→ Stop.

Also wire the `error` port of the NOAA Weather Node to the Stop Node.

**Step 3: Configure the NOAA Weather Node**

Click the **NOAA Weather Node** and set in the **Object Inspector**:

- **lat_key**: `lat`
- **lon_key**: `lon`
- **result_key**: `noaa_weather`

That is all the configuration needed. The node resolves the NWS grid point, fetches observations, and fetches the 7-day forecast automatically.

**Step 4: Write SeedLocation**

```python
from pocketflow import Node

class SeedLocation(Node):
    """Seeds the coordinates for Denver International Airport."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # Denver International Airport
        shared["lat"] = 39.8561
        shared["lon"] = -104.6737
        return "default"
```

**Step 5: Write FormatForecast**

```python
from pocketflow import Node

class FormatForecast(Node):
    """Formats and prints the NWS current conditions and 7-day forecast."""

    def prep(self, shared):
        return shared.get("noaa_weather", {})

    def exec(self, prep_res):
        data = prep_res

        # Current observations
        obs = data.get("current_observation", {})
        print("=== NOAA Current Conditions ===")
        print(f"  Station   : {obs.get('station_name', '?')}")
        print(f"  Temp      : {obs.get('temperature_c', '?')} °C")
        print(f"  Conditions: {obs.get('text_description', '?')}")
        print(f"  Wind      : {obs.get('wind_speed_kmh', '?')} km/h "
              f"from {obs.get('wind_direction_deg', '?')}°")

        # 7-day forecast (daytime periods)
        periods = data.get("forecast_periods", [])
        daytime = [p for p in periods if p.get("isDaytime", True)]
        print(f"\n=== 7-Day Forecast (Denver International Airport) ===")
        print(f"  {'Period':25}  {'High/Low':>10}  Outlook")
        print(f"  {'-'*25}  {'-'*10}  {'-'*35}")
        for period in daytime[:7]:
            name  = period.get("name", "?")
            temp  = period.get("temperature", "?")
            unit  = period.get("temperatureUnit", "F")
            short = period.get("shortForecast", "?")
            print(f"  {name:25}  {temp:>8}°{unit}  {short}")

        return data

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The **Run Log tab** will display current temperature and conditions at Denver International Airport followed by the 7-day high/low forecast.

> ⚠️ **Note:** The NWS API only covers US locations. For non-US coordinates, the node routes the `error` action. Also note that the NWS API can be slow (1–3 seconds per call) and occasionally returns 503 errors during peak demand. If you see intermittent failures, add a **Retry Node** upstream.

**Step 7: Adapt for any US city**

Change `lat` and `lon` in `SeedLocation` to any US city. Some examples:

| City | Latitude | Longitude |
|---|---|---|
| Seattle, WA | 47.6062 | -122.3321 |
| Houston, TX | 29.7604 | -95.3698 |
| Miami, FL | 25.7617 | -80.1918 |
| Anchorage, AK | 61.2181 | -149.9003 |

### What you learned

- The NOAA Weather Node requires no API key and covers all US locations
- Configure only `lat_key`, `lon_key`, and `result_key` — the node handles the NWS two-step API lookup
- The result dict contains `current_observation` (with `temperature_c`, `wind_speed_kmh`, etc.) and `forecast_periods` (list of 7-day period dicts)
- Non-US coordinates route the `error` action
- Add a Retry Node upstream if you need resilience against occasional NWS API 503 errors

---

## Tutorial T-N100: The WRF Model Node

### What it does

The **WRF Model Node** drives a local installation of the Weather Research and Forecasting (WRF) Model — specifically the WRF-ARW core as used in operational and research numerical weather prediction. It executes `real.exe` (to prepare boundary conditions) and `wrf.exe` (the actual model run) inside a WRF run directory that you have already configured with namelists and input data. The node returns a list of output `wrfout_*` file paths and a status summary. WRF is a community mesoscale atmospheric model maintained by NCAR.

### Use cases

- Running a 24–72 hour high-resolution mesoscale weather forecast for a specific domain
- Producing dynamically downscaled climate projections for a regional impact assessment
- Automating WRF ensemble runs by varying namelist parameters across a Batch Node
- Post-processing WRF output file paths and feeding them to downstream analysis nodes

### What you'll build

A four-node flow — **Start → Seed WRF Run Directory → WRF Model → Log Output Files → Stop** — that runs WRF on a pre-configured run directory and logs the paths to the generated `wrfout_d01_*` files.

### Step-by-step

**Step 1: Install WRF**

WRF installation is non-trivial and outside the scope of this tutorial. Follow the NCAR WRF installation guide at https://www2.mmm.ucar.edu/wrf/OnLineTutorial/. Ensure `real.exe` and `wrf.exe` are compiled and present in your WRF run directory.

> 💡 **Tip:** The WRF Model Node is most useful in a production pipeline after WRF is already working on your system. A good first test is to reproduce one of the WRF tutorial cases and confirm `wrf.exe` completes successfully before connecting it to PocketFlow.

**Step 2: Prepare a WRF run directory**

Complete the standard WRF pre-processing steps:

1. Run WPS (geogrid, ungrib, metgrid) to prepare `met_em_*` files.
2. Set up your `namelist.input` in the WRF run directory.
3. Link the `met_em_*` files and all required input files into the run directory.

The WRF Model Node will call `real.exe` then `wrf.exe` inside this directory.

**Step 3: Create a new project**

Name it `gtkn_part22_wrf`.

**Step 4: Build the canvas**

Place: **Start** → **SeedRunDir** (Basic Node) → **WRF Model** → **LogOutputFiles** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 5: Configure the WRF Model Node**

In the **Object Inspector**:

- **run_dir_key**: `wrf_run_dir`
- **nprocs**: `4` (number of MPI processes; set to the number of cores available)
- **skip_real**: `false` (set to `true` if `wrfinput_d01` already exists and you only need to re-run `wrf.exe`)
- **result_key**: `wrf_result`

**Step 6: Write SeedRunDir**

```python
import os
from pocketflow import Node

class SeedRunDir(Node):
    """Seeds the WRF run directory path."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # Absolute path to your WRF run/ directory
        # Must already contain namelist.input and met_em_* files
        shared["wrf_run_dir"] = "/path/to/your/WRF/run"
        return "default"
```

> ⚠️ **Important:** Replace `/path/to/your/WRF/run` with the actual absolute path to your configured WRF run directory. This is not a relative path — use the full filesystem path.

**Step 7: Write LogOutputFiles**

```python
from pocketflow import Node

class LogOutputFiles(Node):
    """Logs the WRF output file paths on completion."""

    def prep(self, shared):
        return shared.get("wrf_result", {})

    def exec(self, prep_res):
        result = prep_res
        print("=== WRF Model Run Results ===")
        print(f"  Status      : {result.get('status', '?')}")
        print(f"  real.exe    : {result.get('real_status', '?')}")
        print(f"  wrf.exe     : {result.get('wrf_status', '?')}")
        print(f"  Elapsed     : {result.get('elapsed_seconds', '?'):.0f} s")

        wrfout_files = result.get("wrfout_files", [])
        print(f"\n  Output files ({len(wrfout_files)}):")
        for f in wrfout_files:
            print(f"    {f}")
        return result

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. WRF runs are long — a 24-hour simulation on a small domain (e.g., 10 km resolution, 9×9 grid) with 4 MPI processes typically takes 5–20 minutes. Watch the **Run Log tab** for `real.exe` and `wrf.exe` stdout output. On completion, the `wrfout_d01_*` files are listed.

> 💡 **Tip:** Once the WRF output files are in the shared store, you can pass their paths to a **Shell Command Node** (Part 16) to run `wrf_to_cf.py` or NCO post-processing commands, then to a **File Writer Node** to archive results — all within the same PocketFlow graph.

### What you learned

- The WRF Model Node requires a functioning WRF-ARW installation with `real.exe` and `wrf.exe` compiled
- The run directory must be fully prepared (namelists, `met_em_*` files) before the node runs
- Set `skip_real: true` to bypass `real.exe` if `wrfinput_d01` already exists
- The result dict contains `status`, `real_status`, `wrf_status`, `elapsed_seconds`, and `wrfout_files`
- Pass `wrfout_files` paths to downstream Shell Command or Python Tool Nodes for post-processing

---

## Tutorial T-N101: The EnergyPlus Run Node

### What it does

The **EnergyPlus Run Node** executes a US Department of Energy EnergyPlus building energy simulation. It accepts the paths to an IDF (or epJSON) input file and an EPW weather file, runs the `energyplus` executable, and returns a summary dict parsed from the EnergyPlus CSV output: total site energy use (kWh), electricity and gas end-use breakdown, and peak demand (kW). EnergyPlus is the physics-based building energy simulation engine that underpins tools like OpenStudio and DesignBuilder.

### Use cases

- Simulating a building model for a full year to assess annual energy consumption and HVAC sizing
- Comparing baseline vs retrofit energy use as part of a green building design workflow
- Automating sensitivity studies by varying IDF parameters (window area, insulation R-value) across a Batch Node
- Generating an AI-narrated energy audit by passing EnergyPlus results to an LLM Prompt Node

### What you'll build

A five-node flow — **Start → Seed IDF Paths → EnergyPlus Run → LLM Prompt (Audit) → File Writer → Stop** — that simulates the EnergyPlus `RefBldgMediumOfficeNew2004` reference building and uses an LLM to generate a plain-English energy audit report saved to `audit_report.md`.

### Step-by-step

**Step 1: Install EnergyPlus**

Download EnergyPlus 23.x (or later) from https://energyplus.net/. Verify installation with `energyplus --version`. The `energyplus` command must be on your PATH.

**Step 2: Obtain reference building IDF and EPW files**

EnergyPlus ships with reference building IDF files. After installation, navigate to the EnergyPlus `ExampleFiles/` directory. Copy `RefBldgMediumOfficeNew2004_Chicago.idf` (or any other IDF file) into your project root. You will also need an EPW (weather) file — copy `USA_IL_Chicago.TMY3.epw` from the EnergyPlus `WeatherData/` directory into the project root.

**Step 3: Create a new project**

Name it `gtkn_part22_energyplus`. Create an `eplus_output/` folder in the project root.

**Step 4: Build the canvas**

Place: **Start** → **SeedPaths** (Basic Node) → **EnergyPlus Run** → **LLM Prompt Node** (AI) → **File Writer Node** (Data/IO) → **Stop**.

Wire all ports including `error` from EnergyPlus Run to Stop.

**Step 5: Configure the EnergyPlus Run Node**

In the **Object Inspector**:

- **idf_path_key**: `eplus_idf_path`
- **weather_path_key**: `eplus_weather_path`
- **output_dir_key**: `eplus_output_dir`
- **result_key**: `eplus_result`

**Step 6: Configure the LLM Prompt Node**

In the **Object Inspector** for the LLM Prompt Node:

- **Title**: `Generate Audit`
- **prompt_type**: `string`
- **prompt_file**: *(leave blank — we will set the prompt in the Start Node's `post()` override; or use the `system_prompt` field)*
- **system_prompt**: `You are an experienced building energy engineer. Write a concise, professional energy audit report in Markdown.`
- **input_key**: `audit_input`
- **output_key**: `audit_report`
- **model**: *(leave blank to use the project default)*

**Step 7: Configure the File Writer Node**

- **input_key**: `audit_report`
- **file_path**: `audit_report.md`

**Step 8: Write SeedPaths**

```python
import os
from pocketflow import Node

class SeedPaths(Node):
    """Seeds the IDF, weather file, and output directory paths."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        shared["eplus_idf_path"] = os.path.join(
            project_dir, "RefBldgMediumOfficeNew2004_Chicago.idf"
        )
        shared["eplus_weather_path"] = os.path.join(
            project_dir, "USA_IL_Chicago.TMY3.epw"
        )
        shared["eplus_output_dir"] = os.path.join(project_dir, "eplus_output")
        return "default"
```

**Step 9: Add a data-bridging Basic Node between EnergyPlus and the LLM**

The LLM Prompt Node reads `shared["audit_input"]`, but the EnergyPlus Run Node writes to `shared["eplus_result"]`. Insert a **Basic Node** (rename to `PrepAuditInput`) between the EnergyPlus Run Node and the LLM Prompt Node to format the simulation results as a prompt string.

Add the `PrepAuditInput` node to the canvas: **EnergyPlus Run** →(default)→ **PrepAuditInput** →(default)→ **LLM Prompt (Generate Audit)**.

```python
from pocketflow import Node

class PrepAuditInput(Node):
    """Formats EnergyPlus results as the LLM audit prompt."""

    def prep(self, shared):
        return shared.get("eplus_result", {})

    def exec(self, prep_res):
        r = prep_res
        end_uses = r.get("end_uses", {})
        prompt = (
            f"Building: {r.get('idf_name', 'Unknown')}\n"
            f"Simulation year: {r.get('year', 'Unknown')}\n"
            f"Total site energy: {r.get('total_site_energy_kwh', '?'):.0f} kWh/yr\n"
            f"Peak electricity demand: {r.get('peak_electricity_kw', '?'):.1f} kW\n\n"
            f"End-use breakdown (kWh/yr):\n"
        )
        for use, kwh in end_uses.items():
            prompt += f"  {use}: {kwh:.0f}\n"
        prompt += (
            "\nBased on this annual simulation data, write a 3-paragraph energy audit "
            "report identifying the dominant energy end-uses, key opportunities for "
            "efficiency improvement, and recommended next steps."
        )
        return prompt

    def post(self, shared, prep_res, exec_res):
        shared["audit_input"] = exec_res
        return "default"
```

**Step 10: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. EnergyPlus simulates a full calendar year — runtime is typically 30–120 seconds for a medium-size building. After completion:

1. The `eplus_output/` folder contains the full EnergyPlus output files.
2. `PrepAuditInput` formats the results as an LLM prompt.
3. The LLM Prompt Node generates the audit narrative.
4. The File Writer Node saves it as `audit_report.md`.

Open `audit_report.md` in the **Project Explorer** to read the AI-generated energy audit.

> 💡 **Tip:** To run a parametric study, wrap the SeedPaths → EnergyPlus Run → PrepAuditInput chain inside a **Batch Node** loop, modifying the IDF file programmatically between iterations to vary window-to-wall ratio, insulation R-value, or HVAC system type.

### What you learned

- The EnergyPlus Run Node requires EnergyPlus installed and `energyplus` on the PATH
- Provide `idf_path_key`, `weather_path_key`, and `output_dir_key` — the node handles execution and output parsing
- The result dict contains `total_site_energy_kwh`, `peak_electricity_kw`, and `end_uses` (by end-use category)
- Chain with an LLM Prompt Node to generate human-readable summaries from simulation data — a powerful pattern for engineering report automation
- EnergyPlus full-year simulations take 30–120 seconds; plan for this latency in production pipelines

---

[← Previous Part: Hydrology and Water Resources](gtkn_part21.md)  
[→ Next Part: Aerospace CFD and Geometry](gtkn_part23.md)  
[↑ Series Index](gtkn_index.md)  
[↑ Tutorials Index](index.md)
