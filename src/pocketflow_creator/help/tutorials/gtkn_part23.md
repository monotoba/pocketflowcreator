# Part 23 — Aerospace CFD and Geometry Addon Nodes

Part 23 covers five aerospace computational fluid dynamics (CFD) and geometry nodes: **Open VSP Geometry**, **VSPAERO Analysis**, **SU2 CFD**, **Cart3D Analysis**, and **FUN3D Run**. These nodes connect PocketFlow to the major open-source and NASA CFD toolchains, ranging from rapid conceptual-level vortex-lattice analysis (VSPAERO) through inviscid Euler methods (Cart3D) to full Reynolds-Averaged Navier-Stokes solvers (SU2, FUN3D). The geometry pipeline starts with Open VSP, which generates the geometry that feeds VSPAERO and can export formats for the other CFD codes.

> ⚠️ **Tool prerequisites:** Each node requires the corresponding software installed and accessible on your system PATH:
> - **Open VSP Geometry**: OpenVSP 3.x (`vsp` command)
> - **VSPAERO Analysis**: Bundled with OpenVSP (`vspaero` command)
> - **SU2 CFD**: SU2 Suite (`SU2_CFD` command)
> - **Cart3D Analysis**: NASA Cart3D (`autoCart.py` or `cart3d` command)
> - **FUN3D Run**: NASA FUN3D (`nodet_mpi` or `nodet` command)

---

## Tutorial T-N102: The Open VSP Geometry Node

### What it does

The **Open VSP Geometry Node** loads a `.vsp3` parametric geometry model, optionally updates named design variables (e.g., wing span, fuselage length), and exports the updated geometry in a requested format — STL, STEP, IGES, DegenGeom CSV, or OBJ. It uses the OpenVSP Python API (`openvsp`) to drive the model programmatically. This node is the starting point for any VSP-based aerodynamic analysis pipeline.

### Use cases

- Parametrically varying wing aspect ratio or fuselage fineness ratio for a design sweep
- Exporting STL files for 3D-printing or meshing in external tools
- Generating a DegenGeom CSV for input to the VSPAERO vortex-lattice solver
- Automating geometry updates across a Batch Node loop for multi-point optimisation

### What you'll build

A four-node flow — **Start → Seed VSP Model Path → Open VSP Geometry → Log Export Path → Stop** — that loads a wing-body `.vsp3` model, updates the wing half-span to 12 m, and exports a DegenGeom CSV file for VSPAERO analysis.

### Step-by-step

**Step 1: Install OpenVSP**

Download OpenVSP from https://openvsp.org/. Confirm `vsp --version` works in a terminal. Install the OpenVSP Python API:

```bash
pip install openvsp
```

**Step 2: Prepare a VSP3 file**

Open the OpenVSP GUI and create a simple wing-body model, then save it as `wing_body.vsp3` in your project root. Alternatively, download any `.vsp3` file from the OpenVSP example gallery at https://github.com/OpenVSP/OpenVSP.

**Step 3: Create a new project**

Name it `gtkn_part23_openvsp`.

**Step 4: Build the canvas**

Place: **Start** → **SeedModelPath** (Basic Node) → **Open VSP Geometry** → **LogExportPath** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 5: Configure the Open VSP Geometry Node**

In the **Object Inspector**:

- **vsp3_path_key**: `vsp3_path`
- **export_format**: `degen_geom`
- **design_vars_key**: `vsp_design_vars`
- **output_path_key**: `vsp_output_path`

**Step 6: Write SeedModelPath**

```python
import os
from pocketflow import Node

class SeedModelPath(Node):
    """Seeds the VSP3 model path and design variable updates."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        shared["vsp3_path"] = os.path.join(project_dir, "wing_body.vsp3")

        # Design variable overrides: {parm_container: {parm_group: {parm_name: value}}}
        # These names must match exactly what appears in the OpenVSP model.
        # Leave as {} to export without modifications.
        shared["vsp_design_vars"] = {
            "Wing": {
                "WingGeom": {
                    "Span": 12.0   # Half-span in meters
                }
            }
        }
        return "default"
```

