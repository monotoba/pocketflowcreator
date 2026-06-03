"""NASA OpenMDAO multidisciplinary analysis node — builds and runs an
OpenMDAO Problem from a model dictionary stored in the shared store.
Requires: pip install openmdao"""

__node_meta__ = {
    "node": "OpenMDAO Model",
    "category": "Aerospace",
    "version": "1.0.0",
    "description": "Executes a NASA OpenMDAO multidisciplinary analysis problem and returns design variable values.",
    "tags": ["openmdao", "mdo", "optimization", "multidisciplinary", "nasa"],
    "license": "MIT",
    "website": "https://openmdao.org/",
    "repo": "https://github.com/OpenMDAO/OpenMDAO",
    "actions": ["default", "error"],
    "properties": {
        "problem_key": {
            "type": "string",
            "default": "openmdao_problem",
            "description": "Shared-store key holding a configured openmdao.api.Problem instance.",
        },
        "driver": {
            "type": "choice",
            "default": "run_model",
            "choices": ["run_model", "run_driver"],
            "description": "Whether to run only the model (analysis) or the full driver (optimization).",
        },
        "result_key": {
            "type": "string",
            "default": "openmdao_result",
            "description": "Shared-store key to write a dict of output variable values.",
        },
    },
    "color": "#006064",
}

__node_icon__ = None


class OpenMDAOModelNode:
    """Run an OpenMDAO Problem and return its output variables."""

    def prep(self, shared: dict) -> dict:
        return {
            "problem": shared.get("openmdao_problem"),
            "driver": shared.get("openmdao_driver", "run_model"),
            "result_key": shared.get("openmdao_result_key", "openmdao_result"),
        }

    def exec(self, prep_res: dict):
        prob = prep_res["problem"]
        if prob is None:
            return {"error": "No openmdao.Problem found in shared store."}
        try:
            import openmdao.api  # type: ignore[import]  # noqa: F401

            if not getattr(prob, "_metadata", None):
                prob.setup()
            if prep_res["driver"] == "run_driver":
                prob.run_driver()
            else:
                prob.run_model()
            # Collect all outputs into a plain dict
            outputs = {}
            for name in prob.model.list_outputs(prom_name=True, out_stream=None):
                try:
                    outputs[name[0]] = float(prob.get_val(name[0]))
                except Exception:  # noqa: BLE001
                    pass
            return {"outputs": outputs}
        except ImportError:
            return {"error": "openmdao not installed.  Run: pip install openmdao"}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["openmdao_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res["outputs"]
        return "default"
