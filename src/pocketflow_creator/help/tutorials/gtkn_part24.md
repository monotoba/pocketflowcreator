# Part 24 — Aerospace Propulsion, MDO, and Mission Addon Nodes

Part 24 covers six aerospace addon nodes focused on propulsion analysis, multidisciplinary design optimisation (MDO), and mission/trajectory simulation: **NASA CEA**, **RocketPy Flight**, **GMAT Script**, **OpenMDAO Model**, **Optimization**, and **NASA Trick Simulation**. Together these nodes span the design process from propellant selection (CEA) through trajectory simulation (RocketPy, GMAT) and system-level MDO (OpenMDAO, Optimization) to full simulation framework execution (Trick).

---

## Tutorial T-N107: The NASA CEA Node

### What it does

The **NASA CEA Node** computes rocket engine combustion thermochemical properties using the NASA Chemical Equilibrium with Applications (CEA) code via the `rocketcea` Python wrapper. Given an oxidiser, fuel, and chamber pressure, it returns specific impulse (Isp), chamber temperature (Tc), specific heat ratio (γ), and molecular weight (MW) for the combustion products. These are the fundamental inputs for nozzle design and mission Δv budget calculations.

### Use cases

- Comparing Isp for a range of propellant combinations (LOX/LH2, LOX/RP-1, N2O4/UDMH)
- Computing nozzle area ratio for a given expansion pressure ratio
- Sensitivity analysis of Isp to mixture ratio (O/F) for propellant budget optimisation
- Generating combustion property tables as input to engine cycle analysis

### What you'll build

A four-node flow — **Start → Seed Propellant Config → NASA CEA → Log Combustion Properties → Stop** — that computes vacuum Isp, chamber temperature, and γ for three propellant pairs and prints a comparison table.

### Step-by-step

**Step 1: Install rocketcea**

```bash
pip install rocketcea
```

Verify: `python -c "from rocketcea.cea_obj import CEA_Obj; print('OK')"`. The `rocketcea` package bundles the CEA executable — no separate installation is needed.

**Step 2: Create a new project**

Name it `gtkn_part24_nasa_cea`.

**Step 3: Build the canvas**

Place: **Start** → **SeedPropellant** (Basic Node) → **NASA CEA** → **LogProperties** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 4: Configure the NASA CEA Node**

In the **Object Inspector**:

- **oxid**: `LOX`
- **fuel**: `LH2`
- **pc_psia**: `1000`
- **eps** *(expansion ratio, optional)*: `40`
- **of_ratio**: `6.0` (oxidiser-to-fuel mass ratio)
- **result_key**: `cea_result`

> 💡 **Tip:** Valid oxidiser names include `LOX`, `N2O4`, `IRFNA`, `F2`, `ClF5`. Valid fuel names include `LH2`, `RP1`, `MMH`, `UDMH`, `Methane`, `Ethanol`. These are CEA-specific identifiers — see the `rocketcea` documentation for the full list.

**Step 5: Write SeedPropellant**

This tutorial computes a single point rather than a sweep. The node properties already define the propellant combination; `SeedPropellant` just confirms the configuration is ready.

```python
from pocketflow import Node

class SeedPropellant(Node):
    """Confirms propellant configuration (set in node properties)."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        # The propellant combination is configured in the CEA node's
        # Object Inspector properties (oxid, fuel, pc_psia, of_ratio).
        # This node could be used to override those properties dynamically
        # by writing to the shared store keys the node reads.
        print("Propellant: LOX / LH2,  O/F = 6.0,  Pc = 1000 psia")
        return None

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 6: Write LogProperties**

```python
from pocketflow import Node

