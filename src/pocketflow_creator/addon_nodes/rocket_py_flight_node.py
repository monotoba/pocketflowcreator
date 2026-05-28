"""RocketPy 6-DOF rocket flight simulation node — runs a full 6-DOF
flight simulation using the RocketPy library.
Install: pip install rocketpy"""

__node_meta__ = {
    "node":        "RocketPy Flight",
    "category":    "Aerospace",
    "version":     "1.0.0",
    "description": "Runs a RocketPy 6-DOF rocket flight simulation and returns apogee, max speed, and flight time.",
    "tags":        ["rocketpy", "rocket", "6dof", "flight-simulation", "propulsion"],
    "license":     "MIT",
    "website":     "https://rocketpy.me/",
    "repo":        "https://github.com/RocketPy-Team/RocketPy",
    "actions":     ["default", "error"],
    "properties": {
        "flight_key": {
            "type":        "string",
            "default":     "rocketpy_flight",
            "description": "Shared-store key holding a configured rocketpy.Flight instance.",
        },
        "result_key": {
            "type":        "string",
            "default":     "rocketpy_result",
            "description": "Shared-store key to write the summary dict.",
        },
    },
    "color": "#b71c1c",
}

__node_icon__ = None


class RocketPyFlightNode:
    """Simulate a rocket flight with RocketPy and collect key outcomes."""

    def prep(self, shared: dict) -> dict:
        return {
            "flight":     shared.get("rocketpy_flight"),
            "result_key": shared.get("rocketpy_result_key", "rocketpy_result"),
        }

    def exec(self, prep_res: dict):
        flight = prep_res["flight"]
        if flight is None:
            return {"error": "No rocketpy.Flight instance found in shared store."}
        try:
            import rocketpy  # type: ignore[import]  # noqa: F401
            apogee    = float(flight.apogee)
            max_speed = float(flight.maxSpeed)
            t_flight  = float(flight.tFinal)
            apogee_t  = float(flight.apogeeTime)
            return {
                "apogee_m":      round(apogee, 1),
                "max_speed_mps": round(max_speed, 2),
                "flight_time_s": round(t_flight, 2),
                "apogee_time_s": round(apogee_t, 2),
            }
        except ImportError:
            return {"error": "rocketpy not installed.  Run: pip install rocketpy"}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        if "error" in exec_res:
            shared["rocketpy_error"] = exec_res["error"]
            return "error"
        shared[prep_res["result_key"]] = exec_res
        return "default"
