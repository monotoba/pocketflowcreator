"""NASA OpenVSP geometry node — opens or creates a VSP model, runs geometry
analysis, and exports surface/mesh files.  Requires OpenVSP with the
openvsp Python bindings installed."""

__node_meta__ = {
    "node":        "OpenVSP Geometry",
    "category":    "Aerospace",
    "version":     "1.0.0",
    "description": "Loads a VSP3 model, updates design variables, and exports geometry files.",
    "tags":        ["openvsp", "vsp", "geometry", "aerospace", "cad", "nasa"],
    "license":     "MIT",
    "website":     "https://openvsp.org/",
    "repo":        "https://github.com/OpenVSP/OpenVSP",
    "actions":     ["default", "error"],
    "properties": {
        "vsp3_path_key": {
            "type":        "string",
            "default":     "vsp3_path",
            "description": "Shared-store key holding the path to the .vsp3 model file.",
        },
        "export_format": {
            "type":        "choice",
            "default":     "stl",
            "choices":     ["stl", "degen_geom", "stp", "iges", "obj"],
            "description": "Geometry export format.",
        },
        "output_path_key": {
            "type":        "string",
            "default":     "vsp_output_path",
            "description": "Shared-store key to write the path of the exported file.",
        },
    },
    "color": "#1565c0",
}

__node_icon__ = None


class OpenVSPGeometryNode:
    """Load a VSP3 model and export geometry in the requested format."""

    def prep(self, shared: dict) -> dict:
        return {
            "vsp3_path":       shared.get("vsp3_path", ""),
            "export_format":   shared.get("vsp_export_format", "stl"),
            "output_path_key": shared.get("vsp_output_path_key", "vsp_output_path"),
        }

    def exec(self, prep_res: dict):
        vsp3_path = prep_res["vsp3_path"]
        if not vsp3_path:
            return {"error": "No .vsp3 file path provided."}
        try:
            import openvsp as vsp  # type: ignore[import]
        except ImportError:
            return {"error": "openvsp Python bindings not found.  Install OpenVSP and its Python API."}
        try:
            import pathlib
            vsp.ClearVSPModel()
            vsp.ReadVSPFile(vsp3_path)
            vsp.Update()
            stem = pathlib.Path(vsp3_path).stem
            fmt = prep_res["export_format"].lower()
            out = str(pathlib.Path(vsp3_path).parent / f"{stem}.{fmt}")
            if fmt == "stl":
                vsp.ExportFile(out, vsp.SET_ALL, vsp.EXPORT_STL)
            elif fmt == "stp":
                vsp.ExportFile(out, vsp.SET_ALL, vsp.EXPORT_STEP)
            elif fmt == "iges":
                vsp.ExportFile(out, vsp.SET_ALL, vsp.EXPORT_IGES)
            elif fmt == "obj":
                vsp.ExportFile(out, vsp.SET_ALL, vsp.EXPORT_OBJ)
            else:
                vsp.ExportFile(out, vsp.SET_ALL, vsp.EXPORT_DEGEN_GEOM_CSV)
            return {"output_path": out}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["vsp_error"] = exec_res["error"]
            return "error"
        shared[prep_res["output_path_key"]] = exec_res["output_path"]
        return "default"
