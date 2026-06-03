"""SU2 open-source CFD node — writes a config, runs SU2_CFD, and
parses the convergence history.  Requires SU2 installed and on PATH.
Install: https://su2code.github.io/docs/Installation/"""

__node_meta__ = {
    "node": "SU2 CFD",
    "category": "Aerospace",
    "version": "1.0.0",
    "description": "Runs an SU2_CFD analysis case and returns drag, lift, and moment convergence history.",
    "tags": ["su2", "cfd", "open-source", "euler", "rans", "aerodynamics"],
    "license": "MIT",
    "website": "https://su2code.github.io/",
    "repo": "https://github.com/su2code/SU2",
    "actions": ["default", "error"],
    "properties": {
        "config_path_key": {
            "type": "string",
            "default": "su2_config_path",
            "description": "Shared-store key holding path to the SU2 .cfg file.",
        },
        "nprocs": {
            "type": "integer",
            "default": "1",
            "description": "Number of MPI processes (1 = serial SU2_CFD).",
        },
        "result_key": {
            "type": "string",
            "default": "su2_result",
            "description": "Shared-store key to write the final aerodynamic coefficients.",
        },
    },
    "color": "#37474f",
}

__node_icon__ = None


class SU2CFDNode:
    """Run SU2_CFD and parse history.dat for final CL/CD."""

    def prep(self, shared: dict) -> dict:
        return {
            "config_path": shared.get("su2_config_path", ""),
            "nprocs": int(shared.get("su2_nprocs", 1)),
            "result_key": shared.get("su2_result_key", "su2_result"),
        }

    def exec(self, prep_res: dict):
        import csv
        import os
        import pathlib
        import subprocess

        cfg_path = pathlib.Path(prep_res["config_path"])
        if not cfg_path.exists():
            return {"error": f"SU2 config file not found: {cfg_path}"}
        case_dir = cfg_path.parent
        nprocs = prep_res["nprocs"]
        try:
            if nprocs > 1:
                cmd = ["mpirun", "-np", str(nprocs), "SU2_CFD", cfg_path.name]
            else:
                cmd = ["SU2_CFD", cfg_path.name]
            proc = subprocess.run(
                cmd,
                cwd=case_dir,
                capture_output=True,
                text=True,
                timeout=7200,
                env=os.environ.copy(),
            )
            history = case_dir / "history.dat"
            last_row: dict = {}
            if history.exists():
                with open(history) as fh:
                    rows = list(csv.DictReader(fh))
                    if rows:
                        last_row = {k.strip(): v.strip() for k, v in rows[-1].items()}
            return {"returncode": proc.returncode, "final": last_row}
        except FileNotFoundError:
            return {"error": "SU2_CFD (or mpirun) not found on PATH.  Install SU2."}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["su2_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