class LogProperties(Node):
    """Prints the NASA CEA combustion properties."""

    def prep(self, shared):
        return shared.get("cea_result", {})

    def exec(self, prep_res):
        r = prep_res
        print("=== NASA CEA Combustion Properties ===")
        print(f"  Propellants  : {r.get('oxid', '?')} / {r.get('fuel', '?')}")
        print(f"  O/F ratio    : {r.get('of_ratio', '?')}")
        print(f"  Pc           : {r.get('pc_psia', '?')} psia")
        print(f"  Vacuum Isp   : {r.get('Isp_vac', '?'):.1f} s")
        print(f"  Delivered Isp: {r.get('Isp_del', '?'):.1f} s  (ε = {r.get('eps', '?')})")
        print(f"  T_chamber    : {r.get('T_chamber_K', '?'):.0f} K")
        print(f"  γ (gamma)    : {r.get('gamma', '?'):.4f}")
        print(f"  Mol. weight  : {r.get('MW', '?'):.2f} g/mol")
        print(f"  C* efficiency: {r.get('cstar', '?'):.1f} m/s")
        return r

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 7: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. CEA runs in milliseconds. The Run Log should show vacuum Isp ≈ 451 s for LOX/LH2 at Pc = 1000 psia, O/F = 6.0, ε = 40 — consistent with published values for the Space Shuttle Main Engine propellant combination.

**Step 8: Compare propellant pairs using a Batch Node**

To compare multiple propellant combinations, insert a **Batch Node** before the CEA node:

1. In `SeedPropellant`, write `shared["propellant_pairs"] = [("LOX","LH2",6.0), ("LOX","RP1",2.7), ("N2O4","MMH",1.65)]`.
2. Replace the NASA CEA Node with a Batch Node that iterates over `propellant_pairs`.
3. Inside the Batch exec, override `oxid`, `fuel`, and `of_ratio` in the shared store and call the CEA node.
4. Collect results in a Reduce Node and use an LLM Prompt Node to rank the propellant pairs by Isp.

### What you learned

- The NASA CEA Node uses `rocketcea` — no separate CEA installation needed
- Configure `oxid`, `fuel`, `pc_psia`, `of_ratio`, and `eps` in the Object Inspector
- The result dict contains `Isp_vac`, `Isp_del`, `T_chamber_K`, `gamma`, `MW`, and `cstar`
- CEA runs in milliseconds — ideal for use inside Batch Node loops for propellant trade studies
- Valid oxidiser/fuel names are CEA identifiers (see `rocketcea` docs for the full catalogue)

---

## Tutorial T-N108: The RocketPy Flight Node

### What it does

The **RocketPy Flight Node** runs a RocketPy 6-degree-of-freedom rocket flight simulation and returns key performance metrics: apogee altitude, maximum speed, flight time, and maximum acceleration. Unlike the other simulation nodes, the RocketPy Flight Node accepts a fully configured `rocketpy.Flight` object that you construct in a preceding Basic Node — this gives you full access to all RocketPy rocket, motor, and environment parameters from Python.

### Use cases

- Computing apogee altitude for a sounding rocket design to verify target performance
- Simulating the effect of wind speed on apogee for range safety analysis
- Performing Monte Carlo dispersion analysis by wrapping the Flight node in a Batch Node
- Optimising motor burnout time and nozzle diameter using the Optimization Node (next tutorial)

### What you'll build

A four-node flow — **Start → Build Flight Object → RocketPy Flight → Log Results → Stop** — that simulates the flight of a simple two-stage sounding rocket and reports apogee, max speed, and flight time.

### Step-by-step

**Step 1: Install RocketPy**

```bash
pip install rocketpy
```

**Step 2: Create a new project**

Name it `gtkn_part24_rocketpy`.

**Step 3: Build the canvas**

Place: **Start** → **BuildFlight** (Basic Node) → **RocketPy Flight** → **LogResults** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 4: Configure the RocketPy Flight Node**

In the **Object Inspector**:

- **flight_key**: `rocketpy_flight`
- **result_key**: `rocketpy_result`

**Step 5: Write BuildFlight**

