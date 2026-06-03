"""USGS MODFLOW 6 groundwater model node — runs a MODFLOW 6 simulation
from a name file and returns budget summary data.
Requires MODFLOW 6 binary on PATH: https://github.com/MODFLOW-USGS/modflow6"""

__node_meta__ = {
    "node":        "MODFLOW 6 Run",
    "category":    "Hydrology / Water",
    "version":     "1.0.0",
    "description": "Runs a USGS MODFLOW 6 groundwater simulation and returns head and budget summaries.",
    "tags":        ["modflow", "groundwater", "usgs", "aquifer", "simulation", "hydrogeology"],
    "license":     "MIT",
    "website":     "https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model",
    "repo":        "https://github.com/MODFLOW-USGS/modflow6",
    "actions":     ["default", "error"],
    "properties": {
        "sim_dir_key": {
            "type":        "string",
            "default":     "mf6_sim_dir",
            "description": "Shared-store key holding path to the MODFLOW 6 simulation directory.",
        },
        "result_key": {
            "type":        "string",
            "default":     "mf6_result",
            "description": "Shared-store key to write run status and listing file summary.",
        },
    },
    "color": "#1565c0",
}

__node_icon__ = None


class MODFLOW6RunNode:
    """Run MODFLOW 6 and parse the listing file for budget information."""

    def prep(self, shared: dict) -> dict:
        return {
            "sim_dir":   shared.get("mf6_sim_dir", ""),
            "result_key": shared.get("mf6_result_key", "mf6_result"),
        }

    def exec(self, prep_res: dict):
        import os
        import pathlib
        import re
        import subprocess
        sim_dir = pathlib.Path(prep_res["sim_dir"])
        if not sim_dir.is_dir():
            return {"error": f"MODFLOW 6 simulation directory not found: {sim_dir}"}
        try:
            proc = subprocess.run(
                ["mf6"],
                cwd=sim_dir, capture_output=True, text=True,
                timeout=3600, env=os.environ.copy(),
            )
            # Find listing file(s)
            lst_files = list(sim_dir.rglob("*.lst"))
            summary: dict = {"returncode": proc.returncode}
            if lst_files:
                lst_text = lst_files[0].read_text()
                # Extract BUDGET information
                budget_match = re.findall(
                    r"TOTAL IN\s+=\s+([\d.E+\-]+).*?TOTAL OUT\s+=\s+([\d.E+\-]+)",
                    lst_text, re.DOTALL
                )
                if budget_match:
                    last = budget_match[-1]
                    summary["total_in"]  = float(last[0])
                    summary["total_out"] = float(last[1])
                summary["listing_file"] = str(lst_files[0])
                # Check NORMAL TERMINATION
                summary["normal_termination"] = "NORMAL TERMINATION" in lst_text
            return summary
        except FileNotFoundError:
            return {"error": "mf6 binary not found on PATH.  Download from https://github.com/MODFLOW-USGS/modflow6/releases"}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["mf6_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
