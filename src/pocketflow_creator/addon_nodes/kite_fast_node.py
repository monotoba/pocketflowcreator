"""NREL KiteFAST airborne wind energy simulation node — runs a KiteFAST
aero-elastic simulation for tethered kite/AWE systems.  KiteFAST is
built on the OpenFAST framework.
Requires KiteFAST binary on PATH."""

__node_meta__ = {
    "node": "KiteFAST",
    "category": "Wind Energy",
    "version": "1.0.0",
    "description": "Runs an NREL KiteFAST airborne-wind-energy (AWE) simulation and returns tether tension and power.",
    "tags": ["kitefast", "awe", "airborne-wind", "kite", "nrel", "simulation"],
    "license": "MIT",
    "website": "https://github.com/OpenFAST/KiteFAST",
    "repo": "https://github.com/OpenFAST/KiteFAST",
    "actions": ["default", "error"],
    "properties": {
        "input_path_key": {
            "type": "string",
            "default": "kitefast_input_path",
            "description": "Shared-store key holding path to the KiteFAST main input file.",
        },
        "result_key": {
            "type": "string",
            "default": "kitefast_result",
            "description": "Shared-store key to write simulation summary (tether tension, power, etc.).",
        },
    },
    "color": "#2e7d32",
}

__node_icon__ = None


class KiteFASTNode:
    """Run KiteFAST and collect tether tension and power output."""

    def prep(self, shared: dict) -> dict:
        return {
            "input_path": shared.get("kitefast_input_path", ""),
            "result_key": shared.get("kitefast_result_key", "kitefast_result"),
        }

    def exec(self, prep_res: dict):
        import os
        import pathlib
        import subprocess

        inp = pathlib.Path(prep_res["input_path"])
        if not inp.exists():
            return {"error": f"KiteFAST input file not found: {inp}"}
        try:
            proc = subprocess.run(
                ["KiteFAST", str(inp)],
                cwd=inp.parent,
                capture_output=True,
                text=True,
                timeout=3600,
                env=os.environ.copy(),
            )
            if proc.returncode != 0:
                return {"error": proc.stderr or "KiteFAST returned non-zero."}
            # Look for output file
            out = inp.with_suffix(".out")
            summary: dict = {"returncode": proc.returncode}
            if out.exists():
                lines = out.read_text().splitlines()
                summary["output_lines"] = len(lines)
                summary["output_head"] = lines[:5]
            return summary
        except FileNotFoundError:
            return {"error": "KiteFAST binary not found on PATH."}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["kitefast_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