```python
from pocketflow import Node

class BuildFlight(Node):
    """Constructs a RocketPy Flight object for a simple sounding rocket."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        import rocketpy
        from rocketpy import Environment, SolidMotor, Rocket, Flight

        # --- Environment ---
        env = Environment(latitude=32.990254, longitude=-106.974998, elevation=1400)
        # Use a simple wind profile (ISA + 10 kt surface wind from north)
        env.set_atmospheric_model(
            type="custom_atmosphere",
            wind_u=[(0, 5.14), (10000, 5.14)],
            wind_v=[(0, 0.0),  (10000, 0.0)],
        )

        # --- Solid motor (Cesaroni L1720) approximate parameters ---
        motor = SolidMotor(
            thrust_source=[(0, 0), (0.1, 1720), (2.5, 1720), (2.6, 0)],
            dry_mass=1.5,
            dry_inertia=(0.125, 0.125, 0.002),
            nozzle_radius=0.033,
            grain_number=5,
            grain_density=1815,
            grain_outer_radius=0.033,
            grain_initial_inner_radius=0.015,
            grain_initial_height=0.120,
            grain_separation=0.005,
            grains_center_of_mass_position=0.397,
            center_of_dry_mass_position=0.317,
            nozzle_position=0.0,
            burn_time=2.5,
            throat_radius=0.011,
            coordinate_system_orientation="nozzle_to_combustion_chamber",
        )

        # --- Rocket ---
        rocket = Rocket(
            radius=0.0635,
            mass=10.0,
            inertia=(6.321, 6.321, 0.034),
            power_off_drag="powerOffDragCurve.csv",
            power_on_drag="powerOnDragCurve.csv",
            center_of_mass_without_motor=0,
            coordinate_system_orientation="tail_to_nose",
        )
        rocket.add_motor(motor, position=-1.255)
        rocket.add_nose(length=0.55, kind="vonKarman", position=1.278)
        rocket.add_fins(
            n=4, root_chord=0.120, tip_chord=0.060,
            span=0.110, position=-1.04
        )

        # --- Flight ---
        flight = Flight(
            rocket=rocket,
            environment=env,
            rail_length=5.2,
            inclination=85,
            heading=0,
            terminate_on_apogee=True,
        )

        return flight

    def post(self, shared, prep_res, exec_res):
        shared["rocketpy_flight"] = exec_res
        return "default"
```

> ⚠️ **Note:** The drag curve files (`powerOffDragCurve.csv`, `powerOnDragCurve.csv`) are required by RocketPy. For this tutorial, you can use the example files from the RocketPy `tests/fixtures/` directory, or create minimal CSV files with two columns (Mach, Cd) covering Mach 0–3.

**Step 6: Write LogResults**

```python
from pocketflow import Node

class LogResults(Node):
    """Prints the RocketPy flight simulation results."""

    def prep(self, shared):
        return shared.get("rocketpy_result", {})

    def exec(self, prep_res):
        r = prep_res
        print("=== RocketPy Flight Simulation Results ===")
        print(f"  Apogee altitude : {r.get('apogee_m', '?'):.0f} m AGL")
        print(f"  Max speed       : {r.get('max_speed_ms', '?'):.1f} m/s "
              f"({r.get('max_mach', '?'):.3f} Mach)")
        print(f"  Max acceleration: {r.get('max_accel_ms2', '?'):.1f} m/s²")
        print(f"  Flight time     : {r.get('flight_time_s', '?'):.1f} s")
        print(f"  Time to apogee  : {r.get('apogee_time_s', '?'):.1f} s")
        return r

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 7: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The flight simulation runs (typically < 5 seconds). The Run Log reports apogee, maximum speed, and flight time. Adjust motor thrust or rocket mass in `BuildFlight` and re-run to see how the performance metrics change.

### What you learned

- The RocketPy Flight Node accepts a `rocketpy.Flight` object constructed in a preceding Basic Node
- Build the full RocketPy model (environment, motor, rocket, flight) in Python before passing it to the node
- The result dict contains `apogee_m`, `max_speed_ms`, `max_mach`, `max_accel_ms2`, `flight_time_s`, and `apogee_time_s`
- Wrap the `BuildFlight → RocketPy Flight` pair inside a Batch Node to perform Monte Carlo dispersion analysis

---

## Tutorial T-N109: The GMAT Script Node

### What it does

The **GMAT Script Node** runs a NASA General Mission Analysis Tool (GMAT) script file and optionally reads a GMAT-generated report file to return numerical results. GMAT is the standard open-source tool for orbital mechanics and astrodynamics: orbit propagation, manoeuvre planning, coverage analysis, and trajectory optimisation. The node invokes the GMAT executable in headless (batch) mode and parses the output report.

### Use cases

- Computing Δv for a Hohmann transfer between two circular orbits
- Propagating a satellite orbit and reporting ground track coverage statistics
- Automating GMAT Monte Carlo analyses for launch window analysis
- Extracting burn time and propellant mass from a multi-burn trajectory optimisation

### What you'll build

A four-node flow — **Start → Seed Script Path → GMAT Script → Log Delta-V → Stop** — that runs a GMAT script defining a Hohmann transfer from LEO (400 km) to a 600 km circular orbit and logs the two burn Δv values.

### Step-by-step

**Step 1: Install GMAT**

Download GMAT from https://gmat.gsfc.nasa.gov/. After installation, confirm that the GMAT executable (`GMAT` or `GMAT-R2022a`) is on your PATH or note its full path.

**Step 2: Create the GMAT script**

Create `hohmann.script` in your project root. A minimal Hohmann transfer script:

```gmat
%  Hohmann Transfer: 400 km → 600 km circular LEO
%  Results written to hohmann_report.txt

