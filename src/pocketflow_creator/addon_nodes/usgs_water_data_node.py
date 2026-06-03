"""USGS Water Data REST API node — queries instantaneous or daily
streamflow, stage, and water-quality data from waterservices.usgs.gov.
No API key required."""

__node_meta__ = {
    "node": "USGS Water Data",
    "category": "Hydrology / Water",
    "version": "1.0.0",
    "description": "Fetches USGS streamgage instantaneous or daily values from waterservices.usgs.gov.",
    "tags": ["usgs", "streamflow", "hydrology", "water-data", "rest-api"],
    "license": "MIT",
    "website": "https://waterservices.usgs.gov/",
    "actions": ["default", "error"],
    "properties": {
        "site_key": {
            "type": "string",
            "default": "usgs_site",
            "description": "Shared-store key holding the USGS site number (e.g. '01646500').",
        },
        "param_cd": {
            "type": "string",
            "default": "00060",
            "description": "USGS parameter code (00060=discharge cfs, 00065=gage height ft).",
        },
        "period": {
            "type": "string",
            "default": "P7D",
            "description": "ISO 8601 period string (e.g. P7D = 7 days, P1Y = 1 year).",
        },
        "service": {
            "type": "choice",
            "default": "iv",
            "choices": ["iv", "dv"],
            "description": "iv = instantaneous values (~15-min), dv = daily values.",
        },
        "result_key": {
            "type": "string",
            "default": "usgs_water",
            "description": "Shared-store key to write the time-series data.",
        },
    },
    "color": "#1565c0",
}

__node_icon__ = None


class USGSWaterDataNode:
    """Download USGS streamgage time-series data."""

    _BASE = "https://waterservices.usgs.gov/nwis"

    def prep(self, shared: dict) -> dict:
        return {
            "site": str(shared.get("usgs_site", "01646500")),
            "param_cd": str(shared.get("usgs_param_cd", "00060")),
            "period": str(shared.get("usgs_period", "P7D")),
            "service": str(shared.get("usgs_service", "iv")),
            "result_key": shared.get("usgs_water_key", "usgs_water"),
        }

    def exec(self, prep_res: dict):
        import json
        import urllib.parse
        import urllib.request

        params = urllib.parse.urlencode(
            {
                "sites": prep_res["site"],
                "parameterCd": prep_res["param_cd"],
                "period": prep_res["period"],
                "format": "json",
            }
        )
        url = f"{self._BASE}/{prep_res['service']}/?{params}"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            ts = data["value"]["timeSeries"]
            if not ts:
                return {"error": f"No data returned for site {prep_res['site']}."}
            series = ts[0]
            values = [{"datetime": v["dateTime"], "value": v["value"]} for v in series["values"][0]["value"]]
            return {
                "site": prep_res["site"],
                "param": series["variable"]["variableName"],
                "unit": series["variable"]["unit"]["unitCode"],
                "n_records": len(values),
                "values": values[-100:],  # last 100 records
            }
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["usgs_water_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
