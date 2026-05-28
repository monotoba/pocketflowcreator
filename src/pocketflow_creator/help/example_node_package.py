"""Example PocketFlow Creator node package.

Copy this file to ~/.pocketflow_creator/nodes/ and rename it to match your
node class.  Edit __node_meta__ and the class below, then restart Creator
(or use Tools → Node Type Library → Install node package).

This example fetches current weather conditions for a city name stored in
the shared store, using the Open-Meteo API (no API key required).
"""

# ── Package and node metadata ─────────────────────────────────────────────────
# All fields are read by the node loader.  Only "node" and "category" are
# required; everything else falls back to a sensible default.

__node_meta__ = {
    # ── Identity ──────────────────────────────────────────────────────────
    "node":     "Weather Fetch",          # display name shown in palette
    "category": "Web / Search",           # palette / toolbar group

    # ── Package info ──────────────────────────────────────────────────────
    "version":             "1.0.0",
    "author":              "Your Name",
    "website":             "https://yoursite.example.com",
    "repo":                "https://github.com/you/weather-fetch-node",
    "description":         "Fetches current temperature for a city via Open-Meteo.",
    "tags":                ["weather", "api", "http", "example"],
    "license":             "MIT",
    "min_creator_version": "0.2.0",

    # ── Node behaviour ────────────────────────────────────────────────────
    "actions": ["default", "error"],
    "properties": {
        "city_key": {
            "type":        "string",
            "default":     "city",
            "description": "Shared-store key that holds the city name to look up.",
        },
        "result_key": {
            "type":        "string",
            "default":     "weather",
            "description": "Shared-store key to write the result dict into.",
        },
    },

    # ── Visual ────────────────────────────────────────────────────────────
    # Hex background colour for the auto-generated palette icon.
    # Remove this key (or set to None) to get the default grey.
    "color": "#0277bd",
}

# Optional: provide a custom icon draw function.
# Signature: (p: QPainter, sz: float, bg: QColor) -> None
# Set to None to use the auto-generated two-letter-initials icon.
__node_icon__ = None


# ── Node implementation ───────────────────────────────────────────────────────

class WeatherFetchNode:
    """Retrieves current temperature and weather code for a city.

    Calls the Open-Meteo geocoding API to resolve the city name to
    coordinates, then calls the forecast API for current conditions.

    Shared-store keys written
    -------------------------
    weather (configurable via ``result_key``)
        Dict with keys: ``city``, ``latitude``, ``longitude``,
        ``temperature_c``, ``weather_code``.
    """

    def prep(self, shared: dict) -> dict:
        city_key   = "city"    # In Creator these come from the Inspector
        result_key = "weather"
        return {
            "city":       shared.get(city_key, "London"),
            "result_key": result_key,
        }

    def exec(self, prep_res: dict) -> dict:
        city = prep_res["city"]
        try:
            import urllib.request
            import json

            # Step 1: Geocode the city name
            geo_url = (
                f"https://geocoding-api.open-meteo.com/v1/search"
                f"?name={city}&count=1&language=en&format=json"
            )
            with urllib.request.urlopen(geo_url, timeout=10) as resp:
                geo = json.loads(resp.read())
            if not geo.get("results"):
                raise ValueError(f"City not found: {city!r}")
            result = geo["results"][0]
            lat, lon = result["latitude"], result["longitude"]

            # Step 2: Fetch current weather
            wx_url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,weather_code"
            )
            with urllib.request.urlopen(wx_url, timeout=10) as resp:
                wx = json.loads(resp.read())
            current = wx["current"]

            return {
                "city":          city,
                "latitude":      lat,
                "longitude":     lon,
                "temperature_c": current["temperature_2m"],
                "weather_code":  current["weather_code"],
            }
        except Exception as exc:
            # Return an error dict rather than raising so post() can route
            return {"city": city, "error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        shared[prep_res["result_key"]] = exec_res
        return "error" if "error" in exec_res else "default"
