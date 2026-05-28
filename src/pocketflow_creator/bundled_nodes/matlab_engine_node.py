"""MATLAB Engine API node — runs a MATLAB function or script via the
official matlab.engine Python interface.  Requires a licensed MATLAB
installation with the Engine API for Python installed."""

__node_meta__ = {
    "node":        "MATLAB Engine",
    "category":    "Scientific Computing",
    "version":     "1.0.0",
    "description": "Runs a MATLAB function or script via matlab.engine and returns workspace variables.",
    "tags":        ["matlab", "numerical", "scientific", "simulation", "commercial"],
    "license":     "MIT",
    "website":     "https://www.mathworks.com/help/matlab/matlab_external/get-started-with-matlab-engine-for-python.html",
    "actions":     ["default", "error"],
    "properties": {
        "script_key": {
            "type":        "string",
            "default":     "matlab_script",
            "description": "Shared-store key holding the MATLAB script/function name to call.",
        },
        "args_key": {
            "type":        "string",
            "default":     "matlab_args",
            "description": "Shared-store key holding a list of positional arguments (optional).",
        },
        "result_key": {
            "type":        "string",
            "default":     "matlab_result",
            "description": "Shared-store key to write the returned value(s) into.",
        },
        "nargout": {
            "type":        "integer",
            "default":     "1",
            "description": "Number of output arguments expected from MATLAB.",
        },
    },
    "color": "#a31515",
}

__node_icon__ = None


class MatlabEngineNode:
    """Start the MATLAB engine, call a function, return results."""

    def prep(self, shared: dict) -> dict:
        return {
            "script":     shared.get("matlab_script", ""),
            "args":       shared.get("matlab_args", []) or [],
            "result_key": shared.get("matlab_result_key", "matlab_result"),
            "nargout":    int(shared.get("matlab_nargout", 1)),
        }

    def exec(self, prep_res: dict):
        script = prep_res["script"]
        if not script:
            return {"error": "No script/function name provided."}
        try:
            import matlab.engine  # type: ignore[import]
            eng = matlab.engine.start_matlab()
            fn = getattr(eng, script, None)
            if fn is None:
                eng.quit()
                return {"error": f"MATLAB function '{script}' not found."}
            result = fn(*prep_res["args"], nargout=prep_res["nargout"])
            eng.quit()
            return {"result": result}
        except ImportError:
            return {
                "error": (
                    "matlab.engine not found.  Install with: "
                    "cd <matlabroot>/extern/engines/python && python setup.py install"
                )
            }
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["matlab_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res["result"]
        return "default"
