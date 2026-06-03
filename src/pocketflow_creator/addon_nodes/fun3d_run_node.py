"""NASA FUN3D advanced CFD node — submits a FUN3D RANS/LES case and
retrieves aerodynamic force/moment history.  Requires FUN3D installed
and licensed from NASA LaRC."""

__node_meta__ = {
    "node": "FUN3D Run",
    "category": "Aerospace",
    "version": "1.0.0",
    "description": "Runs a NASA FUN3D CFD case (steady or unsteady) and returns integrated forces.",
    "tags": ["fun3d", "cfd", "rans", "les", "aerodynamics", "nasa", "high-fidelity"],
    "license": "MIT",
    "website": "https://fun3d.larc.nasa.gov/",
    "actions": ["default", "error"],
    "properties": {
        "case_dir_key": {
            "type": "string",
            "default": "fun3d_case_dir",
            "description": ("Shared-store key holding path to the FUN3D case directory (contains fun3d.nml)."),
        },
        "nprocs": {
            "type": "integer",
            "default": "4",
            "description": "Number of MPI processes for mpirun.",
        },
        "result_key": {
            "type": "string",
            "default": "fun3d_result",
            "description": "Shared-store key to write force history and run status.",
        },
    },
    "color": "#1a237e",
}

__node_icon__ = None


class FUN3DRunNode:
    """Run FUN3D via mpirun and parse the forces history file."""

    def prep(self, shared: dict) -> dict:
        return {
            "case_dir": shared.get("fun3d_case_dir", ""),
            "nprocs": int(shared.get("fun3d_nprocs", 4)),
            "result_key": shared.get("fun3d_result_key", "fun3d_result"),
        }

    def exec(self, prep_res: dict):
        import csv
        import os
        import pathlib
        import subprocess

        case_dir = pathlib.Path(prep_res["case_dir"])
        if not case_dir.is_dir():
            return {"error": f"FUN3D case directory not found: {case_dir}"}
        nml = case_dir / "fun3d.nml"
        if not nml.exists():
            return {"error": "fun3d.nml not found in case directory."}
        try:
            cmd = ["mpirun", "-np", str(prep_res["nprocs"]), "nodet_mpi"]
            proc = subprocess.run(
                cmd,
                cwd=case_dir,
                capture_output=True,
                text=True,
                timeout=7200,
                env=os.environ.copy(),
            )
            # Look for *_hist.dat
            hist_files = list(case_dir.glob("*_hist.dat"))
            forces = []
            if hist_files:
                with open(hist_files[0]) as fh:
                    reader = csv.reader(fh, delimiter=" ", skipinitialspace=True)
                    headers = None
                    for row in reader:
                        row = [c for c in row if c]
                        if not row:
                            continue
                        if headers is None and row[0].startswith("#"):
                            headers = row[1:]
                            continue
                        if headers:
                            forces.append(dict(zip(headers, row, strict=False)))
            return {
                "returncode": proc.returncode,
                "n_iter": len(forces),
                "last_iter": forces[-1] if forces else {},
            }
        except FileNotFoundError:
            return {"error": "mpirun or nodet_mpi not found on PATH."}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["fun3d_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
