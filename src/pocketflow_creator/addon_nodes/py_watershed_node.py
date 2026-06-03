"""USGS pywatershed hydrologic process model node — runs a pywatershed
NHM (National Hydrologic Model) domain simulation.
Install: pip install pywatershed"""

__node_meta__ = {
    "node": "pywatershed",
    "category": "Hydrology / Water",
    "version": "1.0.0",
    "description": "Runs a USGS pywatershed / NHM hydrologic simulation and returns streamflow and storage outputs.",
    "tags": ["pywatershed", "nhm", "usgs", "hydrology", "streamflow", "water-balance"],
    "license": "MIT",
    "website": "https://pywatershed.readthedocs.io/",
    "repo": "https://github.com/EC-USGS/pywatershed",
    "actions": ["default", "error"],
    "properties": {
        "domain_dir_key": {
            "type": "string",
            "default": "pws_domain_dir",
            "description": "Shared-store key holding the pywatershed domain directory path.",
        },
        "control_file_key": {
            "type": "string",
            "default": "pws_control_file",
            "description": "Shared-store key holding the control file path (optional; defaults to control.yml in domain_dir).",
        },
        "result_key": {
            "type": "string",
            "default": "pws_result",
            "description": "Shared-store key to write run summary and output file paths.",
        },
    },
    "color": "#1565c0",
}

__node_icon__ = None


class PyWatershedNode:
    """Run a pywatershed simulation and return output file paths."""

    def prep(self, shared: dict) -> dict:
        import pathlib

        domain_dir = pathlib.Path(shared.get("pws_domain_dir", ""))
        control_file = shared.get("pws_control_file", "") or str(domain_dir / "control.yml")
        return {
            "domain_dir": str(domain_dir),
            "control_file": control_file,
            "result_key": shared.get("pws_result_key", "pws_result"),
        }

    def exec(self, prep_res: dict):
        import pathlib

        domain_dir = pathlib.Path(prep_res["domain_dir"])
        if not domain_dir.is_dir():
            return {"error": f"pywatershed domain directory not found: {domain_dir}"}
        try:
            import pywatershed as pws  # type: ignore[import]
        except ImportError:
            return {"error": "pywatershed not installed.  Run: pip install pywatershed"}
        try:
            control = pws.Control.load_prms(prep_res["control_file"])
            params = pws.Parameters.from_netcdf(str(domain_dir / "parameters.nc"))
            # Build a simple NHM simulation
            sim = pws.Model(
                [pws.PRMSSolarGeometry, pws.PRMSAtmosphere, pws.PRMSSoilzone, pws.PRMSRunoff, pws.PRMSChannel],
                control=control,
                parameters=params,
            )
            sim.initialize_netcdf(domain_dir / "output")
            for _ in sim.advance_n_timesteps(control.n_times):
                sim.calculate()
                sim.output()
            sim.finalize()
            out_files = sorted(str(p) for p in (domain_dir / "output").glob("*.nc"))
            return {"n_timesteps": int(control.n_times), "output_files": out_files[:10]}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["pws_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
