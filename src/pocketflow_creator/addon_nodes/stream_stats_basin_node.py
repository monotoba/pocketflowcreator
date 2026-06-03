"""USGS StreamStats watershed delineation and statistics node —
calls the StreamStats REST API to delineate a watershed and compute
basin characteristics and flow statistics for a pour point."""

__node_meta__ = {
    "node": "StreamStats Basin",
    "category": "Hydrology / Water",
    "version": "1.0.0",
    "description": "Delineates a watershed and computes basin characteristics via the USGS StreamStats REST API.",
    "tags": ["streamstats", "usgs", "watershed", "basin", "hydrology", "delineation"],
    "license": "MIT",
    "website": "https://streamstats.usgs.gov/docs/streamstatsservices/",
    "actions": ["default", "error"],
    "properties": {
        "lat_key": {
            "type": "string",
            "default": "lat",
            "description": "Shared-store key holding pour-point latitude.",
        },
        "lon_key": {
            "type": "string",
            "default": "lon",
            "description": "Shared-store key holding pour-point longitude.",
        },
        "state_cd": {
            "type": "string",
            "default": "VA",
            "description": "Two-letter state code (upper-case) for the StreamStats region.",
        },
        "result_key": {
            "type": "string",
            "default": "streamstats_result",
            "description": "Shared-store key to write watershed delineation and basin characteristics.",
        },
    },
    "color": "#1565c0",
}

__node_icon__ = None


class StreamStatsBasinNode:
    """Delineate a watershed with USGS StreamStats and return basin characteristics."""

    _BASE = "https://streamstats.usgs.gov/streamstatsservices"

    def prep(self, shared: dict) -> dict:
        return {
            "lat": float(shared.get("lat", 38.9072)),
            "lon": float(shared.get("lon", -77.0369)),
            "state_cd": str(shared.get("streamstats_state_cd", "VA")).upper(),
            "result_key": shared.get("streamstats_result_key", "streamstats_result"),
        }

    def exec(self, prep_res: dict):
        import json
        import urllib.parse
        import urllib.request

        lat, lon, state = prep_res["lat"], prep_res["lon"], prep_res["state_cd"]
        try:
            params = urllib.parse.urlencode(
                {
                    "rcode": state,
                    "xlocation": lon,
                    "ylocation": lat,
                    "crs": 4326,
                    "includeparameters": "true",
                    "includeflowtypes": "false",
                    "includefeatures": "false",
                    "simplify": "true",
                }
            )
            url = f"{self._BASE}/watershed.geojson?{params}"
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read())
            params_out = {}
            for p in data.get("parameters", []):
                params_out[p["code"]] = {
                    "name": p["name"],
                    "value": p["value"],
                    "unit": p.get("units", ""),
                }
            return {
                "state": state,
                "lat": lat,
                "lon": lon,
                "basin_parameters": params_out,
                "workspace_id": data.get("workspaceID", ""),
            }
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["streamstats_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
