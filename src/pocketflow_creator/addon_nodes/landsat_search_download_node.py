"""USGS Landsat M2M API search and download node — searches the USGS
Machine-to-Machine (M2M) API for Landsat scenes and downloads them.
Requires a free USGS EarthExplorer account; set credentials in shared store."""

__node_meta__ = {
    "node": "Landsat Search & Download",
    "category": "Geospatial",
    "version": "1.0.0",
    "description": "Searches and downloads Landsat Collection 2 scenes from the USGS M2M API.",
    "tags": ["landsat", "usgs", "remote-sensing", "satellite", "m2m", "earth-observation"],
    "license": "MIT",
    "website": "https://m2m.cr.usgs.gov/",
    "actions": ["default", "error"],
    "properties": {
        "username_key": {
            "type": "string",
            "default": "usgs_username",
            "description": "Shared-store key holding USGS EarthExplorer username.",
        },
        "token_key": {
            "type": "string",
            "default": "usgs_token",
            "description": "Shared-store key holding USGS M2M API token (or password).",
        },
        "bbox_key": {
            "type": "string",
            "default": "bbox",
            "description": "Shared-store key holding bounding box [west, south, east, north].",
        },
        "dataset": {
            "type": "choice",
            "default": "landsat_ot_c2_l2",
            "choices": ["landsat_ot_c2_l2", "landsat_etm_c2_l2", "landsat_tm_c2_l2"],
            "description": "Landsat dataset alias (OLI/TIRS C2 L2, ETM+ C2 L2, TM C2 L2).",
        },
        "max_cloud_pct": {
            "type": "number",
            "default": "20",
            "description": "Maximum cloud cover percentage filter.",
        },
        "download": {
            "type": "bool",
            "default": "false",
            "description": "If true, request download URLs for the first matching scene.",
        },
        "result_key": {
            "type": "string",
            "default": "landsat_result",
            "description": "Shared-store key to write scene list and download URLs.",
        },
    },
    "color": "#1a237e",
}

__node_icon__ = None


class LandsatSearchDownloadNode:
    """Search USGS M2M API for Landsat scenes and optionally get download URLs."""

    _API = "https://m2m.cr.usgs.gov/api/api/json/stable"

    def prep(self, shared: dict) -> dict:
        return {
            "username": shared.get("usgs_username", ""),
            "token": shared.get("usgs_token", ""),
            "bbox": shared.get("bbox", [-77.5, 38.5, -77.0, 39.0]),
            "dataset": shared.get("landsat_dataset", "landsat_ot_c2_l2"),
            "max_cloud": float(shared.get("landsat_max_cloud_pct", 20)),
            "download": bool(shared.get("landsat_download", False)),
            "result_key": shared.get("landsat_result_key", "landsat_result"),
        }

    def exec(self, prep_res: dict):
        import json
        import urllib.request

        if not prep_res["username"] or not prep_res["token"]:
            return {"error": "USGS username and token required.  Get a token at https://m2m.cr.usgs.gov/"}

        def _post(endpoint: str, payload: dict, token: str = "") -> dict:
            req = urllib.request.Request(
                f"{self._API}/{endpoint}",
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "X-Auth-Token": token,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())

        try:
            # Authenticate
            login = _post("login-token", {"username": prep_res["username"], "token": prep_res["token"]})
            api_key = login.get("data", "")
            if not api_key:
                return {"error": f"Login failed: {login.get('errorMessage', 'unknown')}"}

            bbox = prep_res["bbox"]
            search_payload = {
                "datasetName": prep_res["dataset"],
                "spatialFilter": {
                    "filterType": "mbr",
                    "lowerLeft": {"latitude": bbox[1], "longitude": bbox[0]},
                    "upperRight": {"latitude": bbox[3], "longitude": bbox[2]},
                },
                "additionalCriteria": {
                    "filterType": "value",
                    "fieldId": "5e83d14fb9436d88",
                    "value": str(int(prep_res["max_cloud"])),
                    "operand": "<=",
                },
                "maxResults": 10,
                "startingNumber": 1,
            }
            search_res = _post("scene-search", search_payload, api_key)
            scenes = search_res.get("data", {}).get("results", [])
            result: dict = {
                "dataset": prep_res["dataset"],
                "n_scenes": len(scenes),
                "scenes": [
                    {"id": s["entityId"], "date": s.get("temporalCoverage", {}).get("startDate"), "cloud": s.get("cloudCover")} for s in scenes
                ],
            }
            if prep_res["download"] and scenes:
                dl_res = _post("download-options", {"datasetName": prep_res["dataset"], "entityIds": [scenes[0]["entityId"]]}, api_key)
                result["download_options"] = dl_res.get("data", [])[:5]
            _post("logout", {}, api_key)
            return result
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["landsat_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
