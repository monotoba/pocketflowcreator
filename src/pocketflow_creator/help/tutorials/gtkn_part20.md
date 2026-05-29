# Part 20 — Geospatial Addon Nodes

Part 20 introduces the seven geospatial addon nodes: **USGS Elevation Point**, **USGS 3DEP Elevation**, **National Map Download**, **Earthquake Catalog**, **Landsat Search & Download**, **ShakeMap Fetch**, and **ShakeMap Scenario**. These nodes wrap publicly available US government REST APIs and tools, letting you bring real-world geospatial data into a PocketFlow pipeline with nothing more than property configuration and a shared store key.

> ⚠️ **Addon nodes prerequisite:** Addon nodes are installed separately from the built-in palette. Before starting these tutorials, confirm that the geospatial addon package is installed: go to **Tools → Node Type Library**, switch to the **Installed Custom** tab, and verify you see the nodes listed below. If they are missing, use **Tools → Node Type Library → Install node package** and select the appropriate `.py` files from the `addon_nodes/` folder.

Complete Parts 1–6 of the GTKN series before starting here. You should be comfortable with the shared store, the Object Inspector, and writing Basic Node code.

---

## Tutorial T-N84: The USGS Elevation Point Node

### What it does

The **USGS Elevation Point Node** calls the USGS Elevation Point Query Service (EPQS) REST API to return the ground elevation at a single latitude/longitude point. It reads the coordinates from the shared store, makes one HTTP GET request to `epqs.nationalmap.gov`, and writes back a result dict containing the elevation value, the input coordinates, and the units. No API key is required.

### Use cases

- Determining ground surface elevation at a project site for engineering calculations
- Enriching a list of lat/lon observations with elevation data before analysis
- Checking whether a coordinate pair is above or below a flood threshold elevation
- Quick QA of GPS coordinates by confirming reasonable elevation values

### What you'll build

A four-node flow — **Start → Seed Coordinates → USGS Elevation Point → Log Result → Stop** — that retrieves the elevation at the US Capitol building (38.8897 °N, 77.0089 °W) in meters and prints it to the Run Log.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part20_elevation_point`. A blank canvas opens.

**Step 2: Build the canvas**

Drag the following nodes onto the canvas in left-to-right order:

1. **Start Node** (Flow Control)
2. **Basic Node** — rename to `SeedCoordinates`
3. **USGS Elevation Point Node** (Geospatial)
4. **Basic Node** — rename to `LogResult`
5. **Stop Node**

Wire: Start →(default)→ SeedCoordinates →(default)→ USGS Elevation Point →(default)→ LogResult →(default)→ Stop.

Also wire the `error` port from the **USGS Elevation Point Node** to the **Stop Node** (or to a separate `Stop — Error` node) so that the validator accepts the flow. All declared action ports must be wired.

> 💡 **Tip:** Use **View > Auto Arrange… (Ctrl+Shift+L)** with the **Layered** algorithm after placing all five nodes to snap them into a clean horizontal layout.

**Step 3: Configure the USGS Elevation Point Node**

Click the **USGS Elevation Point Node** to select it. In the **Object Inspector** set:

- **lat_key**: `lat` — the shared store key holding the latitude (default; leave as-is)
- **lon_key**: `lon` — the shared store key holding the longitude (default; leave as-is)
- **units**: `Meters`
- **result_key**: `elevation_result`

These four properties are all that is required. The node handles the HTTP call internally.

**Step 4: Write the SeedCoordinates node**

Select **SeedCoordinates** and open the **Python editor tab**. This node seeds the shared store with the US Capitol coordinates:

```python
from pocketflow import Node

