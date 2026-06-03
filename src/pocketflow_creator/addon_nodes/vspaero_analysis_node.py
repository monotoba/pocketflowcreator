"""NASA VSPAERO aerodynamic analysis node — drives a VSPAERO solver run
from a DegenGeom CSV produced by OpenVSP.  Requires the vspaero binary
on PATH or the openvsp Python bindings."""

__node_meta__ = {
    "node":        "VSPAERO Analysis",
    "category":    "Aerospace",
    "version":     "1.0.0",
    "description": "Runs a VSPAERO vortex-lattice / panel method aero analysis and returns CL, CD, and moment data.",
    "tags":        ["vspaero", "openvsp", "aerodynamics", "vortex-lattice", "panel-method", "nasa"],
    "license":     "MIT",
    "website":     "https://openvsp.org/",
    "repo":        "https://github.com/OpenVSP/OpenVSP",
    "actions":     ["default", "error"],
    "properties": {
        "degen_geom_key": {
            "type":        "string",
            "default":     "vsp_output_path",
            "description": "Shared-store key holding the path to the DegenGeom CSV file.",
        },
        "alpha": {
            "type":        "number",
            "default":     "0.0",
            "description": "Angle of attack in degrees.",
        },
        "mach": {
            "type":        "number",
            "default":     "0.1",
            "description": "Freestream Mach number.",
        },
        "result_key": {
            "type":        "string",
            "default":     "vspaero_result",
            "description": "Shared-store key to write the aero polar dict.",
        },
    },
    "color": "#1565c0",
}

__node_icon__ = None


class VSPAeroAnalysisNode:
    """Run a VSPAERO analysis and parse the polar output."""

    def prep(self, shared: dict) -> dict:
        return {
            "degen_geom": shared.get("vsp_output_path", ""),
            "alpha":      float(shared.get("vspaero_alpha", 0.0)),
            "mach":       float(shared.get("vspaero_mach", 0.1)),
            "result_key": shared.get("vspaero_result_key", "vspaero_result"),
        }

    def exec(self, prep_res: dict):
        degen = prep_res["degen_geom"]
        if not degen:
            return {"error": "No DegenGeom path provided."}
        try:
            import openvsp as vsp  # type: ignore[import]
            # Build a simple single-point analysis
            setup = vsp.vspaero.SetupFile(degen)
            setup.AlphaDeg = prep_res["alpha"]
            setup.Mach = prep_res["mach"]
            setup.NumWakeIter = 5
            results = vsp.vspaero.Run(setup)
            polar = {
                "CL": results.CL,
                "CD": results.CD,
                "CM": results.CMy,
                "alpha_deg": prep_res["alpha"],
                "mach": prep_res["mach"],
            }
            return {"polar": polar}
        except ImportError:
            return {"error": "openvsp bindings not found; cannot run VSPAERO."}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["vspaero_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res["polar"]
        return "default"
