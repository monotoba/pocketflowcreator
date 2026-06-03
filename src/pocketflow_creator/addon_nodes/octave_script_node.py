"""GNU Octave script node — runs an Octave script file or inline commands
via the oct2py bridge (pip install oct2py).  Free, open-source alternative
to MATLAB Engine."""

__node_meta__ = {
    "node": "Octave Script",
    "category": "Scientific Computing",
    "version": "1.0.0",
    "description": "Runs a GNU Octave script or expression and returns workspace output.",
    "tags": ["octave", "matlab", "numerical", "scientific", "open-source"],
    "license": "MIT",
    "website": "https://oct2py.readthedocs.io/",
    "repo": "https://github.com/blink1073/oct2py",
    "actions": ["default", "error"],
    "properties": {
        "script_path_key": {
            "type": "string",
            "default": "octave_script_path",
            "description": "Shared-store key holding the path to a .m script file (or leave blank to use inline_code).",
        },
        "inline_code_key": {
            "type": "string",
            "default": "octave_code",
            "description": "Shared-store key holding an inline Octave expression.",
        },
        "result_var": {
            "type": "string",
            "default": "ans",
            "description": "Octave variable name to read back as the result.",
        },
        "result_key": {
            "type": "string",
            "default": "octave_result",
            "description": "Shared-store key to write the result into.",
        },
    },
    "color": "#0d47a1",
}

__node_icon__ = None


class OctaveScriptNode:
    """Run an Octave .m script or inline expression and retrieve a named variable."""

    def prep(self, shared: dict) -> dict:
        return {
            "script_path": shared.get("octave_script_path", ""),
            "inline_code": shared.get("octave_code", ""),
            "result_var": shared.get("octave_result_var", "ans"),
            "result_key": shared.get("octave_result_key", "octave_result"),
        }

    def exec(self, prep_res: dict):
        try:
            from oct2py import Oct2Py  # type: ignore[import]
        except ImportError:
            return {"error": "oct2py not installed.  Run: pip install oct2py"}
        try:
            oc = Oct2Py()
            if prep_res["script_path"]:
                oc.run(prep_res["script_path"])
            elif prep_res["inline_code"]:
                oc.eval(prep_res["inline_code"])
            else:
                return {"error": "No script path or inline code provided."}
            result = oc.pull(prep_res["result_var"])
            oc.exit()
            return {"result": result}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["octave_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res["result"]
        return "default"