class SeedCoordinates(Node):
    """Seeds the shared store with a lat/lon to look up."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # US Capitol building, Washington DC
        shared["lat"] = 38.8897
        shared["lon"] = -77.0089
        return "default"
```

Save with **Ctrl+S**.

**Step 5: Write the LogResult node**

Select **LogResult** and open the **Python editor tab**:

```python
from pocketflow import Node

class LogResult(Node):
    """Prints the elevation result to the Run Log."""

    def prep(self, shared):
        return shared.get("elevation_result", {})

    def exec(self, prep_res):
        result = prep_res
        print("=== USGS Elevation Point Result ===")
        if result:
            lat  = result.get("lat", "?")
            lon  = result.get("lon", "?")
            elev = result.get("elevation", "?")
            units = result.get("units", "?")
            print(f"  Location : {lat}°N, {lon}°W")
            print(f"  Elevation: {elev} {units}")
        else:
            print("  (no result — check for error action)")
        return result

    def post(self, shared, prep_res, exec_res):
        return "default"
```

Save with **Ctrl+S**.

**Step 6: Validate and run**

Press **Ctrl+Shift+V** to validate. Then press **F5** to run. Switch to the **Run Log tab** — you should see output similar to:

```
=== USGS Elevation Point Result ===
  Location : 38.8897°N, -77.0089°W
  Elevation: 17.45 Meters
```

Switch to the **Shared Store tab** to inspect the full `elevation_result` dict.

> ⚠️ **Note:** The EPQS API requires an internet connection. If the call fails (firewall, rate limit, or service outage), the node routes the `error` action. Check the **Run Log tab** for the full error message and confirm that `epqs.nationalmap.gov` is reachable from your machine.

**Step 7: Try a different point**

Update `SeedCoordinates.post()` to use coordinates of your choice — a project site, a USGS gauging station, or any point within the contiguous US. Re-run and observe the new elevation. The EPQS covers the entire US including Alaska and Hawaii.

### What you learned

- The USGS Elevation Point Node requires no API key — it calls a free public REST endpoint
- Configure `lat_key`, `lon_key`, `units`, and `result_key` in the Object Inspector; no custom node code is needed for the USGS node itself
- Always wire the `error` port so the validator accepts the flow
- The result dict contains `lat`, `lon`, `elevation`, and `units` keys
- The node can be dropped into any flow that needs to enrich coordinates with ground elevation

---

## Tutorial T-N85: The USGS 3DEP Elevation Node

### What it does

The **USGS 3DEP Elevation Node** downloads a Digital Elevation Model (DEM) raster for a geographic bounding box using the USGS 3D Elevation Program (3DEP) Web Coverage Service (WCS). It writes the downloaded GeoTIFF file to a local directory and stores the output file path in the shared store. The 3DEP dataset offers national coverage at 1/3 arc-second (~10 m), 1 arc-second (~30 m), and 2 arc-second resolutions.

### Use cases

- Downloading terrain data for a watershed delineation or flood inundation study
- Preparing a DEM for input to a hydraulic or hydrologic model
- Building an elevation base layer for GIS analysis of a study area
- Comparing DEM resolution options (1/3 vs 1 arc-second) before selecting one for production

### What you'll build

A four-node flow — **Start → Seed Bounding Box → USGS 3DEP Elevation → Log Output Path → Stop** — that downloads a 1/3 arc-second DEM for a small area around Rocky Mountain National Park and logs the output GeoTIFF path.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part20_3dep`. Create a `dem_output/` folder in the project root using the **Project Explorer** (right-click → **New Folder**).

**Step 2: Build the canvas**

Place in left-to-right order: **Start** → **Basic Node** (`SeedBBox`) → **USGS 3DEP Elevation** → **Basic Node** (`LogOutputPath`) → **Stop**.

Wire all edges including the `error` port of the 3DEP node to the Stop Node.

**Step 3: Configure the USGS 3DEP Elevation Node**

Click the node and set in the **Object Inspector**:

- **bbox_key**: `bbox`
- **resolution**: `1/3` (arc-second; ~10 m — highest quality)
- **output_dir_key**: `dem_output_dir`
- **result_key**: `dem_result`

**Step 4: Write SeedBBox**

```python
from pocketflow import Node

class SeedBBox(Node):
    """Seeds the bounding box for Rocky Mountain National Park area."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # [west, south, east, north] in decimal degrees
        # Small box ~10 km × 10 km around Estes Park, CO
        shared["bbox"] = [-105.65, 40.32, -105.50, 40.42]
        # Output directory for the downloaded GeoTIFF
        shared["dem_output_dir"] = "dem_output"
        return "default"
```

**Step 5: Write LogOutputPath**

```python
from pocketflow import Node

