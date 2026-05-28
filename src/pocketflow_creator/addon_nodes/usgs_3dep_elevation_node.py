"""USGS 3DEP (3D Elevation Program) DEM download node — retrieves a
Digital Elevation Model raster for a bounding box from the USGS 3DEP
WCS (Web Coverage Service)."""

__node_meta__ = {
    "node":        "USGS 3DEP Elevation",
    "category":    "Geospatial",
    "version":     "1.0.0",
    "description": "Downloads a 3DEP DEM raster for a bounding box via the USGS WCS and saves as GeoTIFF.",
    "tags":        ["usgs", "3dep", "dem", "elevation", "lidar", "geospatial", "raster"],
    "license":     "MIT",
    "website":     "https://www.usgs.gov/3d-elevation-program",
    "actions":     ["default", "error"],
    "properties": {
        "bbox_key": {
            "type":        "string",
            "default":     "bbox",
            "description": "Shared-store key holding bounding box [west, south, east, north] in decimal degrees.",
        },
        "resolution": {
            "type":        "choice",
            "default":     "1",
            "choices":     ["1", "3", "10", "30"],
            "description": "DEM resolution in arc-seconds (1, 3, 10, or 30).",
        },
        "output_path_key": {
            "type":        "string",
            "default":     "dem_output_path",
            "description": "Shared-store key holding the output GeoTIFF path.",
        },
        "result_key": {
            "type":        "string",
            "default":     "dem_result",
            "description": "Shared-store key to write download status and file path.",
        },
    },
    "color": "#33691e",
}

__node_icon__ = None


class USGS3DEPElevationNode:
    """Download a 3DEP DEM tile from the USGS WCS service."""

    # USGS 3DEP WCS endpoint
    _WCS = "https://elevation.nationalmap.gov/arcgis/services/3DEPElevation/ImageServer/WCSServer"

    def prep(self, shared: dict) -> dict:
        import pathlib, tempfile
        bbox = shared.get("bbox", [-77.1, 38.85, -77.0, 38.95])
        out = shared.get("dem_output_path", str(pathlib.Path(tempfile.mkdtemp()) / "dem.tif"))
        return {
            "bbox":        bbox,
            "resolution":  str(shared.get("dem_resolution", "1")),
            "output_path": out,
            "result_key":  shared.get("dem_result_key", "dem_result"),
        }

    def exec(self, prep_res: dict):
        import urllib.request, urllib.parse, pathlib
        bbox  = prep_res["bbox"]
        res   = prep_res["resolution"]
        out_p = pathlib.Path(prep_res["output_path"])
        out_p.parent.mkdir(parents=True, exist_ok=True)
        # Map arc-second resolution to coverage name
        cov_map = {"1": "DEP3Elevation_1", "3": "DEP3Elevation", "10": "DEP3Elevation", "30": "DEP3Elevation"}
        coverage = cov_map.get(res, "DEP3Elevation")
        # Estimate pixel count (keep reasonable)
        import math
        deg_w = abs(bbox[2] - bbox[0])
        deg_h = abs(bbox[3] - bbox[1])
        arc_sec = float(res)
        width  = max(1, int(math.ceil(deg_w * 3600 / arc_sec)))
        height = max(1, int(math.ceil(deg_h * 3600 / arc_sec)))
        if width > 4096 or height > 4096:
            return {"error": f"Bounding box too large for {res}″ DEM (would be {width}×{height}px). Reduce bbox."}
        params = urllib.parse.urlencode({
            "SERVICE":    "WCS",
            "VERSION":    "1.0.0",
            "REQUEST":    "GetCoverage",
            "coverage":   coverage,
            "CRS":        "EPSG:4326",
            "BBOX":       f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
            "WIDTH":      width,
            "HEIGHT":     height,
            "FORMAT":     "GeoTIFF",
        })
        url = f"{self._WCS}?{params}"
        try:
            urllib.request.urlretrieve(url, str(out_p))
            return {"output_path": str(out_p), "width_px": width, "height_px": height}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["dem_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