**Step 7: Write LogExportPath**

```python
from pocketflow import Node

class LogExportPath(Node):
    """Logs the exported geometry file path."""

    def prep(self, shared):
        return {
            "output_path": shared.get("vsp_output_path", ""),
            "export_format": "degen_geom",
        }

    def exec(self, prep_res):
        path = prep_res["output_path"]
        fmt  = prep_res["export_format"]
        print("=== Open VSP Geometry Export ===")
        print(f"  Format      : {fmt}")
        print(f"  Output file : {path}")
        if path:
            import os
            size_kb = os.path.getsize(path) / 1024 if os.path.exists(path) else 0
            print(f"  File size   : {size_kb:.1f} KB")
        return prep_res

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The Open VSP node loads the `.vsp3` model, applies the span override, and exports the DegenGeom CSV. The Run Log shows the output file path. This path is stored in `shared["vsp_output_path"]` — exactly the input required by the **VSPAERO Analysis Node** in Tutorial T-N103.

> 💡 **Tip:** To build a geometry-CFD pipeline, chain this node directly to the VSPAERO Analysis Node (next tutorial). Set the `degen_geom_key` of the VSPAERO node to the same key as `output_path_key` of this node (`vsp_output_path`).

### What you learned

- The Open VSP Geometry Node uses the OpenVSP Python API to load, modify, and export `.vsp3` models
- Design variable overrides use a nested dict: `{container: {group: {parm_name: value}}}`
- The `export_format` property controls the output: `degen_geom` for VSPAERO, `stl` for meshing, `stp`/`iges` for CAD exchange
- The exported file path is stored in `output_path_key` for downstream nodes
- Leave `design_vars_key` pointing to an empty dict to export without modifications

---

## Tutorial T-N103: The VSPAERO Analysis Node

### What it does

The **VSPAERO Analysis Node** runs the VSPAERO vortex-lattice / panel method aerodynamic solver (bundled with OpenVSP) on a DegenGeom CSV file. It computes lift coefficient (CL), drag coefficient (CD), pitching moment coefficient (CM), and span efficiency at the specified angle of attack and Mach number. VSPAERO is appropriate for subsonic conceptual-design aerodynamic analysis where inviscid, linearised flow assumptions are acceptable.

### Use cases

- Generating a CL–CD polar for a wing or full aircraft at conceptual design stage
- Evaluating the aerodynamic effect of wing sweep, taper, or dihedral parameter variations
- Computing trim conditions (zero-moment angle of attack) for stability analysis
- Providing aerodynamic coefficients as input to a mission analysis or performance model

### What you'll build

A four-node flow — **Start → Seed DegenGeom Path → VSPAERO Analysis → Log Polar Point → Stop** — that runs VSPAERO on a DegenGeom file at α = 4° and M = 0.2 and prints CL, CD, and L/D.

### Step-by-step

**Step 1: Create a new project**

Name it `gtkn_part23_vspaero`. If you completed T-N102, copy `wing_body_DegenGeom.csv` from that project into this project root, or run T-N102 first and use its output path directly.

**Step 2: Build the canvas**

Place: **Start** → **SeedGeomPath** (Basic Node) → **VSPAERO Analysis** → **LogPolar** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 3: Configure the VSPAERO Analysis Node**

In the **Object Inspector**:

- **degen_geom_key**: `vsp_output_path`
- **alpha**: `4.0`
- **mach**: `0.2`
- **result_key**: `vspaero_result`

**Step 4: Write SeedGeomPath**

```python
import os
from pocketflow import Node