class LogOutputPath(Node):
    """Logs the downloaded DEM file path."""

    def prep(self, shared):
        return shared.get("dem_result", {})

    def exec(self, prep_res):
        result = prep_res
        print("=== USGS 3DEP DEM Download ===")
        if result:
            print(f"  File    : {result.get('output_path', '(none)')}")
            print(f"  CRS     : {result.get('crs', '?')}")
            print(f"  Bbox    : {result.get('bbox', '?')}")
        else:
            print("  Download failed — check error log.")
        return result

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. After the flow completes, check the `dem_output/` folder in the **Project Explorer**. You should see a `.tif` file. The **Run Log tab** will show its path. The file can be opened in QGIS or any GeoTIFF-compatible viewer.

> ⚠️ **Note:** DEM downloads can take 10–30 seconds depending on the bounding box size and resolution. Keep the study area small (≤ 0.5° × 0.5°) for tutorial purposes. Larger downloads will time out.

### What you learned

- The 3DEP node downloads a GeoTIFF DEM for any US bounding box at up to 1/3 arc-second resolution
- The bounding box format is `[west, south, east, north]` in decimal degrees
- Configure `bbox_key`, `resolution`, `output_dir_key`, and `result_key` — no custom code required for the 3DEP node
- The result dict includes `output_path`, `crs`, and `bbox` keys
- Keep bounding boxes small during development to avoid long download times

---

## Tutorial T-N86: The National Map Download Node

### What it does

The **National Map Download Node** queries The National Map (TNM) Access API — the USGS data discovery and download portal — for available datasets within a bounding box. It can search for elevation data, hydrography (NHD), transportation, structures, imagery (NAIP), and topographic maps. By setting `download` to true the node can also download the discovered files. In search-only mode it returns a list of dataset records with metadata and download URLs.

### Use cases

- Discovering what USGS datasets are available for a project area before downloading
- Automating bulk download of NHD flowline shapefiles for a multi-county study area
- Building a dataset inventory pipeline for a geospatial data catalogue
- Selecting the best-resolution DEM product available for a specific region

### What you'll build

A four-node flow — **Start → Seed Query → National Map Download → Log Datasets → Stop** — that searches for 1/3 arc-second DEM products near Denver, CO, and lists the available dataset titles and download URLs.

### Step-by-step

**Step 1: Create a new project**

Name it `gtkn_part20_nationalmap`.

**Step 2: Build the canvas**

Place: **Start** → **SeedQuery** (Basic Node) → **National Map Download** → **LogDatasets** (Basic Node) → **Stop**.

Wire all edges including `error` to Stop.

**Step 3: Configure the National Map Download Node**

In the **Object Inspector**:

- **bbox_key**: `bbox`
- **dataset**: `National Elevation Dataset (NED) 1/3 arc-second`
- **max_items**: `5`
- **download**: `false` (search only — do not download files in this tutorial)
- **output_dir_key**: `tnm_output_dir`
- **result_key**: `tnm_result`

**Step 4: Write SeedQuery**

```python
from pocketflow import Node

class SeedQuery(Node):
    """Seeds the bounding box for the Denver metro area."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # Denver metro area bounding box
        shared["bbox"] = [-105.2, 39.5, -104.6, 40.0]
        shared["tnm_output_dir"] = "tnm_downloads"
        return "default"
```

**Step 5: Write LogDatasets**

