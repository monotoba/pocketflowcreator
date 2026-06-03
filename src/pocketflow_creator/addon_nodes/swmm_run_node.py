"""EPA SWMM stormwater management model node — runs a SWMM5 simulation
from an .inp file and returns routing summary results.
Requires swmm5 Python bindings: pip install swmm5"""

__node_meta__ = {
    "node":        "EPA SWMM Run",
    "category":    "Hydrology / Water",
    "version":     "1.0.0",
    "description": "Runs an EPA SWMM 5 stormwater simulation and returns peak flow and volume results.",
    "tags":        ["swmm", "epa", "stormwater", "hydrology", "urban-drainage"],
    "license":     "MIT",
    "website":     "https://www.epa.gov/water-research/storm-water-management-model-swmm",
    "repo":        "https://github.com/pyswmm/pyswmm",
    "actions":     ["default", "error"],
    "properties": {
        "inp_path_key": {
            "type":        "string",
            "default":     "swmm_inp_path",
            "description": "Shared-store key holding path to the SWMM .inp file.",
        },
        "report_key": {
            "type":        "string",
            "default":     "swmm_rpt_path",
            "description": "Shared-store key holding path to write the .rpt report (optional).",
        },
        "result_key": {
            "type":        "string",
            "default":     "swmm_result",
            "description": "Shared-store key to write the simulation results dict.",
        },
    },
    "color": "#1565c0",
}

__node_icon__ = None


class SWMMRunNode:
    """Run an EPA SWMM simulation via pyswmm and return link summaries."""

    def prep(self, shared: dict) -> dict:
        import pathlib
        inp = pathlib.Path(shared.get("swmm_inp_path", ""))
        rpt = shared.get("swmm_rpt_path", "") or str(inp.with_suffix(".rpt"))
        return {
            "inp_path":  str(inp),
            "rpt_path":  rpt,
            "result_key": shared.get("swmm_result_key", "swmm_result"),
        }

    def exec(self, prep_res: dict):
        import pathlib
        inp = pathlib.Path(prep_res["inp_path"])
        if not inp.exists():
            return {"error": f"SWMM input file not found: {inp}"}
        try:
            from pyswmm import Links, Simulation  # type: ignore[import]
            with Simulation(str(inp)) as sim:
                links = Links(sim)
                sim.execute()
                summary = {}
                for link in links:
                    summary[link.linkid] = {
                        "peak_flow_cms": link.statistics.get("peak_flow", None),
                        "total_volume":  link.statistics.get("total_volume", None),
                    }
            return {"links": summary, "n_links": len(summary)}
        except ImportError:
            # Fall back to subprocess swmm5
            import os
            import subprocess
            try:
                out_rpt = prep_res["rpt_path"]
                proc = subprocess.run(
                    ["swmm5", str(inp), out_rpt, "/dev/null"],
                    capture_output=True, text=True, timeout=600, env=os.environ.copy(),
                )
                return {"returncode": proc.returncode, "rpt_path": out_rpt}
            except FileNotFoundError:
                return {"error": "pyswmm and swmm5 binary not found.  Run: pip install pyswmm"}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["swmm_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
