"""USGS Earthquake catalog node — queries the USGS ComCat / FDSN
event web service for earthquake events within a bounding box and
time range.  No API key required."""

__node_meta__ = {
    "node": "Earthquake Catalog",
    "category": "Geospatial",
    "version": "1.0.0",
    "description": "Fetches earthquake events from the USGS ComCat / FDSN API by bounding box, time range, and magnitude.",
    "tags": ["usgs", "earthquake", "seismology", "comcat", "fdsn", "geospatial"],
    "license": "MIT",
    "website": "https://earthquake.usgs.gov/fdsnws/event/1/",
    "actions": ["default", "error"],
    "properties": {
        "bbox_key": {
            "type": "string",
            "default": "bbox",
            "description": "Shared-store key holding bounding box [west, south, east, north].",
        },
        "start_time": {
            "type": "string",
            "default": "2024-01-01",
            "description": "Start date/time ISO 8601 (e.g. 2024-01-01).",
        },
        "end_time": {
            "type": "string",
            "default": "2024-12-31",
            "description": "End date/time ISO 8601.",
        },
        "min_magnitude": {
            "type": "number",
            "default": "2.5",
            "description": "Minimum event magnitude.",
        },
        "max_events": {
            "type": "integer",
            "default": "100",
            "description": "Maximum number of events to return.",
        },
        "result_key": {
            "type": "string",
            "default": "earthquake_result",
            "description": "Shared-store key to write the event list.",
        },
    },
    "color": "#b71c1c",
}

__node_icon__ = None


class EarthquakeCatalogNode:
    """Fetch earthquake events from the USGS FDSN event service."""

    _API = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    def prep(self, shared: dict) -> dict:
        return {
            "bbox": shared.get("bbox", [-125, 24, -65, 50]),
            "start": shared.get("eq_start_time", "2024-01-01"),
            "end": shared.get("eq_end_time", "2024-12-31"),
            "min_mag": float(shared.get("eq_min_magnitude", 2.5)),
            "max_events": int(shared.get("eq_max_events", 100)),
            "result_key": shared.get("earthquake_result_key", "earthquake_result"),
        }

    def exec(self, prep_res: dict):
        import json
        import urllib.parse
        import urllib.request

        bbox = prep_res["bbox"]
        params = urllib.parse.urlencode(
            {
                "format": "geojson",
                "starttime": prep_res["start"],
                "endtime": prep_res["end"],
                "minlatitude": bbox[1],
                "maxlatitude": bbox[3],
                "minlongitude": bbox[0],
                "maxlongitude": bbox[2],
                "minmagnitude": prep_res["min_mag"],
                "limit": prep_res["max_events"],
                "orderby": "magnitude",
            }
        )
        url = f"{self._API}?{params}"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            features = data.get("features", [])
            events = []
            for f in features:
                p = f["properties"]
                c = f["geometry"]["coordinates"]
                events.append(
                    {
                        "id": f["id"],
                        "magnitude": p.get("mag"),
                        "place": p.get("place"),
                        "time": p.get("time"),
                        "lon": c[0],
                        "lat": c[1],
                        "depth_km": c[2],
                        "url": p.get("url"),
                    }
                )
            return {
                "n_events": len(events),
                "events": events,
                "bbox": bbox,
            }
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["earthquake_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