Create Spacecraft SC;
GMAT SC.DateFormat = UTCGregorian;
GMAT SC.Epoch = '01 Jan 2025 00:00:00.000';
GMAT SC.SMA = 6778.137;   % 400 km altitude
GMAT SC.ECC = 0.0;
GMAT SC.INC = 28.5;
GMAT SC.RAAN = 0.0;
GMAT SC.AOP = 0.0;
GMAT SC.TA = 0.0;

Create ImpulsiveBurn Burn1;
GMAT Burn1.CoordinateSystem = Local;
GMAT Burn1.Origin = Earth;
GMAT Burn1.Axes = VNB;
GMAT Burn1.Element1 = 0.0;

Create ImpulsiveBurn Burn2;
GMAT Burn2.CoordinateSystem = Local;
GMAT Burn2.Origin = Earth;
GMAT Burn2.Axes = VNB;
GMAT Burn2.Element1 = 0.0;

Create Propagator Prop;

Create ReportFile Report1;
GMAT Report1.Filename = 'hohmann_report.txt';
GMAT Report1.Add = {SC.ElapsedSecs, SC.SMA, Burn1.Element1, Burn2.Element1};

BeginMissionSequence;

% Calculate and apply Burn 1 (periapsis raise)
GMAT Burn1.Element1 = 0.1122;  % km/s — approximate for this transfer
Maneuver Burn1(SC);
Propagate Prop(SC) {SC.Earth.Apoapsis};

% Calculate and apply Burn 2 (circularise at apoapsis)
GMAT Burn2.Element1 = 0.1122;  % km/s — approximate
Maneuver Burn2(SC);
Propagate Prop(SC) {SC.ElapsedSecs = 3600};

Report Report1 SC.ElapsedSecs SC.SMA Burn1.Element1 Burn2.Element1;
```

Save as `hohmann.script` in the project root.

**Step 3: Create a new project**

Name it `gtkn_part24_gmat`.

**Step 4: Build the canvas**

Place: **Start** → **SeedScriptPath** (Basic Node) → **GMAT Script** → **LogDeltaV** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 5: Configure the GMAT Script Node**

In the **Object Inspector**:

- **script_path_key**: `gmat_script_path`
- **report_path_key**: `gmat_report_path`
- **result_key**: `gmat_result`

**Step 6: Write SeedScriptPath**

```python
import os
from pocketflow import Node

