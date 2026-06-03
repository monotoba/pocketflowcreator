"""NASA Trick simulation framework node — builds and runs a Trick
simulation from a directory and returns logged variable data.
Requires Trick installed and on PATH."""

__node_meta__ = {
    "node": "Trick Simulation",
    "category": "Aerospace",
    "version": "1.0.0",
    "description": "Builds and runs a NASA Trick simulation, then reads logged variable data.",
    "tags": ["trick", "simulation", "nasa", "dynamics", "real-time"],
    "license": "MIT",
    "website": "https://nasa.github.io/trick/",
    "repo": "https://github.com/nasa/trick",
    "actions": ["default", "error"],
    "properties": {
        "sim_dir_key": {
            "type": "string",
            "default": "trick_sim_dir",
            "description": "Shared-store key holding the path to the Trick simulation directory.",
        },
        "input_file_key": {
            "type": "string",
            "default": "trick_input_file",
            "description": "Shared-store key holding the Python input file path (relative to sim_dir).",
        },
        "build": {
            "type": "bool",
            "default": "true",
            "description": "If true, run 'trick-CP' to build before running.",
        },
        "result_key": {
            "type": "string",
            "default": "trick_result",
            "description": "Shared-store key to write run status and log path.",
        },
    },
    "color": "#0d47a1",
}

__node_icon__ = None


class TrickSimulationNode:
    """Build (optional) and run a Trick simulation."""

    def prep(self, shared: dict) -> dict:
        return {
            "sim_dir": shared.get("trick_sim_dir", ""),
            "input_file": shared.get("trick_input_file", "RUN_test/input.py"),
            "build": bool(shared.get("trick_build", True)),
            "result_key": shared.get("trick_result_key", "trick_result"),
        }

    def exec(self, prep_res: dict):
        import os
        import pathlib
        import subprocess

        sim_dir = pathlib.Path(prep_res["sim_dir"])
        if not sim_dir.is_dir():
            return {"error": f"Simulation directory not found: {sim_dir}"}
        env = os.environ.copy()
        try:
            if prep_res["build"]:
                build_proc = subprocess.run(
                    ["trick-CP"],
                    cwd=sim_dir,
                    capture_output=True,
                    text=True,
                    timeout=600,
                    env=env,
                )
                if build_proc.returncode != 0:
                    return {"error": f"trick-CP failed:\n{build_proc.stderr}"}
            run_proc = subprocess.run(
                [str(sim_dir / "S_main_Linux_x86_64.exe"), prep_res["input_file"]],
                cwd=sim_dir,
                capture_output=True,
                text=True,
                timeout=3600,
                env=env,
            )
            log_dir = sim_dir / "RUN_test"
            return {
                "returncode": run_proc.returncode,
                "log_dir": str(log_dir),
                "stdout_tail": run_proc.stdout[-2000:] if run_proc.stdout else "",
            }
        except FileNotFoundError:
            return {"error": "Trick binaries (trick-CP / S_main) not found on PATH."}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["trick_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
