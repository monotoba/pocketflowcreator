"""NASA Cart3D inviscid CFD node — prepares input, runs the Cart3D
adaptive mesh refinement pipeline, and returns integrated aerodynamic
coefficients.  Requires Cart3D installed and licensed from NASA."""

__node_meta__ = {
    "node":        "Cart3D Analysis",
    "category":    "Aerospace",
    "version":     "1.0.0",
    "description": "Runs a NASA Cart3D inviscid Euler CFD analysis and returns CL/CD/CM coefficients.",
    "tags":        ["cart3d", "cfd", "euler", "inviscid", "aerodynamics", "nasa"],
    "license":     "MIT",
    "website":     "https://www.nas.nasa.gov/software/cart3d.html",
    "actions":     ["default", "error"],
    "properties": {
        "case_dir_key": {
            "type":        "string",
            "default":     "cart3d_case_dir",
            "description": "Shared-store key holding path to the Cart3D case directory.",
        },
        "aoa": {
            "type":        "number",
            "default":     "0.0",
            "description": "Angle of attack in degrees.",
        },
        "mach": {
            "type":        "number",
            "default":     "0.5",
            "description": "Freestream Mach number.",
        },
        "n_adapt": {
            "type":        "integer",
            "default":     "5",
            "description": "Number of mesh adaptation cycles.",
        },
        "result_key": {
            "type":        "string",
            "default":     "cart3d_result",
            "description": "Shared-store key to write the aero coefficient dict.",
        },
    },
    "color": "#004d40",
}

__node_icon__ = None


class Cart3DAnalysisNode:
    """Set up and run a Cart3D AMR CFD case."""

    def prep(self, shared: dict) -> dict:
        return {
            "case_dir":  shared.get("cart3d_case_dir", ""),
            "aoa":       float(shared.get("cart3d_aoa", 0.0)),
            "mach":      float(shared.get("cart3d_mach", 0.5)),
            "n_adapt":   int(shared.get("cart3d_n_adapt", 5)),
            "result_key": shared.get("cart3d_result_key", "cart3d_result"),
        }

    def exec(self, prep_res: dict):
        import os
        import pathlib
        import re
        import subprocess
        case_dir = pathlib.Path(prep_res["case_dir"])
        if not case_dir.is_dir():
            return {"error": f"Cart3D case directory not found: {case_dir}"}
        try:
            # Write aero.csh or adapt.csh configuration
            input_csh = case_dir / "aero.csh"
            if not input_csh.exists():
                return {"error": "aero.csh not found in case directory."}
            run_proc = subprocess.run(
                ["bash", "aero.csh", "ADAPT", f"N={prep_res['n_adapt']}"],
                cwd=case_dir, capture_output=True, text=True,
                timeout=7200, env=os.environ.copy(),
            )
            # Parse loadsCC.dat for coefficients
            loads_file = case_dir / "BEST" / "FLOW" / "loadsCC.dat"
            cl = cd = cm = None
            if loads_file.exists():
                for line in loads_file.read_text().splitlines():
                    m = re.search(r"CL\s*=\s*([-\d.eE+]+)", line)
                    if m:
                        cl = float(m.group(1))
                    m = re.search(r"CD\s*=\s*([-\d.eE+]+)", line)
                    if m:
                        cd = float(m.group(1))
                    m = re.search(r"CM\s*=\s*([-\d.eE+]+)", line)
                    if m:
                        cm = float(m.group(1))
            return {"CL": cl, "CD": cd, "CM": cm, "returncode": run_proc.returncode}
        except FileNotFoundError:
            return {"error": "Cart3D / bash not found on PATH."}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["cart3d_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