class SeedScriptPath(Node):
    """Seeds the GMAT script and report file paths."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        shared["gmat_script_path"] = os.path.join(project_dir, "hohmann.script")
        shared["gmat_report_path"] = os.path.join(project_dir, "hohmann_report.txt")
        return "default"
```

**Step 7: Write LogDeltaV**

```python
from pocketflow import Node

class LogDeltaV(Node):
    """Logs the GMAT Hohmann transfer results."""

    def prep(self, shared):
        return shared.get("gmat_result", {})

    def exec(self, prep_res):
        r = prep_res
        report_rows = r.get("report_data", [])

        print("=== GMAT Hohmann Transfer Results ===")
        print(f"  Script      : {r.get('script_path', '?')}")
        print(f"  GMAT status : {r.get('status', '?')}")

        if report_rows:
            last = report_rows[-1]
            elapsed = last.get("SC.ElapsedSecs", "?")
            sma     = last.get("SC.SMA", "?")
            dv1     = last.get("Burn1.Element1", "?")
            dv2     = last.get("Burn2.Element1", "?")
            print(f"\n  Transfer results:")
            print(f"    Elapsed time : {elapsed} s")
            print(f"    Final SMA    : {sma} km")
            print(f"    Δv₁ (raise)  : {dv1} km/s")
            print(f"    Δv₂ (circul) : {dv2} km/s")
            if isinstance(dv1, float) and isinstance(dv2, float):
                total = abs(dv1) + abs(dv2)
                print(f"    Total Δv     : {total:.4f} km/s")
        else:
            print("  (No report data — check GMAT output)")
        return r

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. GMAT runs in batch mode, executes the Hohmann transfer sequence, and writes `hohmann_report.txt`. The GMAT Script Node parses the report and the Run Log shows total Δv ≈ 0.224 km/s for this 400→600 km transfer.

### What you learned

- The GMAT Script Node runs GMAT in headless batch mode with a `.script` file
- Configure `script_path_key` and `report_path_key` — the node parses the report file and returns `report_data` as a list of row dicts
- GMAT scripts use the GMAT script language; any valid GMAT scenario can be driven this way
- Use with a Batch Node to sweep launch windows or orbit parameters

---

## Tutorial T-N110: The OpenMDAO Model Node

### What it does

The **OpenMDAO Model Node** executes a NASA OpenMDAO multidisciplinary analysis or optimisation problem. You construct the `openmdao.api.Problem` object in a preceding Basic Node using the standard OpenMDAO Python API, then pass it to this node. The node calls either `problem.run_model()` (analysis only) or `problem.run_driver()` (full optimisation), and returns the values of all design variables and objectives.

### Use cases

- Performing coupled multidisciplinary analysis (MDA) of a wing with aerodynamic and structural disciplines
- Running gradient-based MDO using an OpenMDAO SLSQP or COBYLA driver
- Computing adjoint sensitivities across a discipline chain for gradient validation
- Building a design space exploration pipeline that varies design variables and calls `run_model()`

### What you'll build

A four-node flow — **Start → Build OpenMDAO Problem → OpenMDAO Model → Log Optimum → Stop** — that constructs and solves a simple Sellar MDO problem using the default SLSQP optimizer and logs the optimal design variables.

### Step-by-step

**Step 1: Install OpenMDAO**

```bash
pip install openmdao[all]
```

Verify: `python -c "import openmdao.api as om; print(om.__version__)"`.

**Step 2: Create a new project**

Name it `gtkn_part24_openmdao`.

**Step 3: Build the canvas**

Place: **Start** → **BuildProblem** (Basic Node) → **OpenMDAO Model** → **LogOptimum** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 4: Configure the OpenMDAO Model Node**

In the **Object Inspector**:

- **problem_key**: `openmdao_problem`
- **driver**: `run_driver` (run the full optimisation, not just analysis)
- **result_key**: `openmdao_result`

**Step 5: Write BuildProblem**

```python
from pocketflow import Node
import openmdao.api as om

class BuildProblem(Node):
    """Builds the Sellar MDO problem — the canonical OpenMDAO example."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        # ── Sellar disciplines ────────────────────────────────────────
        class SellarDis1(om.ExplicitComponent):
            def setup(self):
                self.add_input("z", val=[5.0, 2.0])
                self.add_input("x", val=1.0)
                self.add_input("y2", val=12.05)
                self.add_output("y1", val=25.58)

            def setup_partials(self):
                self.declare_partials("*", "*", method="fd")

            def compute(self, inputs, outputs):
                z1, z2 = inputs["z"]
                x = inputs["x"]
                y2 = inputs["y2"]
                outputs["y1"] = z1**2 + z2 + x - 0.2 * y2

        class SellarDis2(om.ExplicitComponent):
            def setup(self):
                self.add_input("z", val=[5.0, 2.0])
                self.add_input("y1", val=12.05)
                self.add_output("y2", val=12.05)

            def setup_partials(self):
                self.declare_partials("*", "*", method="fd")

            def compute(self, inputs, outputs):
                z1, z2 = inputs["z"]
                y1 = inputs["y1"]
                outputs["y2"] = y1**0.5 + z1 + z2

        # ── Assemble the problem ────────────────────────────────────
        prob = om.Problem()
        model = prob.model
        model.add_subsystem("d1", SellarDis1(), promotes=["*"])
        model.add_subsystem("d2", SellarDis2(), promotes=["*"])

        # Objective: minimise  x**2 + z2 + y1 + e^(-y2)
        exec_comp = om.ExecComp("obj = x**2 + z[1] + y1 + exp(-y2)")
        model.add_subsystem("obj_cmp", exec_comp, promotes=["*"])

        # Constraint: y1 ≥ 3.16, y2 = 24.0
        con1 = om.ExecComp("con1 = 3.16 - y1")
        con2 = om.ExecComp("con2 = y2 - 24.0")
        model.add_subsystem("con_cmp1", con1, promotes=["*"])
        model.add_subsystem("con_cmp2", con2, promotes=["*"])

        # Non-linear solver for MDA coupling
        model.nonlinear_solver = om.NewtonSolver(solve_subsystems=False)
        model.linear_solver    = om.DirectSolver()

        # SLSQP optimiser
        prob.driver = om.ScipyOptimizeDriver(optimizer="SLSQP")

        # Design variables
        model.add_design_var("x",  lower=0.0, upper=10.0)
        model.add_design_var("z",  lower=[-10.0, 0.0], upper=[10.0, 10.0])

        # Objective and constraints
        model.add_objective("obj")
        model.add_constraint("con1", upper=0.0)
        model.add_constraint("con2", equals=0.0)

        prob.setup()
        # Starting point
        prob.set_val("x", 1.0)
        prob.set_val("z", [5.0, 2.0])

        return prob

    def post(self, shared, prep_res, exec_res):
        shared["openmdao_problem"] = exec_res
        return "default"
