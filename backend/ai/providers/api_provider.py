from typing import List, Dict, Any
import requests
from .base import FleetDataProvider
from ..config import config

class APIFleetProvider(FleetDataProvider):
    """
    Live implementation that fetches data from the Flask backend (app.py).
    Adapts the high-level backend endpoints to the AI's data requirements.
    """
    def __init__(self):
        self.base_url = config.BACKEND_BASE_URL.rstrip('/')

    def _get(self, endpoint: str) -> Any:
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"AI Provider Error during GET {endpoint}: {e}")
            return [] if "List" in str(type([])) else {}

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Any:
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"AI Provider Error during POST {endpoint}: {e}")
            return {}

    def get_fleet_summary(self) -> Dict[str, Any]:
        """Calculates fleet-wide metrics from the /driver-cards endpoint."""
        cards = self._get("/driver-cards")
        if not isinstance(cards, list):
            return {"total_drivers": 0, "available": 0, "en_route": 0}
            
        summary = {
            "total_drivers": len(cards),
            "available": len([c for c in cards if c.get('status_label') == "Available"]),
            "en_route": len([c for c in cards if c.get('status_label') == "En Route"]),
            "off_duty": len([c for c in cards if c.get('status_label') == "Off Duty"]),
            "driving": len([c for c in cards if c.get('status_label') == "Driving"]),
            "high_alerts": sum(len([a for a in c.get('alerts', []) if a.get('severity') == "high"]) for c in cards)
        }
        return summary

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Collects all alerts across the entire fleet."""
        cards = self._get("/driver-cards")
        all_alerts = []
        if isinstance(cards, list):
            for card in cards:
                for alert in card.get("alerts", []):
                    all_alerts.append({
                        "driver_name": card.get("name"),
                        "severity": alert.get("severity"),
                        "text": alert.get("text")
                    })
        return all_alerts

    def get_driver_status(self, driver_name: str) -> Dict[str, Any]:
        """Finds detailed status for a specific driver by name."""
        cards = self._get("/driver-cards")
        if isinstance(cards, list):
            for card in cards:
                if driver_name.lower() in card.get("name", "").lower():
                    return card
        return {}

    def get_all_drivers(self) -> List[Dict[str, Any]]:
        """Returns all driver cards."""
        return self._get("/driver-cards")

    def get_available_drivers(self) -> List[Dict[str, Any]]:
        """Filters for drivers with 'Available' status."""
        cards = self._get("/driver-cards")
        if isinstance(cards, list):
            return [c for c in cards if c.get("status_label") == "Available"]
        return []

    def get_delivery_risk_drivers(self) -> List[Dict[str, Any]]:
        """Filters for drivers whose alerts mention high delay or ETA risk."""
        cards = self._get("/driver-cards")
        risky = []
        if isinstance(cards, list):
            for card in cards:
                for alert in card.get("alerts", []):
                    text = alert.get("text", "").lower()
                    if "delay" in text or "eta" in text:
                        risky.append(card)
                        break
        return risky

    def get_low_fuel_en_route_drivers(self) -> List[Dict[str, Any]]:
        """Placeholder for fuel risk (requires fuel data in alerts)."""
        cards = self._get("/driver-cards")
        risky = []
        if isinstance(cards, list):
            for card in cards:
                for alert in card.get("alerts", []):
                    if "fuel" in alert.get("text", "").lower():
                        risky.append(card)
                        break
        return risky

    def get_best_cost_per_mile_driver(self) -> Dict[str, Any]:
        """Hypothetical helper to find most efficient driver."""
        cards = self._get("/driver-cards")
        if not cards or not isinstance(cards, list):
            return {}
        # Sort by those with fewest high severity alerts as a proxy for efficiency
        sorted_cards = sorted(cards, key=lambda c: len([a for a in c.get("alerts", []) if a.get("severity") == "high"]))
        return sorted_cards[0] if sorted_cards else {}

    def rank_drivers_for_load(self, origin: str, destination: str, pickup_time: str = None) -> List[Dict[str, Any]]:
        """
        Uses the backend logic to rank drivers.
        Creates a draft load and then fetches recommendations.
        """
        load_data = {
            "pickup_name": "Temporary Query",
            "pickup_address": origin,
            "pickup_lat": 0.0,
            "pickup_lng": 0.0,
            "dropoff_name": "Temporary Dest",
            "dropoff_address": destination,
            "dropoff_lat": 0.0,
            "dropoff_lng": 0.0,
            "pickup_time": pickup_time or "2024-01-01T12:00:00Z",
            "dropoff_time": "2024-01-02T12:00:00Z"
        }
        load = self._post("/loads", load_data)
        if load and "id" in load:
            return self._get(f"/loads/{load['id']}/recommendations")
        return []
