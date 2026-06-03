"""USGS Elevation Point Query Service (EPQS) node — returns the
ground elevation for a single lat/lon coordinate from the USGS
National Elevation Dataset REST API.  No key required."""

__node_meta__ = {
    "node":        "USGS Elevation Point",
    "category":    "Geospatial",
    "version":     "1.0.0",
    "description": "Returns ground elevation (feet or meters) for a lat/lon point using the USGS EPQS REST API.",
    "tags":        ["usgs", "elevation", "epqs", "ned", "dem", "geospatial"],
    "license":     "MIT",
    "website":     "https://apps.nationalmap.gov/epqs/",
    "actions":     ["default", "error"],
    "properties": {
        "lat_key": {
            "type":        "string",
            "default":     "lat",
            "description": "Shared-store key holding latitude (decimal degrees).",
        },
        "lon_key": {
            "type":        "string",
            "default":     "lon",
            "description": "Shared-store key holding longitude (decimal degrees).",
        },
        "units": {
            "type":        "choice",
            "default":     "Meters",
            "choices":     ["Meters", "Feet"],
            "description": "Elevation units.",
        },
        "result_key": {
            "type":        "string",
            "default":     "elevation_result",
            "description": "Shared-store key to write the elevation dict.",
        },
    },
    "color": "#33691e",
}

__node_icon__ = None


class USGSElevationPointNode:
    """Query USGS EPQS for elevation at a single point."""

    _API = "https://epqs.nationalmap.gov/v1/json"

    def prep(self, shared: dict) -> dict:
        return {
            "lat":        float(shared.get("lat", 38.9072)),
            "lon":        float(shared.get("lon", -77.0369)),
            "units":      shared.get("epqs_units", "Meters"),
            "result_key": shared.get("elevation_result_key", "elevation_result"),
        }

    def exec(self, prep_res: dict):
        import json
        import urllib.parse
        import urllib.request
        params = urllib.parse.urlencode({
            "x":           prep_res["lon"],
            "y":           prep_res["lat"],
            "units":       prep_res["units"],
            "output":      "json",
        })
        url = f"{self._API}?{params}"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
            elev = data.get("value", data.get("Elevation_Query", {}).get("Elevation"))
            return {
                "lat":       prep_res["lat"],
                "lon":       prep_res["lon"],
                "elevation": float(elev) if elev is not None else None,
                "units":     prep_res["units"],
            }
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["epqs_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