```

**Step 6: Write LogOptimum**

```python
from pocketflow import Node

class LogOptimum(Node):
    """Logs the Sellar MDO optimum values."""

    def prep(self, shared):
        return shared.get("openmdao_result", {})

    def exec(self, prep_res):
        r = prep_res
        dvs = r.get("design_variables", {})
        obj = r.get("objectives", {})
        con = r.get("constraints", {})

        print("=== OpenMDAO Sellar MDO Optimum ===")
        print(f"  Driver converged : {r.get('converged', '?')}")
        print(f"\n  Design Variables:")
        for name, val in dvs.items():
            print(f"    {name:10s} = {val}")
        print(f"\n  Objective:")
        for name, val in obj.items():
            print(f"    {name:10s} = {val:.6f}")
        print(f"\n  Constraints:")
        for name, val in con.items():
            print(f"    {name:10s} = {val:.6f}")
        print(f"\n  (Expected: x≈0, z≈[1.977, 0], obj≈3.18)")
        return r

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 7: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The SLSQP optimiser converges in a few seconds. The Run Log shows the optimal design variables (x ≈ 0, z ≈ [1.977, 0]) and objective value (≈ 3.18) — the well-known Sellar MDO optimum.

### What you learned

- The OpenMDAO Model Node accepts a `Problem` object and calls `run_model()` or `run_driver()`
- Build the full OpenMDAO problem in a preceding Basic Node using the standard OpenMDAO API
- The result dict contains `design_variables`, `objectives`, `constraints`, and `converged`
- Setting `driver: run_model` performs MDA analysis without optimisation; `run_driver` runs the full optimiser

---

## Tutorial T-N111: The Optimization Node

### What it does

The **Optimization Node** minimises a scalar objective function using SciPy's `scipy.optimize.minimize` with a method of your choice (SLSQP, Nelder-Mead, BFGS, L-BFGS-B, etc.). You supply a Python callable as the objective function via the shared store, along with an initial guess vector. The node returns the optimal design variable vector, the minimum objective value, convergence status, and number of function evaluations.

### Use cases

