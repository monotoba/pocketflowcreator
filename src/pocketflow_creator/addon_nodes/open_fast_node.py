"""NREL OpenFAST wind-turbine aero-elastic simulation node — runs
OpenFAST from a .fst file and returns key rotor performance metrics.
Requires OpenFAST binary on PATH or openfast-toolbox for post-processing.
Install tools: pip install openfast-toolbox"""

__node_meta__ = {
    "node":        "OpenFAST",
    "category":    "Wind Energy",
    "version":     "1.0.0",
    "description": "Runs an NREL OpenFAST wind turbine aero-elastic simulation and returns rotor power and loads.",
    "tags":        ["openfast", "wind-energy", "aero-elastic", "nrel", "turbine"],
    "license":     "MIT",
    "website":     "https://openfast.readthedocs.io/",
    "repo":        "https://github.com/OpenFAST/openfast",
    "actions":     ["default", "error"],
    "properties": {
        "fst_path_key": {
            "type":        "string",
            "default":     "openfast_fst_path",
            "description": "Shared-store key holding path to the .fst OpenFAST input file.",
        },
        "result_key": {
            "type":        "string",
            "default":     "openfast_result",
            "description": "Shared-store key to write summarised output (RtAeroCp, RotSpeed, etc.).",
        },
    },
    "color": "#1b5e20",
}

__node_icon__ = None


class OpenFASTNode:
    """Run an OpenFAST simulation and return mean rotor metrics."""

    def prep(self, shared: dict) -> dict:
        return {
            "fst_path":   shared.get("openfast_fst_path", ""),
            "result_key": shared.get("openfast_result_key", "openfast_result"),
        }

    def exec(self, prep_res: dict):
        import os
        import pathlib
        import subprocess
        fst_path = pathlib.Path(prep_res["fst_path"])
        if not fst_path.exists():
            return {"error": f".fst file not found: {fst_path}"}
        try:
            proc = subprocess.run(
                ["openfast", str(fst_path)],
                cwd=fst_path.parent, capture_output=True, text=True,
                timeout=3600, env=os.environ.copy(),
            )
            if proc.returncode != 0:
                return {"error": proc.stderr or "openfast returned non-zero."}
            # Parse .outb with openfast_toolbox if available
            out_dat = fst_path.with_suffix(".out")
            summary: dict = {"returncode": proc.returncode}
            try:
                from openfast_toolbox.io import FASTInputFile  # type: ignore[import]
                if out_dat.exists():
                    data = FASTInputFile(str(out_dat)).toDataFrame()
                    for col in ["RtAeroCp_[-]", "RotSpeed_[rpm]", "GenPwr_[kW]"]:
                        if col in data.columns:
                            summary[col.split("_")[0]] = float(data[col].mean())
            except ImportError:
                summary["note"] = "Install openfast-toolbox for detailed parsing."
            return summary
        except FileNotFoundError:
            return {"error": "openfast binary not found on PATH."}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["openfast_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
