"""NOAA/NWS weather node — queries the NOAA National Weather Service
REST API (api.weather.gov) for current conditions and forecasts.
No API key required; uses the public NWS JSON API."""

__node_meta__ = {
    "node": "NOAA Weather",
    "category": "Weather / Atmosphere",
    "version": "1.0.0",
    "description": "Fetches current NWS observations and the 7-day forecast for a latitude/longitude point.",
    "tags": ["noaa", "nws", "weather", "forecast", "rest-api", "atmosphere"],
    "license": "MIT",
    "website": "https://www.weather.gov/documentation/services-web-api",
    "actions": ["default", "error"],
    "properties": {
        "lat_key": {
            "type": "string",
            "default": "lat",
            "description": "Shared-store key holding latitude (decimal degrees).",
        },
        "lon_key": {
            "type": "string",
            "default": "lon",
            "description": "Shared-store key holding longitude (decimal degrees).",
        },
        "result_key": {
            "type": "string",
            "default": "noaa_weather",
            "description": "Shared-store key to write the weather dict.",
        },
    },
    "color": "#01579b",
}

__node_icon__ = None


class NOAAWeatherNode:
    """Fetch NWS forecast and latest observation for a lat/lon point."""

    _UA = "PocketFlowCreator/1.0 (github.com/you/pocketflow-creator)"

    def prep(self, shared: dict) -> dict:
        return {
            "lat": float(shared.get("lat", 38.9072)),
            "lon": float(shared.get("lon", -77.0369)),
            "result_key": shared.get("noaa_weather_key", "noaa_weather"),
        }

    def exec(self, prep_res: dict):
        import json
        import urllib.request

        lat, lon = prep_res["lat"], prep_res["lon"]
        headers = {"User-Agent": self._UA, "Accept": "application/geo+json"}

        def _get(url: str) -> dict:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read())

        try:
            # 1. Resolve to office/gridpoint
            meta = _get(f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}")
            props = meta["properties"]
            forecast_url = props["forecast"]
            obs_url = props.get("observationStations", "")

            # 2. 7-day forecast
            fc = _get(forecast_url)
            periods = [
                {
                    "name": p["name"],
                    "temperature": p["temperature"],
                    "unit": p["temperatureUnit"],
                    "wind": p["windSpeed"],
                    "short": p["shortForecast"],
                }
                for p in fc["properties"]["periods"][:7]
            ]

            result: dict = {"lat": lat, "lon": lon, "forecast": periods}

            # 3. Latest observation (best-effort)
            if obs_url:
                stations = _get(obs_url)
                first_station = stations["features"][0]["id"] if stations.get("features") else None
                if first_station:
                    obs = _get(f"{first_station}/observations/latest")
                    op = obs["properties"]
                    result["observation"] = {
                        "temp_c": op.get("temperature", {}).get("value"),
                        "humidity": op.get("relativeHumidity", {}).get("value"),
                        "wind_mps": op.get("windSpeed", {}).get("value"),
                        "condition": op.get("textDescription", ""),
                    }
            return result
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["noaa_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
