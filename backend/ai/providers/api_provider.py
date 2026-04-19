from typing import List, Dict, Any, Optional
import requests
from .base import FleetDataProvider
from ..config import config


class APIFleetProvider(FleetDataProvider):
    """
    Fleet data provider that reads from the Flask ops backend (app.py, port 8000).
    All methods fall back to returning empty structures if the backend is unreachable,
    so the AI layer never hard-crashes due to connectivity issues.
    """

    def __init__(self):
        self.base_url = config.BACKEND_BASE_URL.rstrip("/")
        self._timeout = 4  # seconds — fast fail so chat stays responsive

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _get(self, path: str) -> Optional[Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = requests.get(url, timeout=self._timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            print(f"[APIFleetProvider] Backend unreachable at {url}")
            return None
        except requests.exceptions.Timeout:
            print(f"[APIFleetProvider] Timeout fetching {url}")
            return None
        except Exception as e:
            print(f"[APIFleetProvider] Error fetching {url}: {e}")
            return None

    def _raw_drivers(self) -> List[Dict[str, Any]]:
        """Fetch /driver-cards and return list; empty list on failure."""
        data = self._get("/driver-cards")
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "drivers" in data:
            return data["drivers"]
        return []

    @staticmethod
    def _normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Map app.py driver-card shape → common shape used by AI handlers."""
        load = raw.get("current_load") or {}
        alerts_raw = raw.get("alerts") or []
        perf = raw.get("performance") or {}

        # Derive a simple status string
        status = (raw.get("status_label") or "unknown").lower().replace(" ", "_")

        # On-time rate from performance schedule/actual time
        on_time_rate = None
        if perf.get("schedule_time") and perf.get("actual_time"):
            try:
                on_time_rate = round(
                    min(perf["schedule_time"] / perf["actual_time"], 1.0) * 100, 1
                )
            except (ZeroDivisionError, TypeError):
                pass

        # CPM estimate from performance miles data
        cost_per_mile = None
        if perf.get("actual_miles") and perf.get("actual_miles") > 0:
            # Rough CPM: not ideal, but sufficient for AI ranking without ELD data
            cost_per_mile = round(1.5 + (perf.get("oor_miles", 0) / max(perf["actual_miles"], 1)) * 2, 2)

        return {
            "id": str(raw.get("driver_id", "")),
            "name": raw.get("name", "Unknown"),
            "truck_id": raw.get("vehicle_no") or raw.get("vehicle_id"),
            "status": status,
            "location": raw.get("location_label") or "Unknown",
            "hos_remaining_hours": raw.get("hos_remaining_hours"),  # None until ELD wired
            "fuel_level_pct": raw.get("fuel_pct"),                 # None until ELD wired
            "cost_per_mile": cost_per_mile,
            "on_time_rate": on_time_rate,
            "load": {
                "id": load.get("load_id"),
                "origin": load.get("origin"),
                "destination": load.get("destination"),
                "progress_pct": raw.get("load_progress_pct"),
                "eta": raw.get("eta_label"),
            } if load.get("load_id") else None,
            "alerts": [
                a.get("text", a) if isinstance(a, dict) else str(a)
                for a in alerts_raw
            ],
            "performance": perf,
        }

    # ------------------------------------------------------------------ #
    # FleetDataProvider interface                                          #
    # ------------------------------------------------------------------ #

    def get_all_drivers(self) -> List[Dict[str, Any]]:
        return [self._normalize(d) for d in self._raw_drivers()]

    def get_fleet_summary(self) -> Dict[str, Any]:
        drivers = self.get_all_drivers()
        statuses = [d["status"] for d in drivers]
        alerts_count = sum(len(d.get("alerts", [])) for d in drivers)
        return {
            "total_drivers": len(drivers),
            "en_route": statuses.count("en_route"),
            "available": statuses.count("available"),
            "on_break": statuses.count("on_break"),
            "off_duty": statuses.count("off_duty"),
            "active_alerts": alerts_count,
        }

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        drivers = self.get_all_drivers()
        alerts = []
        for d in drivers:
            for alert_text in d.get("alerts", []):
                alerts.append({
                    "driver_name": d["name"],
                    "driver_id": d["id"],
                    "severity": "critical" if "critical" in alert_text.lower() or "HOS" in alert_text else "warning",
                    "message": alert_text,
                })
        return alerts

    def get_driver_status(self, driver_name: str) -> Dict[str, Any]:
        for d in self.get_all_drivers():
            if driver_name.lower() in d["name"].lower():
                return d
        return {}

    def get_available_drivers(self) -> List[Dict[str, Any]]:
        return [d for d in self.get_all_drivers() if d["status"] == "available"]

    def get_delivery_risk_drivers(self) -> List[Dict[str, Any]]:
        """Drivers en-route with HOS < 4h or with delay/HOS alerts."""
        drivers = self.get_all_drivers()
        at_risk = []
        for d in drivers:
            if d["status"] != "en_route":
                continue
            hos = d.get("hos_remaining_hours")
            alerts = " ".join(d.get("alerts", [])).lower()
            if (hos is not None and hos < 4) or "delay" in alerts or "hos" in alerts:
                at_risk.append(d)
        return at_risk

    def get_low_fuel_en_route_drivers(self) -> List[Dict[str, Any]]:
        drivers = self.get_all_drivers()
        low_fuel = []
        for d in drivers:
            if d["status"] != "en_route":
                continue
            fuel = d.get("fuel_level_pct")
            alerts = " ".join(d.get("alerts", [])).lower()
            if (fuel is not None and fuel < 35) or "fuel" in alerts:
                low_fuel.append(d)
        return low_fuel

    def get_best_cost_per_mile_driver(self) -> Dict[str, Any]:
        available = self.get_available_drivers()
        with_cpm = [d for d in available if d.get("cost_per_mile") is not None]
        if not with_cpm:
            return available[0] if available else {}
        return min(with_cpm, key=lambda d: d["cost_per_mile"])

    def rank_drivers_for_load(self, origin: str, destination: str, pickup_time: str = None) -> List[Dict[str, Any]]:
        """Score available drivers for a load using HOS, proximity hint, and CPM."""
        available = self.get_available_drivers()

        def score(d: Dict[str, Any]) -> float:
            s = 0.0
            # HOS: more is better
            hos = d.get("hos_remaining_hours") or 8
            s += min(hos, 11) * 5
            # CPM: lower is better
            cpm = d.get("cost_per_mile") or 2.0
            s -= cpm * 10
            # Proximity: naive location match
            loc = (d.get("location") or "").lower()
            if origin.lower() in loc:
                s += 30
            return s

        return sorted(available, key=score, reverse=True)