class SeedGeomPath(Node):
    """Seeds the DegenGeom CSV path for VSPAERO."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        # Path to the DegenGeom CSV exported by the Open VSP Geometry Node
        shared["vsp_output_path"] = os.path.join(
            project_dir, "wing_body_DegenGeom.csv"
        )
        return "default"
```

**Step 5: Write LogPolar**

```python
from pocketflow import Node

class LogPolar(Node):
    """Prints the VSPAERO aero coefficients."""

    def prep(self, shared):
        return shared.get("vspaero_result", {})

    def exec(self, prep_res):
        r = prep_res
        cl   = r.get("CL", "?")
        cd   = r.get("CD", "?")
        cm   = r.get("CMy", "?")
        e    = r.get("e", "?")
        aoa  = r.get("alpha", "?")
        mach = r.get("mach", "?")

        ld = cl / cd if isinstance(cl, (int, float)) and isinstance(cd, (int, float)) and cd != 0 else "?"

        print("=== VSPAERO Analysis Results ===")
        print(f"  α = {aoa}°,  M = {mach}")
        print(f"  CL    : {cl}")
        print(f"  CD    : {cd}")
        print(f"  CMy   : {cm}  (pitching moment)")
        print(f"  L/D   : {ld:.2f}" if isinstance(ld, float) else f"  L/D   : {ld}")
        print(f"  e     : {e}  (span efficiency)")
        return r

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. VSPAERO runs (typically < 5 seconds for a simple wing-body model) and the Run Log shows CL, CD, L/D, and span efficiency at α = 4°, M = 0.2.

**Step 7: Build an alpha sweep using a Batch Node**

To generate a complete polar, replace the single `SeedGeomPath → VSPAERO Analysis` pattern with a **Batch Node** that iterates over `alpha` values:

1. In `SeedGeomPath`, set `shared["alpha_sweep"] = [-2, 0, 2, 4, 6, 8, 10, 12]`.
2. Replace the VSPAERO Analysis Node with a **Batch Node** that iterates over `alpha_sweep`.
3. Inside the Batch Node's `exec()`, call the VSPAERO node with each alpha value.
4. Collect the results list in a downstream Reduce Node.

### What you learned

- The VSPAERO Analysis Node wraps the VSPAERO solver for rapid subsonic conceptual aerodynamics
- Configure `alpha`, `mach`, and `degen_geom_key` in the inspector — no custom node code needed
- The result dict contains `CL`, `CD`, `CMy`, `e`, `alpha`, and `mach`
- Chain directly from the Open VSP Geometry Node by sharing the `output_path_key` / `degen_geom_key`
- Use a Batch Node to sweep alpha and build a full CL–CD polar

---

## Tutorial T-N104: The SU2 CFD Node

### What it does

The **SU2 CFD Node** runs SU2_CFD — the open-source multiphysics CFD solver from Stanford University — on a user-supplied SU2 configuration (`.cfg`) file and mesh. It monitors the residual history file (`history.dat`) to extract convergence data and reports the converged lift, drag, and moment coefficients. SU2 supports Euler, RANS, and other PDE systems, making it suitable for both inviscid and viscous aerodynamic simulations.

### Use cases

- Running a 2D NACA airfoil analysis at transonic speeds where VSPAERO is not valid
- Automating a 3D wing CFD analysis loop that varies angle of attack or Mach number
- Extracting drag polars for use in mission analysis or performance sizing
- Performing adjoint-based sensitivity analysis for gradient-based aerodynamic shape optimisation

### What you'll build

A four-node flow — **Start → Seed Config Path → SU2 CFD → Log Aero Coefficients → Stop** — that runs the SU2 NACA 0012 tutorial case (inviscid Euler, M = 0.8, α = 1.25°) and logs the converged CL and CD.

### Step-by-step

**Step 1: Install SU2**

Download SU2 from https://su2code.github.io/ and add `SU2_CFD` to your PATH. Verify with `SU2_CFD -h`.

**Step 2: Set up the tutorial case**

The SU2 distribution includes the NACA 0012 tutorial case. Copy the `TestCases/euler/naca0012/` directory (containing `inv_NACA0012.cfg` and `mesh_NACA0012_inv.su2`) into your project root as `su2_naca0012/`.

**Step 3: Create a new project**

Name it `gtkn_part23_su2`.

**Step 4: Build the canvas**

Place: **Start** → **SeedConfigPath** (Basic Node) → **SU2 CFD** → **LogCoefficients** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 5: Configure the SU2 CFD Node**

In the **Object Inspector**:

- **config_path_key**: `su2_config_path`
- **nprocs**: `1` (serial run; increase for parallel if OpenMPI is installed)
- **result_key**: `su2_result`

**Step 6: Write SeedConfigPath**

```python
import os
from pocketflow import Node

class SeedConfigPath(Node):
    """Seeds the SU2 configuration file path."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        shared["su2_config_path"] = os.path.join(
            project_dir, "su2_naca0012", "inv_NACA0012.cfg"
        )
        return "default"
