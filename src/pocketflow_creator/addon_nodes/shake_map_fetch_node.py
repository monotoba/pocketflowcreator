"""USGS ShakeMap fetch node — retrieves ShakeMap products (grid, contours,
PGA/PGV rasters) for a specific earthquake event ID from the USGS
ComCat / Product Distribution Layer API."""

__node_meta__ = {
    "node":        "ShakeMap Fetch",
    "category":    "Geospatial",
    "version":     "1.0.0",
    "description": "Downloads ShakeMap grid/contour products for a USGS earthquake event ID.",
    "tags":        ["shakemap", "usgs", "earthquake", "ground-motion", "hazard", "geospatial"],
    "license":     "MIT",
    "website":     "https://earthquake.usgs.gov/data/shakemap/",
    "actions":     ["default", "error"],
    "properties": {
        "event_id_key": {
            "type":        "string",
            "default":     "eq_event_id",
            "description": "Shared-store key holding the USGS event ID (e.g. 'us7000n7n5').",
        },
        "product_type": {
            "type":        "choice",
            "default":     "download/grid.xml",
            "choices":     [
                "download/grid.xml",
                "download/contour_pga.json",
                "download/contour_pgv.json",
                "download/pga.jpg",
                "download/info.json",
            ],
            "description": "ShakeMap product to fetch.",
        },
        "output_dir_key": {
            "type":        "string",
            "default":     "shakemap_output_dir",
            "description": "Shared-store key holding local directory to save the product.",
        },
        "result_key": {
            "type":        "string",
            "default":     "shakemap_result",
            "description": "Shared-store key to write download status and file path.",
        },
    },
    "color": "#bf360c",
}

__node_icon__ = None


class ShakeMapFetchNode:
    """Fetch a ShakeMap product file for an earthquake event."""

    _BASE = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    _PDL  = "https://earthquake.usgs.gov/product/shakemap"

    def prep(self, shared: dict) -> dict:
        import tempfile
        return {
            "event_id":   shared.get("eq_event_id", ""),
            "product":    shared.get("shakemap_product_type", "download/grid.xml"),
            "output_dir": shared.get("shakemap_output_dir", tempfile.mkdtemp(prefix="shakemap_")),
            "result_key": shared.get("shakemap_result_key", "shakemap_result"),
        }

    def exec(self, prep_res: dict):
        import json
        import pathlib
        import urllib.request
        event_id = prep_res["event_id"]
        if not event_id:
            return {"error": "No earthquake event ID provided."}
        # Get event detail JSON to find ShakeMap product URL
        detail_url = f"{self._BASE}?eventid={event_id}&format=geojson"
        try:
            req = urllib.request.Request(detail_url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                detail = json.loads(r.read())
            products = detail.get("properties", {}).get("products", {})
            shakemap_list = products.get("shakemap", [])
            if not shakemap_list:
                return {"error": f"No ShakeMap product for event {event_id}."}
            sm = shakemap_list[0]
            product_type = prep_res["product"]
            contents = sm.get("contents", {})
            if product_type not in contents:
                available = list(contents.keys())[:10]
                return {"error": f"Product '{product_type}' not available. Available: {available}"}
            dl_url = contents[product_type]["url"]
            fname  = pathlib.Path(product_type).name
            out_p  = pathlib.Path(prep_res["output_dir"]) / fname
            out_p.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(dl_url, str(out_p))
            return {"event_id": event_id, "product": product_type, "file": str(out_p)}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["shakemap_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
