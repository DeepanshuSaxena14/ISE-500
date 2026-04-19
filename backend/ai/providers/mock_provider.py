from typing import List, Dict, Any
from .base import FleetDataProvider

class MockFleetProvider(FleetDataProvider):
    def __init__(self):
        self.drivers = [
            {"name": "James Okafor", "status": "en_route", "fuel_level_pct": 31, "eta": "16:10", "destination": "Dallas", "hos_remaining_hours": 4, "cost_per_mile": 1.95, "location": "Austin", "truck_id": "T-10"},
            {"name": "Sarah Jenkins", "status": "available", "fuel_level_pct": 80, "eta": None, "destination": None, "hos_remaining_hours": 10, "cost_per_mile": 1.75, "location": "Phoenix", "truck_id": "T-11"},
            {"name": "Mike Chen", "status": "stopped", "fuel_level_pct": 45, "eta": None, "destination": "Chicago", "hos_remaining_hours": 2, "cost_per_mile": 2.10, "location": "off-route", "truck_id": "T-18"},
            {"name": "Driver A", "status": "available", "fuel_level_pct": 95, "eta": None, "destination": None, "hos_remaining_hours": 14, "cost_per_mile": 1.50, "location": "Tucson", "truck_id": "T-22"}
        ]
        
        self.alerts = [
            {"severity": "critical", "message": "Truck 18 is stopped off-route for 43 minutes.", "truck_id": "T-18"},
            {"severity": "warning", "message": "Truck 10 is running low on fuel (31%).", "truck_id": "T-10"},
        ]

    def get_fleet_summary(self) -> Dict[str, Any]:
        return {
            "total_drivers": len(self.drivers),
            "en_route": len([d for d in self.drivers if d["status"] == "en_route"]),
            "available": len([d for d in self.drivers if d["status"] == "available"]),
            "active_alerts": len(self.alerts)
        }

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        return self.alerts

    def get_driver_status(self, driver_name: str) -> Dict[str, Any]:
        for d in self.drivers:
            if driver_name.lower() in d["name"].lower():
                return d
        return {}

    def get_all_drivers(self) -> List[Dict[str, Any]]:
        return self.drivers

    def get_available_drivers(self) -> List[Dict[str, Any]]:
        return [d for d in self.drivers if d["status"] == "available"]

    def get_delivery_risk_drivers(self) -> List[Dict[str, Any]]:
        # Mocking delivery risk based on hos remaining
        return [d for d in self.drivers if d["status"] == "en_route" and d["hos_remaining_hours"] < 5]

    def get_low_fuel_en_route_drivers(self) -> List[Dict[str, Any]]:
        return [d for d in self.drivers if d["status"] == "en_route" and d["fuel_level_pct"] < 35]

    def get_best_cost_per_mile_driver(self) -> Dict[str, Any]:
        available = self.get_available_drivers()
        if not available:
            return {}
        return min(available, key=lambda x: x["cost_per_mile"])

    def rank_drivers_for_load(self, origin: str, destination: str, pickup_time: str = None) -> List[Dict[str, Any]]:
        # Mock ranking logic: preferring available drivers near origin and lower cost per mile
        available = self.get_available_drivers()
        
        def score(driver):
            score_val = 0
            if driver["location"].lower() == origin.lower():
                score_val += 100
            score_val -= driver["cost_per_mile"] * 10
            return score_val
            
        ranked = sorted(available, key=score, reverse=True)
        return ranked