```

**Step 7: Write LogCoefficients**

```python
from pocketflow import Node

class LogCoefficients(Node):
    """Logs the converged SU2 aerodynamic coefficients."""

    def prep(self, shared):
        return shared.get("su2_result", {})

    def exec(self, prep_res):
        r = prep_res
        cl   = r.get("CL", "?")
        cd   = r.get("CD", "?")
        cm   = r.get("CMy", "?")
        iters = r.get("iterations", "?")
        conv  = r.get("converged", False)
        residual = r.get("final_residual", "?")

        ld = cl / cd if isinstance(cl, float) and isinstance(cd, float) and cd != 0 else "?"

        print("=== SU2 CFD Results — NACA 0012 Euler ===")
        print(f"  Converged   : {conv}")
        print(f"  Iterations  : {iters}")
        print(f"  Final Res.  : {residual:.2e}" if isinstance(residual, float) else f"  Final Res.  : {residual}")
        print(f"  CL          : {cl}")
        print(f"  CD          : {cd}")
        print(f"  CMy         : {cm}")
        print(f"  L/D         : {ld:.2f}" if isinstance(ld, float) else f"  L/D         : {ld}")
        return r

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. SU2_CFD runs the NACA 0012 Euler case (typically 30–90 seconds to convergence). The Run Log shows iteration residuals streaming in from SU2, followed by the final converged CL and CD. Expected values for this case are approximately CL ≈ 0.34, CD ≈ 0.022 at M = 0.8, α = 1.25°.

> 💡 **Tip:** To run a Mach sweep, put the `SeedConfigPath → SU2 CFD` pair inside a Batch Node and modify the `MACH_NUMBER` line in the `.cfg` file programmatically before each run using Python's `re.sub()` in a Python Tool Node.

### What you learned

- The SU2 CFD Node runs SU2_CFD with a user-supplied `.cfg` file and mesh
- The result dict contains `CL`, `CD`, `CMy`, `iterations`, `converged`, and `final_residual`
- The `nprocs` property enables parallel runs when OpenMPI is available
- Chain with a Batch Node to automate multi-point polar generation
- The `.cfg` file controls all physical settings (Mach, AoA, turbulence model, solver type)

---

## Tutorial T-N105: The Cart3D Analysis Node

### What it does

The **Cart3D Analysis Node** runs a NASA Cart3D inviscid Euler CFD analysis. Cart3D uses a Cartesian mesh approach — it automatically generates an adaptive Cartesian mesh from a closed triangulated surface (STL or `.tri` file) — making it excellent for rapid inviscid aerodynamic analysis of complex geometries without manual meshing. The node runs the Cart3D pipeline (`autoCart` or equivalent) and returns the integrated aerodynamic force and moment coefficients.

### Use cases

- Rapid inviscid aerodynamic analysis of aircraft configurations at subsonic and transonic speeds
- Comparing aerodynamic performance of design variants in an automated geometry sweep
- Computing interference effects between wing, fuselage, and nacelle using complex geometry
- Producing CL/CD/CM coefficients for performance sizing when viscous effects are secondary

### What you'll build

A four-node flow — **Start → Seed Case Directory → Cart3D Analysis → Log Coefficients → Stop** — that runs Cart3D on a pre-configured case directory containing a surface mesh and sets up file and reports CL, CD, and CM.