```python
from pocketflow import Node

class LogDatasets(Node):
    """Logs the discovered TNM dataset records."""

    def prep(self, shared):
        return shared.get("tnm_result", {})

    def exec(self, prep_res):
        result = prep_res
        items = result.get("items", [])
        print(f"=== National Map: {len(items)} dataset(s) found ===")
        for i, item in enumerate(items, 1):
            title = item.get("title", "(no title)")
            url   = item.get("downloadURL", "(no URL)")
            size  = item.get("sizeInBytes", 0)
            mb    = round(size / 1_048_576, 1) if size else "?"
            print(f"  [{i}] {title}")
            print(f"       Size: {mb} MB")
            print(f"       URL : {url}")
        return result

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The **Run Log tab** should list up to five NED 1/3 arc-second tiles with their download URLs. To actually download one, set **download** to `true` in the inspector and re-run — the node will fetch each file into `tnm_downloads/`.

### What you learned

- The National Map Download Node searches the TNM API for datasets within a bounding box
- Setting `download: false` performs a search-only dry run — safe for exploration
- The `dataset` property selects the data product type (NED, NHD, NAIP, Topo, etc.)
- The result dict contains an `items` list; each item has `title`, `downloadURL`, and `sizeInBytes`
- Always start with `download: false` to confirm the right products are available before downloading

---

## Tutorial T-N87: The Earthquake Catalog Node

### What it does

The **Earthquake Catalog Node** queries the USGS FDSN Event Web Service (formerly ComCat) to retrieve a list of earthquake events matching a geographic bounding box, time range, and minimum magnitude. It returns a list of event dicts — each with magnitude, depth, location description, time, and a USGS detail URL — written to the shared store. No authentication is required.

### Use cases

- Fetching recent seismicity data for a site hazard assessment
- Feeding earthquake event IDs to a ShakeMap Fetch Node downstream
- Building an automated seismic monitoring report for a region of interest
- Analysing historical seismicity patterns as input to probabilistic hazard analysis

### What you'll build

A four-node flow — **Start → Seed Query Params → Earthquake Catalog → Summarise Events → Stop** — that fetches M ≥ 4.0 earthquakes in California from the past 90 days and prints a summary table to the Run Log.

### Step-by-step

**Step 1: Create a new project**

Name it `gtkn_part20_earthquake`.

**Step 2: Build the canvas**

Place: **Start** → **SeedParams** (Basic Node) → **Earthquake Catalog** → **SummariseEvents** (Basic Node) → **Stop**.

Wire all edges including `error` to Stop.

**Step 3: Configure the Earthquake Catalog Node**

In the **Object Inspector**:

- **bbox_key**: `bbox`
- **start_time**: `2025-03-01` (adjust to be ~90 days before today)
- **end_time**: *(leave blank for "now")*
- **min_mag**: `4.0`
- **max_results**: `20`
- **result_key**: `eq_events`

**Step 4: Write SeedParams**

```python
from pocketflow import Node

