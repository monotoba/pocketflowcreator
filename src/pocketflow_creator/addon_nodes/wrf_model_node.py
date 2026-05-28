"""WRF (Weather Research and Forecasting) model node — prepares namelist
files and runs real.exe + wrf.exe for numerical weather prediction.
Requires WRF compiled and on PATH."""

__node_meta__ = {
    "node":        "WRF Model",
    "category":    "Weather / Atmosphere",
    "version":     "1.0.0",
    "description": "Runs WRF NWP simulation (real.exe + wrf.exe) and returns wrfout file paths.",
    "tags":        ["wrf", "numerical-weather", "nwp", "atmosphere", "mesoscale"],
    "license":     "MIT",
    "website":     "https://www.mmm.ucar.edu/weather-research-and-forecasting-model",
    "repo":        "https://github.com/wrf-model/WRF",
    "actions":     ["default", "error"],
    "properties": {
        "run_dir_key": {
            "type":        "string",
            "default":     "wrf_run_dir",
            "description": "Shared-store key holding path to the WRF run/ directory.",
        },
        "nprocs": {
            "type":        "integer",
            "default":     "4",
            "description": "Number of MPI processes.",
        },
        "skip_real": {
            "type":        "bool",
            "default":     "false",
            "description": "Skip real.exe (use if wrfinput/wrfbdy already exist).",
        },
        "result_key": {
            "type":        "string",
            "default":     "wrf_result",
            "description": "Shared-store key to write wrfout file paths and status.",
        },
    },
    "color": "#0277bd",
}

__node_icon__ = None


class WRFModelNode:
    """Run WRF (optionally real.exe then wrf.exe) and list output files."""

    def prep(self, shared: dict) -> dict:
        return {
            "run_dir":    shared.get("wrf_run_dir", ""),
            "nprocs":     int(shared.get("wrf_nprocs", 4)),
            "skip_real":  bool(shared.get("wrf_skip_real", False)),
            "result_key": shared.get("wrf_result_key", "wrf_result"),
        }

    def exec(self, prep_res: dict):
        import subprocess, pathlib, os, glob
        run_dir = pathlib.Path(prep_res["run_dir"])
        if not run_dir.is_dir():
            return {"error": f"WRF run directory not found: {run_dir}"}
        env = os.environ.copy()
        np = prep_res["nprocs"]
        try:
            if not prep_res["skip_real"]:
                real_proc = subprocess.run(
                    ["mpirun", "-np", str(np), "./real.exe"],
                    cwd=run_dir, capture_output=True, text=True,
                    timeout=3600, env=env,
                )
                if real_proc.returncode != 0:
                    return {"error": f"real.exe failed:\n{real_proc.stderr[-1000:]}"}
            wrf_proc = subprocess.run(
                ["mpirun", "-np", str(np), "./wrf.exe"],
                cwd=run_dir, capture_output=True, text=True,
                timeout=86400, env=env,
            )
            if wrf_proc.returncode != 0:
                return {"error": f"wrf.exe failed:\n{wrf_proc.stderr[-1000:]}"}
            wrfout_files = sorted(glob.glob(str(run_dir / "wrfout_*")))
            return {"returncode": wrf_proc.returncode, "wrfout_files": wrfout_files}
        except FileNotFoundError:
            return {"error": "mpirun or WRF executables not found on PATH."}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["wrf_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
