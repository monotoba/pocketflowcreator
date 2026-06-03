"""USGS ShakeMap scenario node — runs a local ShakeMap v4 scenario
simulation for a user-defined fault rupture.
Requires ShakeMap v4 installed: https://usgs.github.io/shakemap/"""

__node_meta__ = {
    "node":        "ShakeMap Scenario",
    "category":    "Geospatial",
    "version":     "1.0.0",
    "description": "Runs a USGS ShakeMap v4 scenario simulation for a fault rupture and returns output grid path.",
    "tags":        ["shakemap", "usgs", "scenario", "ground-motion", "hazard", "earthquake", "simulation"],
    "license":     "MIT",
    "website":     "https://usgs.github.io/shakemap/",
    "repo":        "https://github.com/usgs/shakemap",
    "actions":     ["default", "error"],
    "properties": {
        "event_dir_key": {
            "type":        "string",
            "default":     "shakemap_event_dir",
            "description": "Shared-store key holding the ShakeMap event directory path (contains event.xml).",
        },
        "commands": {
            "type":        "string",
            "default":     "select assemble model contour",
            "description": "Space-separated ShakeMap processing pipeline commands.",
        },
        "result_key": {
            "type":        "string",
            "default":     "shakemap_scenario_result",
            "description": "Shared-store key to write run status and output file paths.",
        },
    },
    "color": "#e65100",
}

__node_icon__ = None


class ShakeMapScenarioNode:
    """Run a ShakeMap v4 scenario pipeline for a local event directory."""

    def prep(self, shared: dict) -> dict:
        return {
            "event_dir": shared.get("shakemap_event_dir", ""),
            "commands":  shared.get("shakemap_commands", "select assemble model contour").split(),
            "result_key": shared.get("shakemap_scenario_result_key", "shakemap_scenario_result"),
        }

    def exec(self, prep_res: dict):
        import os
        import pathlib
        import subprocess
        event_dir = pathlib.Path(prep_res["event_dir"])
        if not event_dir.is_dir():
            return {"error": f"ShakeMap event directory not found: {event_dir}"}
        event_xml = event_dir / "event.xml"
        if not event_xml.exists():
            return {"error": "event.xml not found in event directory."}
        # Derive event ID from directory name
        event_id = event_dir.name
        results = []
        try:
            for cmd in prep_res["commands"]:
                proc = subprocess.run(
                    ["shake", event_id, cmd],
                    capture_output=True, text=True, timeout=1800,
                    env=os.environ.copy(),
                )
                results.append({"command": cmd, "returncode": proc.returncode, "stderr_tail": proc.stderr[-300:]})
                if proc.returncode != 0:
                    return {"error": f"shake {cmd} failed.", "steps": results}
            # List output files
            out_dir = event_dir / "current"
            output_files = sorted(str(p) for p in out_dir.glob("*")) if out_dir.is_dir() else []
            return {"event_id": event_id, "steps": results, "output_files": output_files[:20]}
        except FileNotFoundError:
            return {"error": "ShakeMap 'shake' command not found on PATH.  Install ShakeMap v4."}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["shakemap_scenario_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