class SeedParams(Node):
    """Seeds the California bounding box for earthquake queries."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # California bounding box
        shared["bbox"] = [-124.5, 32.5, -114.0, 42.0]
        return "default"
```

**Step 5: Write SummariseEvents**

```python
from pocketflow import Node

class SummariseEvents(Node):
    """Prints a summary table of earthquake events."""

    def prep(self, shared):
        return shared.get("eq_events", [])

    def exec(self, prep_res):
        events = prep_res
        print(f"=== {len(events)} Earthquake(s) M≥4.0 in California ===")
        print(f"  {'Mag':>5}  {'Depth':>7}  {'Time (UTC)':22}  {'Place'}")
        print(f"  {'-'*5}  {'-'*7}  {'-'*22}  {'-'*40}")
        for ev in events:
            mag   = ev.get("magnitude", "?")
            depth = ev.get("depth_km", "?")
            time  = ev.get("time", "?")
            place = ev.get("place", "?")
            print(f"  {mag:>5.1f}  {depth:>5.1f}km  {time:22}  {place}")
        return events

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The **Run Log tab** will display a table of recent California earthquakes sorted by time (most recent first). Note the `id` field in each event dict — you will use event IDs in Tutorial T-N89 (ShakeMap Fetch).

> 💡 **Tip:** To wire this node to a downstream **ShakeMap Fetch Node**, extract the first event's `id` value from `shared["eq_events"][0]["id"]` in a Basic Node and write it to `shared["eq_event_id"]` before the ShakeMap node.

### What you learned

- The Earthquake Catalog Node wraps the USGS FDSN Event API — no API key needed
- `bbox`, `start_time`, `min_mag`, and `max_results` control the query scope
- Each event dict contains `magnitude`, `depth_km`, `time`, `place`, and `id`
- The `id` field can be passed to a ShakeMap Fetch Node to retrieve ShakeMap products for that event
- Leave `end_time` blank to query up to the current moment

---

## Tutorial T-N88: The Landsat Search & Download Node

### What it does

The **Landsat Search & Download Node** authenticates with the USGS EarthExplorer M2M (Machine-to-Machine) API and searches for Landsat Collection 2 Level-2 scenes matching a bounding box, date range, and cloud cover threshold. In download mode it fetches the selected scenes to a local directory. It supports Landsat 8 and Landsat 9 and returns a list of scene metadata records. A free USGS EarthExplorer account is required.

### Use cases

- Downloading cloud-free Landsat imagery for land cover change analysis
- Building an automated archive of satellite imagery for a recurring monitoring area
- Finding scenes with < 10 % cloud cover for a specific growing season
- Selecting Landsat scenes as input to a remote sensing processing pipeline

### What you'll build

A four-node flow — **Start → Seed Credentials & AOI → Landsat Search & Download → Log Scenes → Stop** — that searches (without downloading) for Landsat 9 scenes over the Chesapeake Bay watershed from the past 60 days.

### Step-by-step

**Step 1: Create a new project**

Name it `gtkn_part20_landsat`.

> ⚠️ **Prerequisites:** You need a free USGS EarthExplorer account. Register at https://ers.cr.usgs.gov/register. Your credentials are used only in the `SeedCredentials` node below — they are never stored in the project file.

**Step 2: Build the canvas**

Place: **Start** → **SeedCredentials** (Basic Node) → **Landsat Search & Download** → **LogScenes** (Basic Node) → **Stop**.

Wire all edges including `error` to Stop.

**Step 3: Configure the Landsat Search & Download Node**

In the **Object Inspector**:

- **username_key**: `usgs_username`
- **token_key**: `usgs_token`
- **bbox_key**: `bbox`
- **dataset**: `landsat_ot_c2_l2` (Landsat Collection 2 Level-2)
- **start_date**: `2025-04-01`
- **end_date**: *(leave blank for today)*
- **max_cloud_pct**: `20`
- **max_results**: `5`
- **download**: `false`
- **output_dir_key**: `landsat_output_dir`
- **result_key**: `landsat_scenes`

**Step 4: Write SeedCredentials**

```python
import os
from pocketflow import Node

class SeedCredentials(Node):
    """Seeds USGS credentials and search parameters."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # Load credentials from environment variables — never hard-code these.
        # Set USGS_USERNAME and USGS_TOKEN in your shell before running.
        shared["usgs_username"] = os.environ.get("USGS_USERNAME", "")
        shared["usgs_token"]    = os.environ.get("USGS_TOKEN", "")

        # Chesapeake Bay watershed approximate bounding box
        shared["bbox"] = [-79.8, 36.9, -74.5, 42.6]
        shared["landsat_output_dir"] = "landsat_scenes"
        return "default"
```

> 💡 **Tip:** Use a **Secret Node** (covered in GTKN Part 19) to load credentials from environment variables or a `.env` file in production flows. The Secret Node is the idiomatic PocketFlow approach for any key or password.

**Step 5: Write LogScenes**

```python
from pocketflow import Node

class LogScenes(Node):
    """Logs the found Landsat scene metadata."""

    def prep(self, shared):
        return shared.get("landsat_scenes", [])

    def exec(self, prep_res):
        scenes = prep_res
        print(f"=== {len(scenes)} Landsat Scene(s) Found ===")
        for i, s in enumerate(scenes, 1):
            print(f"  [{i}] Scene ID : {s.get('entity_id', '?')}")
            print(f"       Date     : {s.get('acquisition_date', '?')}")
            print(f"       Cloud %  : {s.get('cloud_cover', '?'):.1f}")
            print(f"       Path/Row : {s.get('wrs_path', '?')}/{s.get('wrs_row', '?')}")
        return scenes

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 6: Validate and run**

Set `USGS_USERNAME` and `USGS_TOKEN` in your terminal, then press **F5**. The Run Log will list up to five scene IDs with dates and cloud cover percentages. To download the scenes, change **download** to `true` in the inspector and re-run.

### What you learned

