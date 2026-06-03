"""Generic scipy/OpenMDAO optimization node — wraps scipy.optimize or an
OpenMDAO ScipyOptimizeDriver problem for single-objective minimization."""

__node_meta__ = {
    "node": "Optimization",
    "category": "Aerospace",
    "version": "1.0.0",
    "description": "Minimizes an objective function using scipy or an OpenMDAO driver; returns optimal design variables.",
    "tags": ["optimization", "scipy", "openmdao", "minimization", "gradient-free", "gradient-based"],
    "license": "MIT",
    "website": "https://docs.scipy.org/doc/scipy/reference/optimize.html",
    "actions": ["default", "error"],
    "properties": {
        "objective_key": {
            "type": "string",
            "default": "objective_fn",
            "description": "Shared-store key holding a callable f(x) -> float (scipy mode).",
        },
        "x0_key": {
            "type": "string",
            "default": "x0",
            "description": "Shared-store key holding the initial guess (list or ndarray).",
        },
        "method": {
            "type": "choice",
            "default": "SLSQP",
            "choices": ["SLSQP", "L-BFGS-B", "Nelder-Mead", "COBYLA", "trust-constr"],
            "description": "Scipy optimization method.",
        },
        "result_key": {
            "type": "string",
            "default": "opt_result",
            "description": "Shared-store key to write the scipy OptimizeResult dict.",
        },
    },
    "color": "#004d40",
}

__node_icon__ = None


class OptimizationNode:
    """Run scipy.optimize.minimize and return the result."""

    def prep(self, shared: dict) -> dict:
        return {
            "fn": shared.get("objective_fn"),
            "x0": shared.get("x0", [0.0]),
            "method": shared.get("opt_method", "SLSQP"),
            "result_key": shared.get("opt_result_key", "opt_result"),
        }

    def exec(self, prep_res: dict):
        fn = prep_res["fn"]
        if fn is None:
            return {"error": "No objective function found in shared store."}
        try:
            import numpy as np
            from scipy.optimize import minimize  # type: ignore[import]

            x0 = np.asarray(prep_res["x0"], dtype=float)
            res = minimize(fn, x0, method=prep_res["method"])
            return {
                "x_opt": res.x.tolist(),
                "fun": float(res.fun),
                "success": res.success,
                "message": res.message,
                "nit": res.nit,
            }
        except ImportError:
            return {"error": "scipy not installed.  Run: pip install scipy"}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["opt_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
