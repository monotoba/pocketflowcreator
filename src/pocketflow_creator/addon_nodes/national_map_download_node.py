"""USGS National Map download node — queries the TNM (The National Map)
API for available data products within a bounding box and optionally
downloads the first result."""

__node_meta__ = {
    "node":        "National Map Download",
    "category":    "Geospatial",
    "version":     "1.0.0",
    "description": "Searches The National Map API for available datasets in a bounding box and optionally downloads them.",
    "tags":        ["usgs", "national-map", "tnm", "elevation", "topo", "geospatial", "download"],
    "license":     "MIT",
    "website":     "https://apps.nationalmap.gov/tnmaccess/",
    "actions":     ["default", "error"],
    "properties": {
        "bbox_key": {
            "type":        "string",
            "default":     "bbox",
            "description": "Shared-store key holding bounding box as [west, south, east, north] in decimal degrees.",
        },
        "dataset": {
            "type":        "choice",
            "default":     "Digital Elevation Model (DEM) 1 meter",
            "choices":     [
                "Digital Elevation Model (DEM) 1 meter",
                "National Hydrography Dataset (NHD)",
                "National Structures Dataset",
                "National Transportation Dataset",
                "USGS Topographic Maps",
            ],
            "description": "Dataset type to search.",
        },
        "download": {
            "type":        "bool",
            "default":     "false",
            "description": "If true, download the first result to output_dir.",
        },
        "output_dir_key": {
            "type":        "string",
            "default":     "tnm_output_dir",
            "description": "Shared-store key holding the local directory for downloads.",
        },
        "result_key": {
            "type":        "string",
            "default":     "tnm_result",
            "description": "Shared-store key to write product list and download path.",
        },
    },
    "color": "#1a237e",
}

__node_icon__ = None


class NationalMapDownloadNode:
    """Search and optionally download USGS National Map products."""

    _API = "https://tnmaccess.nationalmap.gov/api/v1/products"

    def prep(self, shared: dict) -> dict:
        return {
            "bbox":       shared.get("bbox", [-77.5, 38.5, -77.0, 39.0]),
            "dataset":    shared.get("tnm_dataset", "Digital Elevation Model (DEM) 1 meter"),
            "download":   bool(shared.get("tnm_download", False)),
            "output_dir": shared.get("tnm_output_dir", "."),
            "result_key": shared.get("tnm_result_key", "tnm_result"),
        }

    def exec(self, prep_res: dict):
        import json, urllib.request, urllib.parse, pathlib
        bbox = prep_res["bbox"]
        try:
            params = urllib.parse.urlencode({
                "datasets": prep_res["dataset"],
                "bbox":     ",".join(str(c) for c in bbox),
                "max":      10,
                "offset":   0,
                "outputFormat": "JSON",
            })
            url = f"{self._API}?{params}"
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            items = data.get("items", [])
            products = [
                {"title": it.get("title"), "url": it.get("downloadURL"), "size_b": it.get("sizeInBytes")}
                for it in items
            ]
            result: dict = {"n_products": len(products), "products": products}
            if prep_res["download"] and products and products[0]["url"]:
                dl_url = products[0]["url"]
                fname = pathlib.Path(dl_url).name
                out_path = pathlib.Path(prep_res["output_dir"]) / fname
                urllib.request.urlretrieve(dl_url, out_path)
                result["downloaded"] = str(out_path)
            return result
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["tnm_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
