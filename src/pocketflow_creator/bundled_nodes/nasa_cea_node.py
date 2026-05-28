"""NASA CEA (Chemical Equilibrium with Applications) node — computes
combustion properties and rocket performance parameters.  Uses the
rocketcea Python wrapper (pip install rocketcea) which bundles the
Fortran CEA binary."""

__node_meta__ = {
    "node":        "NASA CEA",
    "category":    "Aerospace",
    "version":     "1.0.0",
    "description": "Computes rocket combustion properties (Isp, Tc, gamma, MW) using NASA CEA via rocketcea.",
    "tags":        ["cea", "combustion", "rocket", "propulsion", "thermodynamics", "nasa"],
    "license":     "MIT",
    "website":     "https://rocketcea.readthedocs.io/",
    "repo":        "https://github.com/sonofeft/RocketCEA",
    "actions":     ["default", "error"],
    "properties": {
        "oxid": {
            "type":        "string",
            "default":     "LOX",
            "description": "CEA oxidizer name (e.g. LOX, N2O4, IRFNA).",
        },
        "fuel": {
            "type":        "string",
            "default":     "LH2",
            "description": "CEA fuel name (e.g. LH2, RP1, MMH, Methane).",
        },
        "pc_psia": {
            "type":        "number",
            "default":     "1000",
            "description": "Chamber pressure in psia.",
        },
        "mr": {
            "type":        "number",
            "default":     "6.0",
            "description": "Mixture ratio (O/F) by mass.",
        },
        "eps": {
            "type":        "number",
            "default":     "40.0",
            "description": "Nozzle area ratio (exit/throat).",
        },
        "result_key": {
            "type":        "string",
            "default":     "cea_result",
            "description": "Shared-store key to write the CEA performance dict.",
        },
    },
    "color": "#b71c1c",
}

__node_icon__ = None


class NASACEANode:
    """Run a CEA rocket performance calculation via rocketcea."""

    def prep(self, shared: dict) -> dict:
        return {
            "oxid":       shared.get("cea_oxid", "LOX"),
            "fuel":       shared.get("cea_fuel", "LH2"),
            "pc_psia":    float(shared.get("cea_pc_psia", 1000.0)),
            "mr":         float(shared.get("cea_mr", 6.0)),
            "eps":        float(shared.get("cea_eps", 40.0)),
            "result_key": shared.get("cea_result_key", "cea_result"),
        }

    def exec(self, prep_res: dict):
        try:
            from rocketcea.cea_obj import CEA_Obj  # type: ignore[import]
        except ImportError:
            return {"error": "rocketcea not installed.  Run: pip install rocketcea"}
        try:
            cea = CEA_Obj(oxName=prep_res["oxid"], fuelName=prep_res["fuel"])
            pc    = prep_res["pc_psia"]
            mr    = prep_res["mr"]
            eps   = prep_res["eps"]
            isp_vac = cea.get_Isp(Pc=pc, MR=mr, eps=eps)
            isp_del = cea.get_IspAmb(Pc=pc, MR=mr, eps=eps)
            tc      = cea.get_Tcomb(Pc=pc, MR=mr)
            cstar   = cea.get_Cstar(Pc=pc, MR=mr)
            cf      = cea.get_PambCf(Pc=pc, MR=mr, eps=eps)[1]
            return {
                "Isp_vac_s":   round(isp_vac, 2),
                "Isp_del_s":   round(isp_del, 2),
                "Tc_R":        round(tc, 1),
                "Cstar_fps":   round(cstar, 1),
                "Cf":          round(cf, 4),
                "oxid":        prep_res["oxid"],
                "fuel":        prep_res["fuel"],
                "pc_psia":     pc,
                "mr":          mr,
                "eps":         eps,
            }
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["cea_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
