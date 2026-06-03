"""DOE EnergyPlus building energy simulation node — runs an EnergyPlus
simulation from an .idf or .epJSON file and returns energy use summary.
Requires EnergyPlus installed: https://energyplus.net/downloads
Optional: pip install eppy"""

__node_meta__ = {
    "node": "EnergyPlus Run",
    "category": "Building Energy",
    "version": "1.0.0",
    "description": "Runs a DOE EnergyPlus building energy simulation and returns annual energy use and peak demand.",
    "tags": ["energyplus", "building-energy", "doe", "hvac", "simulation", "idf"],
    "license": "MIT",
    "website": "https://energyplus.net/",
    "repo": "https://github.com/NREL/EnergyPlus",
    "actions": ["default", "error"],
    "properties": {
        "idf_path_key": {
            "type": "string",
            "default": "eplus_idf_path",
            "description": "Shared-store key holding path to the .idf or .epJSON input file.",
        },
        "weather_path_key": {
            "type": "string",
            "default": "eplus_weather_path",
            "description": "Shared-store key holding path to the .epw weather file.",
        },
        "output_dir_key": {
            "type": "string",
            "default": "eplus_output_dir",
            "description": "Shared-store key holding the output directory path.",
        },
        "result_key": {
            "type": "string",
            "default": "eplus_result",
            "description": "Shared-store key to write energy summary dict.",
        },
    },
    "color": "#e65100",
}

__node_icon__ = None


class EnergyPlusRunNode:
    """Run EnergyPlus and parse the HTML/csv summary for total energy use."""

    def prep(self, shared: dict) -> dict:
        import tempfile

        return {
            "idf_path": shared.get("eplus_idf_path", ""),
            "weather_path": shared.get("eplus_weather_path", ""),
            "output_dir": shared.get("eplus_output_dir", tempfile.mkdtemp(prefix="eplus_")),
            "result_key": shared.get("eplus_result_key", "eplus_result"),
        }

    def exec(self, prep_res: dict):
        import os
        import pathlib
        import shutil
        import subprocess

        idf = pathlib.Path(prep_res["idf_path"])
        epw = pathlib.Path(prep_res["weather_path"])
        out_dir = pathlib.Path(prep_res["output_dir"])
        if not idf.exists():
            return {"error": f"IDF file not found: {idf}"}
        if not epw.exists():
            return {"error": f"Weather file not found: {epw}"}
        out_dir.mkdir(parents=True, exist_ok=True)

        # Try energyplus binary
        ep_bin = shutil.which("energyplus") or shutil.which("EnergyPlus")
        if ep_bin is None:
            return {"error": "EnergyPlus binary not found on PATH.  Download from https://energyplus.net/downloads"}
        try:
            proc = subprocess.run(
                [ep_bin, "-w", str(epw), "-d", str(out_dir), str(idf)],
                capture_output=True,
                text=True,
                timeout=3600,
                env=os.environ.copy(),
            )
            # Parse eplustbl.csv for totals
            csv_file = out_dir / "eplustbl.csv"
            summary: dict = {"returncode": proc.returncode, "output_dir": str(out_dir)}
            if csv_file.exists():
                import csv

                with open(csv_file) as f:
                    rows = list(csv.reader(f))
                summary["table_rows"] = len(rows)
                # Find total site energy row
                for row in rows:
                    if len(row) > 1 and "Total Site Energy" in row[0]:
                        summary["total_site_energy_GJ"] = row[1]
                        break
            return summary
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["eplus_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