### Step-by-step

**Step 1: Install Cart3D**

Cart3D is available from https://www.nas.nasa.gov/software/cart3d.html (requires a NASA software request). After installation, confirm that `autoCart.py` (or the `cart3d` entry point) is on your PATH.

**Step 2: Prepare a case directory**

Create `cart3d_case/` in the project root. Inside it, place:

- `Components.i.tri` — your triangulated surface geometry (STL or `.tri` format)
- `input.cntl` — Cart3D control file (sets Mach, AoA, Reynolds number, etc.)

The Cart3D distribution includes example cases. Use `ONERAM6/` or `wing_body/` from the Cart3D tutorials.

**Step 3: Create a new project**

Name it `gtkn_part23_cart3d`.

**Step 4: Build the canvas**

Place: **Start** → **SeedCaseDir** (Basic Node) → **Cart3D Analysis** → **LogCoeffs** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 5: Configure the Cart3D Analysis Node**

In the **Object Inspector**:

- **case_dir_key**: `cart3d_case_dir`
- **aoa**: `2.0` (angle of attack in degrees — overrides `input.cntl` if supported)
- **mach**: `0.5`
- **result_key**: `cart3d_result`

**Step 6: Write SeedCaseDir**

```python
import os
from pocketflow import Node

class SeedCaseDir(Node):
    """Seeds the Cart3D case directory path."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        shared["cart3d_case_dir"] = os.path.join(project_dir, "cart3d_case")
        return "default"
```

**Step 7: Write LogCoeffs**

```python
from pocketflow import Node

class LogCoeffs(Node):
    """Logs Cart3D aerodynamic coefficients."""

    def prep(self, shared):
        return shared.get("cart3d_result", {})

    def exec(self, prep_res):
        r = prep_res
        cl  = r.get("CL", "?")
        cd  = r.get("CD", "?")
        cm  = r.get("CM", "?")
        aoa = r.get("alpha", "?")

        ld = cl / cd if isinstance(cl, float) and isinstance(cd, float) and cd != 0 else "?"

        print("=== Cart3D Euler CFD Results ===")
        print(f"  α = {aoa}°")
        print(f"  CL  : {cl}")
        print(f"  CD  : {cd}")
        print(f"  CM  : {cm}")
        print(f"  L/D : {ld:.2f}" if isinstance(ld, float) else f"  L/D : {ld}")
        return r

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. Cart3D runs mesh generation and the Euler flow solver. Runtime varies from seconds (coarse mesh) to minutes (refined adaptive mesh). The Run Log streams Cart3D output, and `LogCoeffs` prints the converged force coefficients.

### What you learned

- The Cart3D Analysis Node runs the NASA Cart3D Euler CFD pipeline from a case directory
- Cart3D automatically meshes from a triangulated surface — no manual meshing required
- The result dict contains `CL`, `CD`, `CM`, and `alpha`
- Configure `aoa` and `mach` in the inspector to override the case control file values
- Cart3D is best for rapid inviscid aerodynamic assessment of complex geometries

---

## Tutorial T-N106: The FUN3D Run Node

### What it does

The **FUN3D Run Node** executes a NASA FUN3D CFD case — a high-fidelity Reynolds-Averaged Navier-Stokes (RANS) or Large Eddy Simulation (LES) solver. FUN3D uses unstructured meshes and supports adjoint-based sensitivity analysis, making it suitable for high-fidelity aerodynamic shape optimisation. The node runs `nodet_mpi` (or `nodet` in serial) inside a pre-configured case directory containing `fun3d.nml`, the grid file, and boundary conditions.

### Use cases

- High-fidelity RANS aerodynamic analysis of wing or full-aircraft configurations
- Computing adjoint sensitivities for gradient-based aerodynamic shape optimisation
- Simulating unsteady flows (buffet, dynamic stall) that require time-accurate methods
- Validating conceptual aerodynamic predictions against higher-fidelity computations

### What you'll build

A four-node flow — **Start → Seed Case Directory → FUN3D Run → Log Forces → Stop** — that runs a steady RANS computation and logs converged lift and drag coefficients from the `history.dat` file.

### Step-by-step

**Step 1: Install FUN3D**

FUN3D is available to US government entities and their contractors from https://fun3d.larc.nasa.gov/. Compile `nodet_mpi` and confirm it is on your PATH. FUN3D requires MPI (e.g., OpenMPI).

**Step 2: Prepare a FUN3D case directory**

Create `fun3d_case/` in the project root. It must contain:

- `fun3d.nml` — the FUN3D namelist (controls physics, solver settings, I/O)
- A grid file (`.ugrid` or `.b8.ugrid` format) linked or copied into the directory
- Boundary condition files as required by the namelist

Use the 2D NACA 0012 FUN3D tutorial case from the FUN3D distribution for a quick start.

**Step 3: Create a new project**

Name it `gtkn_part23_fun3d`.

**Step 4: Build the canvas**

Place: **Start** → **SeedCaseDir** (Basic Node) → **FUN3D Run** → **LogForces** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 5: Configure the FUN3D Run Node**

In the **Object Inspector**:

- **case_dir_key**: `fun3d_case_dir`
- **nprocs**: `4`
- **result_key**: `fun3d_result`

**Step 6: Write SeedCaseDir**

```python
import os
from pocketflow import Node

