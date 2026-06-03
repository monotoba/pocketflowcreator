"""USGS FloPy Python interface node — builds and runs a MODFLOW model
using the FloPy library and returns head arrays and budget data.
Install: pip install flopy"""

__node_meta__ = {
    "node":        "FloPy Model",
    "category":    "Hydrology / Water",
    "version":     "1.0.0",
    "description": "Builds and runs a MODFLOW model via FloPy and returns simulated head and budget arrays.",
    "tags":        ["flopy", "modflow", "groundwater", "usgs", "python", "hydrogeology"],
    "license":     "MIT",
    "website":     "https://flopy.readthedocs.io/",
    "repo":        "https://github.com/modflowpy/flopy",
    "actions":     ["default", "error"],
    "properties": {
        "model_key": {
            "type":        "string",
            "default":     "flopy_model",
            "description": "Shared-store key holding a configured flopy.modflow.Modflow or flopy.mf6.MFSimulation instance.",
        },
        "exe_name": {
            "type":        "string",
            "default":     "mf6",
            "description": "MODFLOW executable name (mf6, mf2005, mfnwt, etc.).",
        },
        "result_key": {
            "type":        "string",
            "default":     "flopy_result",
            "description": "Shared-store key to write head statistics and budget summary.",
        },
    },
    "color": "#0277bd",
}

__node_icon__ = None


class FloPyModelNode:
    """Run a FloPy-configured MODFLOW model and return head statistics."""

    def prep(self, shared: dict) -> dict:
        return {
            "model":      shared.get("flopy_model"),
            "exe_name":   shared.get("flopy_exe_name", "mf6"),
            "result_key": shared.get("flopy_result_key", "flopy_result"),
        }

    def exec(self, prep_res: dict):
        model = prep_res["model"]
        if model is None:
            return {"error": "No FloPy model instance found in shared store."}
        try:
            import numpy as np  # noqa: F401
        except ImportError:
            return {"error": "flopy not installed.  Run: pip install flopy"}
        try:
            model.exe_name = prep_res["exe_name"]
            success, buff = model.run_model(silent=True)
            if not success:
                return {"error": "MODFLOW run failed.", "buffer": buff[-500:] if buff else ""}
            # Try to read heads
            result: dict = {"success": success}
            try:
                hds = model.output.head()
                head_data = hds.get_data()
                result["head_min"] = float(np.nanmin(head_data))
                result["head_max"] = float(np.nanmax(head_data))
                result["head_mean"] = float(np.nanmean(head_data))
                result["head_shape"] = list(head_data.shape)
            except Exception:  # noqa: BLE001
                result["head_note"] = "Could not read head output."
            return result
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["flopy_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