- The Landsat Search & Download Node requires a free USGS EarthExplorer account
- Store credentials in environment variables and load them with `os.environ.get()` or a Secret Node
- Set `download: false` for search-only dry runs; switch to `true` to fetch scene data
- Each scene record includes `entity_id`, `acquisition_date`, `cloud_cover`, `wrs_path`, and `wrs_row`
- The `dataset` property selects the Landsat collection (`landsat_ot_c2_l2` = Collection 2 Level-2)

---

## Tutorial T-N89: The ShakeMap Fetch Node

### What it does

The **ShakeMap Fetch Node** downloads ShakeMap ground-motion products for a specific USGS earthquake event ID from the USGS earthquake hazard data service. Products include the ground-motion intensity grid (`grid.xml`), contour GeoJSON, MMI raster, and PNG maps. The event ID is the same identifier returned by the Earthquake Catalog Node. No API key is required.

### Use cases

- Downloading ShakeMap grids for post-earthquake damage assessment workflows
- Automating retrieval of ShakeMap products immediately after a significant event
- Feeding ground-motion intensity data into a loss estimation or risk model
- Building a ShakeMap archive for historical earthquake events

### What you'll build

A four-node flow — **Start → Seed Event ID → ShakeMap Fetch → Log Product Paths → Stop** — that downloads the ShakeMap `grid.xml` for the 2019 Ridgecrest M7.1 earthquake (USGS event ID `ci38457511`).

### Step-by-step

**Step 1: Create a new project**

Name it `gtkn_part20_shakemap_fetch`. Create a `shakemap_products/` folder in the project root.

**Step 2: Build the canvas**

Place: **Start** → **SeedEventID** (Basic Node) → **ShakeMap Fetch** → **LogProducts** (Basic Node) → **Stop**.

Wire `default` and `error` ports as before.

**Step 3: Configure the ShakeMap Fetch Node**

In the **Object Inspector**:

- **event_id_key**: `eq_event_id`
- **product_type**: `download/grid.xml`
- **output_dir_key**: `shakemap_output_dir`
- **result_key**: `shakemap_fetch_result`

**Step 4: Write SeedEventID**

```python
from pocketflow import Node

class SeedEventID(Node):
    """Seeds the USGS event ID for the 2019 Ridgecrest M7.1 earthquake."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # 2019 Ridgecrest M7.1 — well-known publicly available ShakeMap
        shared["eq_event_id"] = "ci38457511"
        shared["shakemap_output_dir"] = "shakemap_products"
        return "default"
```

**Step 5: Write LogProducts**

```python
from pocketflow import Node

class LogProducts(Node):
    """Logs the downloaded ShakeMap product file paths."""

    def prep(self, shared):
        return shared.get("shakemap_fetch_result", {})

    def exec(self, prep_res):
        result = prep_res
        print("=== ShakeMap Fetch Result ===")
        print(f"  Event ID : {result.get('event_id', '?')}")
        print(f"  Status   : {result.get('status', '?')}")
        for path in result.get("downloaded_files", []):
            print(f"  File     : {path}")
        return result

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. After the run, the `shakemap_products/` folder will contain `grid.xml` for the Ridgecrest earthquake. The **Run Log tab** shows the local file path. You can open `grid.xml` in any text editor or GIS tool to inspect MMI and PGA values on the grid.

> 💡 **Tip:** To chain this node with the Earthquake Catalog Node, add a Basic Node between them that extracts `shared["eq_events"][0]["id"]` and writes it to `shared["eq_event_id"]`.

### What you learned

- The ShakeMap Fetch Node downloads USGS ShakeMap products by USGS event ID — no API key required
- `product_type` selects the product file (e.g. `download/grid.xml`, `download/stationlist.json`)
- The result dict contains `event_id`, `status`, and `downloaded_files` (list of local paths)
- Chain with the Earthquake Catalog Node to automatically fetch ShakeMaps for new events
- The `shakemap_products/` folder is created automatically if it does not exist

---

## Tutorial T-N90: The ShakeMap Scenario Node

### What it does

The **ShakeMap Scenario Node** runs the USGS ShakeMap v4 software locally to produce a ground-motion scenario for a hypothetical or historical fault rupture. Rather than fetching existing ShakeMap data from the web, this node drives the local `shake` command-line tool to generate a brand-new scenario from an `event.xml` file you supply. This is how emergency managers and researchers produce "what-if" ground-motion scenarios before an earthquake occurs.

### Use cases

- Producing deterministic ground-motion maps for scenario-based earthquake response planning
- Generating synthetic ShakeMap grids for input to a loss estimation model (e.g., Hazus)
- Testing the sensitivity of ground-motion predictions to fault rupture parameters
- Validating local ShakeMap installations by re-running a well-documented historical event

### What you'll build

A four-node flow — **Start → Seed Scenario Directory → ShakeMap Scenario → Log Grid Path → Stop** — that runs ShakeMap v4 on a pre-configured scenario event directory and reports the path to the output ground-motion grid.

### Step-by-step

**Step 1: Install ShakeMap v4**

ShakeMap v4 must be installed locally. Follow the official USGS instructions at https://usgs.github.io/shakemap/. Confirm that the `shake` command is on your `PATH` by running `shake --help` in a terminal.

**Step 2: Create a scenario event directory**

ShakeMap v4 expects an event directory containing `event.xml`. Create the following structure inside your project:

```
shakemap_events/
  my_scenario/
    event.xml