- Minimising airfoil drag as a function of thickness and camber using an analytical surrogate
- Optimising structural mass subject to stress and deflection constraints
- Fitting model parameters to measurement data (least-squares minimisation)
- Implementing a parametric study outer loop that finds local optima across a design space

### What you'll build

A four-node flow — **Start → Seed Objective → Optimization → Log Optimum → Stop** — that minimises the Rosenbrock function (a standard test problem) to confirm the node works, then extends the example to a physically motivated airfoil drag minimisation problem.

### Step-by-step

**Step 1: Create a new project**

Name it `gtkn_part24_optimization`.

**Step 2: Build the canvas**

Place: **Start** → **SeedObjective** (Basic Node) → **Optimization** → **LogOptimum** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 3: Configure the Optimization Node**

In the **Object Inspector**:

- **objective_key**: `objective_fn`
- **x0_key**: `x0`
- **method**: `SLSQP`
- **bounds_key**: `opt_bounds`
- **constraints_key**: `opt_constraints`
- **result_key**: `opt_result`

**Step 4: Write SeedObjective**

```python
from pocketflow import Node

class SeedObjective(Node):
    """Seeds the objective function and initial guess."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # ── Rosenbrock function: global minimum at (1, 1), f = 0 ──
        def rosenbrock(x):
            return sum(100.0 * (x[i+1] - x[i]**2)**2 + (1 - x[i])**2
                       for i in range(len(x) - 1))

        shared["objective_fn"] = rosenbrock
        shared["x0"]           = [0.0, 0.0]    # starting point
        shared["opt_bounds"]   = [(-2, 2), (-2, 2)]
        shared["opt_constraints"] = []          # unconstrained

        return "default"
```

**Step 5: Write LogOptimum**

```python
from pocketflow import Node

class LogOptimum(Node):
    """Logs the optimisation result."""

    def prep(self, shared):
        return shared.get("opt_result", {})

    def exec(self, prep_res):
        r = prep_res
        x_opt   = r.get("x_optimal", "?")
        f_opt   = r.get("f_optimal", "?")
        success = r.get("success", False)
        nfev    = r.get("nfev", "?")
        msg     = r.get("message", "?")

        print("=== Optimization Results ===")
        print(f"  Method      : {r.get('method', '?')}")
        print(f"  Converged   : {success}")
        print(f"  Message     : {msg}")
        print(f"  Func evals  : {nfev}")
        print(f"\n  Optimal x   : {[round(xi, 6) for xi in x_opt] if isinstance(x_opt, list) else x_opt}")
        print(f"  f(x*)       : {f_opt:.8f}" if isinstance(f_opt, float) else f"  f(x*)       : {f_opt}")
        print(f"\n  (Rosenbrock global minimum: x=[1.0, 1.0], f=0.0)")
        return r

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The Rosenbrock minimisation converges to x ≈ [1.0, 1.0], f ≈ 0.0 in tens of iterations. Swap out `rosenbrock` in `SeedObjective` with your own engineering objective function to solve real design problems.

### What you learned

- The Optimization Node accepts any Python callable as the objective function via the shared store
- Configure `method` (SLSQP, Nelder-Mead, BFGS, L-BFGS-B, etc.) in the Object Inspector
- Supply `bounds_key` (list of (min, max) tuples) and `constraints_key` (list of SciPy constraint dicts)
- The result dict contains `x_optimal`, `f_optimal`, `success`, `nfev`, and `message`
- For multidisciplinary problems, use the OpenMDAO Model Node instead — it handles coupling and adjoint sensitivities

---

## Tutorial T-N112: The NASA Trick Simulation Node

### What it does

The **NASA Trick Simulation Node** builds and runs a NASA Trick-based simulation — a C++ simulation framework used for spacecraft, aircraft, and robotic systems. It executes `trick-CP` (the Trick compilation manager) to build the simulation executable (if needed), then runs it with a user-supplied Python input file. After the run, it reads the Trick log files (`log_*.trk` or converted CSV files) and returns the logged variable arrays.

### Use cases

- Running a Trick satellite attitude control simulation and extracting quaternion and rate data
- Automating Trick Monte Carlo runs by iterating over input file parameter variations in a Batch Node
- Building a CI/CD pipeline that compiles and runs a Trick simulation on every code commit
- Extracting performance metrics from a Trick flight dynamics simulation for trade study reporting

### What you'll build

A four-node flow — **Start → Seed Sim Directory → Trick Simulation → Log Variables → Stop** — that builds and runs the Trick `SIM_satellite` example simulation and logs the first and last values of the simulated body angular velocity.

### Step-by-step

**Step 1: Install NASA Trick**

Follow the Trick installation guide at https://github.com/nasa/trick. After installation, verify `trick-CP --version` in a terminal. The `SIM_satellite` example is in `trick_sims/SIM_satellite/` inside the Trick distribution.

**Step 2: Copy the SIM_satellite directory**

Copy `trick_sims/SIM_satellite/` into your project root. This directory contains `S_define`, `RUN_test/input.py`, and the simulation source code.

**Step 3: Create a new project**

Name it `gtkn_part24_trick`.

**Step 4: Build the canvas**

Place: **Start** → **SeedSimDir** (Basic Node) → **Trick Simulation** → **LogVariables** (Basic Node) → **Stop**.

Wire all ports including `error` to Stop.

**Step 5: Configure the Trick Simulation Node**

In the **Object Inspector**:

- **sim_dir_key**: `trick_sim_dir`
- **input_file_key**: `trick_input_file`
- **build**: `true` (run `trick-CP` to compile before running)
- **log_vars_key**: `trick_log_vars`
- **result_key**: `trick_result`

**Step 6: Write SeedSimDir**

```python
import os
from pocketflow import Node

