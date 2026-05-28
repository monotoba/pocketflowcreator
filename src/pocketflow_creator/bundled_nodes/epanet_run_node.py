"""EPA EPANET water distribution network node — runs an EPANET hydraulic
and water-quality simulation from an .inp file.
Requires wntr or epynet: pip install wntr"""

__node_meta__ = {
    "node":        "EPA EPANET Run",
    "category":    "Hydrology / Water",
    "version":     "1.0.0",
    "description": "Runs an EPA EPANET water distribution network simulation and returns nodal pressures and pipe flows.",
    "tags":        ["epanet", "epa", "water-distribution", "hydraulics", "water-quality"],
    "license":     "MIT",
    "website":     "https://www.epa.gov/water-research/epanet",
    "repo":        "https://github.com/USEPA/EPANET2.2",
    "actions":     ["default", "error"],
    "properties": {
        "inp_path_key": {
            "type":        "string",
            "default":     "epanet_inp_path",
            "description": "Shared-store key holding path to the EPANET .inp file.",
        },
        "result_key": {
            "type":        "string",
            "default":     "epanet_result",
            "description": "Shared-store key to write pressures, flows, and velocity summary.",
        },
    },
    "color": "#006064",
}

__node_icon__ = None


class EPANETRunNode:
    """Simulate an EPANET network with wntr and return pressure/flow summaries."""

    def prep(self, shared: dict) -> dict:
        return {
            "inp_path":  shared.get("epanet_inp_path", ""),
            "result_key": shared.get("epanet_result_key", "epanet_result"),
        }

    def exec(self, prep_res: dict):
        import pathlib
        inp = pathlib.Path(prep_res["inp_path"])
        if not inp.exists():
            return {"error": f"EPANET input file not found: {inp}"}
        try:
            import wntr  # type: ignore[import]
            wn = wntr.network.WaterNetworkModel(str(inp))
            sim = wntr.sim.EpanetSimulator(wn)
            results = sim.run_sim()
            pressure = results.node["pressure"].mean().to_dict()
            flowrate = results.link["flowrate"].mean().to_dict()
            return {
                "n_nodes":         len(pressure),
                "n_links":         len(flowrate),
                "mean_pressure_m": {k: round(v, 3) for k, v in list(pressure.items())[:20]},
                "mean_flow_cms":   {k: round(v, 6) for k, v in list(flowrate.items())[:20]},
            }
        except ImportError:
            return {"error": "wntr not installed.  Run: pip install wntr"}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["epanet_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
