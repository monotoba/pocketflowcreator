"""NASA GMAT (General Mission Analysis Tool) script node — executes a
.script file using the gmat Python API or the gmat command-line binary.
Requires GMAT R2022a+ with the Python API enabled."""

__node_meta__ = {
    "node": "GMAT Script",
    "category": "Aerospace",
    "version": "1.0.0",
    "description": "Runs a GMAT mission analysis script and returns selected report file data.",
    "tags": ["gmat", "orbital-mechanics", "astrodynamics", "mission-analysis", "nasa"],
    "license": "MIT",
    "website": "https://gmat.gsfc.nasa.gov/",
    "repo": "https://sourceforge.net/projects/gmat/",
    "actions": ["default", "error"],
    "properties": {
        "script_path_key": {
            "type": "string",
            "default": "gmat_script_path",
            "description": "Shared-store key holding the path to the GMAT .script file.",
        },
        "report_path_key": {
            "type": "string",
            "default": "gmat_report_path",
            "description": "Shared-store key holding the path to the expected output report file (optional).",
        },
        "result_key": {
            "type": "string",
            "default": "gmat_result",
            "description": "Shared-store key to write parsed report data or run status.",
        },
    },
    "color": "#1a237e",
}

__node_icon__ = None


class GMATScriptNode:
    """Execute a GMAT script and optionally parse its report output."""

    def prep(self, shared: dict) -> dict:
        return {
            "script_path": shared.get("gmat_script_path", ""),
            "report_path": shared.get("gmat_report_path", ""),
            "result_key": shared.get("gmat_result_key", "gmat_result"),
        }

    def exec(self, prep_res: dict):
        script = prep_res["script_path"]
        if not script:
            return {"error": "No GMAT script path provided."}
        # Try the gmat Python API first, fall back to subprocess
        try:
            import gmat_py_simple as gmat  # type: ignore[import]

            gmat.LoadApplicationData()
            gmat.RunScript(script)
            result: dict = {"status": "success", "script": script}
        except ImportError:
            import pathlib
            import subprocess

            try:
                proc = subprocess.run(
                    ["GMAT", "--run", "--script", script, "--exit"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if proc.returncode != 0:
                    return {"error": proc.stderr or "GMAT exited with non-zero code."}
                result = {"status": "success", "script": script, "stdout": proc.stdout}
            except FileNotFoundError:
                return {"error": "GMAT binary not found on PATH and gmat_py_simple not installed."}
            except Exception as exc:  # noqa: BLE001
                return {"error": str(exc)}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}
        # Parse report file if provided
        report = prep_res["report_path"]
        if report:
            import pathlib

            p = pathlib.Path(report)
            if p.exists():
                lines = p.read_text().strip().splitlines()
                result["report_lines"] = len(lines)
                result["report_head"] = lines[:5]
        return result

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["gmat_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
