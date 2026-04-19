from abc import ABC, abstractmethod
from typing import List, Dict, Any

class FleetDataProvider(ABC):
    @abstractmethod
    def get_fleet_summary(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_driver_status(self, driver_name: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_all_drivers(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_available_drivers(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_delivery_risk_drivers(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_low_fuel_en_route_drivers(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_best_cost_per_mile_driver(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def rank_drivers_for_load(self, origin: str, destination: str, pickup_time: str = None) -> List[Dict[str, Any]]:
        pass
