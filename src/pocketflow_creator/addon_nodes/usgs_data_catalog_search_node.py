"""USGS ScienceBase data catalog search node — queries the USGS
ScienceBase Catalog REST API for datasets, reports, and data releases
matching a keyword query."""

__node_meta__ = {
    "node":        "USGS Data Catalog Search",
    "category":    "Data Catalog",
    "version":     "1.0.0",
    "description": "Searches the USGS ScienceBase Catalog for datasets and data releases by keyword.",
    "tags":        ["usgs", "sciencebase", "data-catalog", "metadata", "search", "open-data"],
    "license":     "MIT",
    "website":     "https://www.sciencebase.gov/catalog/",
    "actions":     ["default", "error"],
    "properties": {
        "query_key": {
            "type":        "string",
            "default":     "sciencebase_query",
            "description": "Shared-store key holding the keyword search string.",
        },
        "max_results": {
            "type":        "integer",
            "default":     "20",
            "description": "Maximum number of catalog items to return.",
        },
        "fields": {
            "type":        "string",
            "default":     "id,title,summary,link",
            "description": "Comma-separated ScienceBase item fields to include in results.",
        },
        "result_key": {
            "type":        "string",
            "default":     "sciencebase_result",
            "description": "Shared-store key to write the search results list.",
        },
    },
    "color": "#1a237e",
}

__node_icon__ = None


class USGSDataCatalogSearchNode:
    """Search USGS ScienceBase and return matching catalog items."""

    _API = "https://www.sciencebase.gov/catalog/items"

    def prep(self, shared: dict) -> dict:
        return {
            "query":      str(shared.get("sciencebase_query", "")),
            "max":        int(shared.get("sciencebase_max_results", 20)),
            "fields":     str(shared.get("sciencebase_fields", "id,title,summary,link")),
            "result_key": shared.get("sciencebase_result_key", "sciencebase_result"),
        }

    def exec(self, prep_res: dict):
        import json, urllib.request, urllib.parse
        if not prep_res["query"]:
            return {"error": "No search query provided."}
        params = urllib.parse.urlencode({
            "q":      prep_res["query"],
            "max":    prep_res["max"],
            "fields": prep_res["fields"],
            "format": "json",
        })
        url = f"{self._API}?{params}"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            items = data.get("items", [])
            results = []
            for item in items:
                results.append({
                    "id":      item.get("id"),
                    "title":   item.get("title"),
                    "summary": (item.get("summary") or "")[:200],
                    "url":     item.get("link", {}).get("url", ""),
                })
            return {
                "query":    prep_res["query"],
                "n_items":  len(results),
                "items":    results,
                "total":    data.get("total", len(results)),
            }
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["sciencebase_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