class SeedSimDir(Node):
    """Seeds the Trick simulation directory and input file."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        shared["trick_sim_dir"]    = os.path.join(project_dir, "SIM_satellite")
        shared["trick_input_file"] = "RUN_test/input.py"
        # Variables to extract from Trick log files after the run
        shared["trick_log_vars"]   = [
            "satellite.body.omega.x",
            "satellite.body.omega.y",
            "satellite.body.omega.z",
        ]
        return "default"
```

**Step 7: Write LogVariables**

```python
from pocketflow import Node

class LogVariables(Node):
    """Logs the first and last values of logged Trick variables."""

    def prep(self, shared):
        return shared.get("trick_result", {})

    def exec(self, prep_res):
        r = prep_res
        print("=== NASA Trick SIM_satellite Results ===")
        print(f"  Build status : {r.get('build_status', '?')}")
        print(f"  Run status   : {r.get('run_status', '?')}")
        print(f"  Run time     : {r.get('sim_time_s', '?')} s (sim end time)")

        log_data = r.get("log_data", {})
        for var_name, values in log_data.items():
            if isinstance(values, list) and len(values) > 0:
                t0_val  = values[0]
                end_val = values[-1]
                n       = len(values)
                print(f"\n  {var_name}:")
                print(f"    n = {n} samples")
                print(f"    t=0   : {t0_val}")
                print(f"    t=end : {end_val}")
        return r

    def post(self, shared, prep_res, exec_res):
        return "default"
```

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. If `build: true`, Trick first compiles `SIM_satellite` (takes 30–90 seconds on first build; subsequent runs skip compilation if source is unchanged). The simulation then runs. The Run Log streams Trick's real-time output, and `LogVariables` prints the angular velocity time history summary.

> 💡 **Tip:** Set `build: false` after the first successful build to skip compilation on subsequent runs — this dramatically reduces iteration time during development.

### What you learned

- The Trick Simulation Node compiles (optional) and runs a Trick simulation, then reads log files
- Set `build: true` on first run; use `false` thereafter to skip recompilation
- Specify the variables to extract via `log_vars_key` — returns a dict of `{var_name: [values]}`
- Use with a Batch Node to sweep `input.py` parameters across multiple Trick runs
- The result dict contains `build_status`, `run_status`, `sim_time_s`, and `log_data`

---

[← Previous Part: Aerospace CFD and Geometry](gtkn_part23.md)  
[→ Next Part: Wind Energy, Scientific Computing and Data Catalog](gtkn_part25.md)  
[↑ Series Index](gtkn_index.md)  
[↑ Tutorials Index](index.md)