class SeedCaseDir(Node):
    """Seeds the FUN3D case directory path."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        shared["fun3d_case_dir"] = os.path.join(project_dir, "fun3d_case")
        return "default"
```

**Step 7: Write LogForces**

```python
from pocketflow import Node

class LogForces(Node):
    """Logs converged FUN3D aerodynamic force coefficients."""

    def prep(self, shared):
        return shared.get("fun3d_result", {})

    def exec(self, prep_res):
        r     = prep_res
        cl    = r.get("CL", "?")
        cd    = r.get("CD", "?")
        cm    = r.get("CM", "?")
        iters = r.get("iterations", "?")
        conv  = r.get("converged", False)

        ld = cl / cd if isinstance(cl, float) and isinstance(cd, float) and cd != 0 else "?"

        print("=== FUN3D RANS Results ===")
        print(f"  Converged  : {conv}")
        print(f"  Iterations : {iters}")
        print(f"  CL         : {cl}")
        print(f"  CD         : {cd}")
        print(f"  CM         : {cm}")
        print(f"  L/D        : {ld:.2f}" if isinstance(ld, float) else f"  L/D        : {ld}")

        # Report convergence history summary
        history = r.get("residual_history", [])
        if history:
            print(f"\n  Residual: {history[0]:.2e} → {history[-1]:.2e}  "
                  f"({len(history)} iterations)")
        return r

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. FUN3D runs the RANS simulation with 4 MPI processes. Expect runtime of 5–30 minutes depending on mesh size and convergence criteria. The Run Log streams `nodet_mpi` output including residual history, and `LogForces` prints the final converged coefficients.

> 💡 **Tip:** FUN3D RANS simulations are expensive. During development, reduce the `ITER` count in `fun3d.nml` to 50–100 iterations just to confirm the PocketFlow node integration works before running to full convergence.

### What you learned

- The FUN3D Run Node requires a pre-configured FUN3D case directory with `fun3d.nml` and a grid file
- Set `nprocs` to the number of MPI processes available on your machine
- The result dict contains `CL`, `CD`, `CM`, `iterations`, `converged`, and `residual_history`
- FUN3D RANS runs take minutes to hours — plan for this when designing production pipelines
- Use the Retry Node upstream to automatically re-start runs that diverge due to poor initial conditions

---

[← Previous Part: Weather, Atmosphere and Building Energy](gtkn_part22.md)  
[→ Next Part: Aerospace Propulsion, MDO and Mission](gtkn_part24.md)  
[↑ Series Index](gtkn_index.md)  
[↑ Tutorials Index](index.md)