```

A minimal `event.xml` for a hypothetical M6.5 event:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<earthquake id="my_scenario"
            lat="37.9"
            lon="-122.0"
            depth="10"
            mag="6.5"
            locstring="Hypothetical M6.5 East Bay Scenario"
            time="2025-06-01T12:00:00Z"
            timezone="UTC"/>
```

**Step 3: Create a new project**

Name it `gtkn_part20_shakemap_scenario`.

**Step 4: Build the canvas**

Place: **Start** → **SeedScenario** (Basic Node) → **ShakeMap Scenario** → **LogGridPath** (Basic Node) → **Stop**.

Wire all edges.

**Step 5: Configure the ShakeMap Scenario Node**

In the **Object Inspector**:

- **event_dir_key**: `shakemap_event_dir`
- **commands**: `assemble, model, contour` (comma-separated ShakeMap pipeline steps)
- **result_key**: `shakemap_scenario_result`

**Step 6: Write SeedScenario**

```python
import os
from pocketflow import Node

class SeedScenario(Node):
    """Seeds the path to the ShakeMap scenario event directory."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # Absolute path to the scenario event directory
        project_dir = os.path.dirname(os.path.abspath(__file__))
        shared["shakemap_event_dir"] = os.path.join(
            project_dir, "shakemap_events", "my_scenario"
        )
        return "default"
```

**Step 7: Write LogGridPath**

```python
from pocketflow import Node

class LogGridPath(Node):
    """Logs the output grid path from the ShakeMap scenario run."""

    def prep(self, shared):
        return shared.get("shakemap_scenario_result", {})

    def exec(self, prep_res):
        result = prep_res
        print("=== ShakeMap Scenario Result ===")
        print(f"  Status    : {result.get('status', '?')}")
        print(f"  Grid path : {result.get('grid_path', '(none)')}")
        print(f"  Commands  : {result.get('commands_run', [])}")
        return result

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. ShakeMap will run the `assemble`, `model`, and `contour` pipeline steps. The Run Log shows each command's output. After completion, the `grid_path` in the log points to the generated `grid.xml` inside the event's ShakeMap output directory.

> ⚠️ **Note:** ShakeMap v4 requires a working installation with GMPE data files. If `shake` is not on your PATH, the node routes the `error` action and logs the subprocess error. This node is intended for users who already have ShakeMap v4 operational on their system.

### What you learned

- The ShakeMap Scenario Node requires a local ShakeMap v4 installation
- Provide an `event.xml` in the event directory; the node runs the `shake` pipeline commands you specify
- The `commands` property controls which ShakeMap processing steps run (e.g., `assemble, model, contour`)
- The result dict includes `status`, `grid_path`, and `commands_run`
- Use this node for "what-if" scenario planning before or independent of real earthquake events

---

[← Previous Part: Resilience, Messaging, and Security](gtkn_part19.md)  
[→ Next Part: Hydrology and Water Resources](gtkn_part21.md)  
[↑ Series Index](gtkn_index.md)  
[↑ Tutorials Index](index.md)
