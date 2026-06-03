"""USGS NWIS (National Water Information System) query node — searches
for sites and retrieves statistical or peak-flow records via the NWIS
web services REST API."""

__node_meta__ = {
    "node": "NWIS Query",
    "category": "Hydrology / Water",
    "version": "1.0.0",
    "description": "Searches USGS NWIS for monitoring sites and retrieves statistical or peak-flow records.",
    "tags": ["nwis", "usgs", "hydrology", "peak-flow", "statistics", "water-records"],
    "license": "MIT",
    "website": "https://nwis.waterdata.usgs.gov/",
    "actions": ["default", "error"],
    "properties": {
        "query_type": {
            "type": "choice",
            "default": "site",
            "choices": ["site", "peak", "stat"],
            "description": "Type of NWIS query: site metadata, peak flow record, or statistics.",
        },
        "site_key": {
            "type": "string",
            "default": "usgs_site",
            "description": "Shared-store key holding the USGS site number.",
        },
        "state_cd": {
            "type": "string",
            "default": "",
            "description": "Two-letter state code for site searches (e.g. 'va', 'md').",
        },
        "result_key": {
            "type": "string",
            "default": "nwis_result",
            "description": "Shared-store key to write the NWIS response.",
        },
    },
    "color": "#0d47a1",
}

__node_icon__ = None


class NWISQueryNode:
    """Query USGS NWIS web services for site, peak-flow, or statistics data."""

    _BASE = "https://nwis.waterservices.usgs.gov/nwis"
    _PEAK = "https://nwis.waterdata.usgs.gov/nwis/peak"

    def prep(self, shared: dict) -> dict:
        return {
            "query_type": shared.get("nwis_query_type", "site"),
            "site": str(shared.get("usgs_site", "01646500")),
            "state_cd": str(shared.get("nwis_state_cd", "")),
            "result_key": shared.get("nwis_result_key", "nwis_result"),
        }

    def exec(self, prep_res: dict):
        import urllib.parse
        import urllib.request

        qt = prep_res["query_type"]
        site = prep_res["site"]
        try:
            if qt == "peak":
                params = urllib.parse.urlencode(
                    {
                        "site_no": site,
                        "agency_cd": "USGS",
                        "format": "rdb",
                    }
                )
                url = f"{self._PEAK}?{params}"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=30) as r:
                    text = r.read().decode()
                lines = [line for line in text.splitlines() if not line.startswith("#") and line.strip()]
                return {"site": site, "query": "peak", "raw_lines": lines[:50]}
            else:
                # site or stat
                endpoint = "site" if qt == "site" else "stat"
                kw: dict = {"format": "rdb"}
                if site:
                    kw["sites"] = site
                if prep_res["state_cd"]:
                    kw["stateCd"] = prep_res["state_cd"]
                params = urllib.parse.urlencode(kw)
                url = f"{self._BASE}/{endpoint}/?{params}"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=30) as r:
                    text = r.read().decode()
                lines = [line for line in text.splitlines() if not line.startswith("#") and line.strip()]
                return {"site": site, "query": qt, "raw_lines": lines[:50]}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["nwis_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
