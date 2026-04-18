"""
DispatchIQ — Mock Data Generator
Provides a realistic fleet snapshot and an async event stream
that simulates live GPS / status updates.

Import in main.py:
    from mock_data import MOCK_FLEET_SNAPSHOT, MOCK_ALERTS, fleet_event_generator
"""

from __future__ import annotations

import asyncio
import random
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator

# ── Static fleet snapshot ────────────────────────────────────────────────────

_DRIVERS: list[dict] = [
    {
        "id": "D-001",
        "name": "Marcus Rivera",
        "phone": "+1-602-555-0101",
        "status": "en_route",
        "hours_remaining": 9.5,
        "fuel_pct": 72,
        "current_lat": 33.8303,
        "current_lng": -112.5684,
        "current_load_id": "LD-4821",
        "cpm": 0.52,
        "on_time_rate": 94.2,
    },
    {
        "id": "D-002",
        "name": "Sandra Kim",
        "phone": "+1-602-555-0102",
        "status": "on_break",
        "hours_remaining": 7.2,
        "fuel_pct": 61,
        "current_lat": 34.0522,
        "current_lng": -118.2437,
        "current_load_id": "LD-4798",
        "cpm": 0.49,
        "on_time_rate": 97.8,
        "break_ends_minutes": 22,      # extra field for UI
    },
    {
        "id": "D-003",
        "name": "James Okafor",
        "phone": "+1-602-555-0103",
        "status": "en_route",
        "hours_remaining": 2.1,        # ⚠ HOS critical
        "fuel_pct": 29,                # ⚠ Fuel critical
        "current_lat": 35.0844,
        "current_lng": -106.6504,
        "current_load_id": "LD-4809",
        "cpm": 0.55,
        "on_time_rate": 88.1,
    },
    {
        "id": "D-004",
        "name": "Tanya Reyes",
        "phone": "+1-602-555-0104",
        "status": "available",
        "hours_remaining": 10.0,
        "fuel_pct": 95,
        "current_lat": 33.4484,
        "current_lng": -112.0740,
        "current_load_id": None,
        "cpm": 0.47,
        "on_time_rate": 99.1,
    },
    {
        "id": "D-005",
        "name": "Devon Carter",
        "phone": "+1-602-555-0105",
        "status": "en_route",
        "hours_remaining": 5.5,
        "fuel_pct": 54,
        "current_lat": 35.1983,
        "current_lng": -111.6513,
        "current_load_id": "LD-4815",
        "cpm": 0.51,
        "on_time_rate": 91.3,
        "delay_minutes": 47,           # extra field
        "weather_advisory": "Wind advisory I-40",
    },
    {
        "id": "D-006",
        "name": "Priya Nair",
        "phone": "+1-602-555-0106",
        "status": "off_duty",
        "hours_remaining": 0.0,
        "fuel_pct": 88,
        "current_lat": 33.4255,
        "current_lng": -111.9400,
        "current_load_id": None,
        "cpm": 0.53,
        "on_time_rate": 96.0,
        "hos_reset_hours": 34,         # 34-hr reset in progress
        "available_at": "Tomorrow 06:00",
    },
    {
        "id": "D-007",
        "name": "Luis Mendoza",
        "phone": "+1-602-555-0107",
        "status": "en_route",
        "hours_remaining": 6.8,
        "fuel_pct": 67,
        "current_lat": 34.8697,
        "current_lng": -111.7610,
        "current_load_id": "LD-4822",
        "cpm": 0.50,
        "on_time_rate": 93.5,
    },
    {
        "id": "D-008",
        "name": "Rachel Stone",
        "phone": "+1-602-555-0108",
        "status": "en_route",
        "hours_remaining": 8.3,
        "fuel_pct": 43,
        "current_lat": 33.9806,
        "current_lng": -114.5900,
        "current_load_id": "LD-4817",
        "cpm": 0.48,
        "on_time_rate": 95.7,
    },
]

_LOADS: list[dict] = [
    {
        "id": "LD-4821", "driver_id": "D-001",
        "origin_city": "Phoenix", "origin_state": "AZ",
        "dest_city": "Dallas", "dest_state": "TX",
        "distance_miles": 1027, "rate_usd": 2850.00,
        "status": "en_route", "progress_pct": 34,
        "commodity": "Electronics", "weight_lbs": 38000,
        "delivery_eta": "2024-01-15T22:00:00Z",
    },
    {
        "id": "LD-4798", "driver_id": "D-002",
        "origin_city": "Los Angeles", "origin_state": "CA",
        "dest_city": "Albuquerque", "dest_state": "NM",
        "distance_miles": 790, "rate_usd": 2100.00,
        "status": "en_route", "progress_pct": 0,
        "commodity": "Apparel", "weight_lbs": 24000,
        "delivery_eta": "2024-01-16T08:00:00Z",
    },
    {
        "id": "LD-4809", "driver_id": "D-003",
        "origin_city": "Albuquerque", "origin_state": "NM",
        "dest_city": "Phoenix", "dest_state": "AZ",
        "distance_miles": 460, "rate_usd": 1400.00,
        "status": "en_route", "progress_pct": 71,
        "commodity": "Auto Parts", "weight_lbs": 18000,
        "delivery_eta": "2024-01-15T17:00:00Z",
    },
    {
        "id": "LD-4815", "driver_id": "D-005",
        "origin_city": "Albuquerque", "origin_state": "NM",
        "dest_city": "Flagstaff", "dest_state": "AZ",
        "distance_miles": 325, "rate_usd": 950.00,
        "status": "en_route", "progress_pct": 55,
        "commodity": "Building Materials", "weight_lbs": 42000,
        "delivery_eta": "2024-01-15T19:30:00Z",
    },
    {
        "id": "LD-4822", "driver_id": "D-007",
        "origin_city": "Phoenix", "origin_state": "AZ",
        "dest_city": "Flagstaff", "dest_state": "AZ",
        "distance_miles": 145, "rate_usd": 480.00,
        "status": "en_route", "progress_pct": 62,
        "commodity": "Food & Beverage", "weight_lbs": 29000,
        "delivery_eta": "2024-01-15T15:00:00Z",
    },
    {
        "id": "LD-4817", "driver_id": "D-008",
        "origin_city": "Phoenix", "origin_state": "AZ",
        "dest_city": "Las Vegas", "dest_state": "NV",
        "distance_miles": 285, "rate_usd": 875.00,
        "status": "en_route", "progress_pct": 28,
        "commodity": "Consumer Goods", "weight_lbs": 31000,
        "delivery_eta": "2024-01-15T20:00:00Z",
    },
]

_LOADS_BY_ID: dict[str, dict] = {l["id"]: l for l in _LOADS}

# Attach load info to each driver for convenience
for _d in _DRIVERS:
    _lid = _d.get("current_load_id")
    _d["load"] = _LOADS_BY_ID.get(_lid) if _lid else None


MOCK_ALERTS: list[dict] = [
    {
        "id": 1,
        "driver_id": "D-003",
        "load_id": "LD-4809",
        "alert_type": "hos_critical",
        "severity": "critical",
        "title": "HOS Critical — James Okafor",
        "description": "James has only 2.1 hours of drive time remaining. LD-4809 needs 1.3 hrs to destination. Recommend fueling stop + handoff planning.",
        "is_read": False,
        "is_resolved": False,
        "created_at": "2024-01-15T12:00:00Z",
    },
    {
        "id": 2,
        "driver_id": "D-003",
        "load_id": "LD-4809",
        "alert_type": "fuel_critical",
        "severity": "critical",
        "title": "Fuel Critical — James Okafor (29%)",
        "description": "James is running low on fuel near Albuquerque. Nearest Pilot is 4 miles ahead on I-40.",
        "is_read": False,
        "is_resolved": False,
        "created_at": "2024-01-15T12:05:00Z",
    },
    {
        "id": 3,
        "driver_id": "D-005",
        "load_id": "LD-4815",
        "alert_type": "delay",
        "severity": "warning",
        "title": "Delay — Devon Carter (47 min behind)",
        "description": "Wind advisory on I-40 has slowed Devon. ETA pushed to 20:17. Notify receiver.",
        "is_read": False,
        "is_resolved": False,
        "created_at": "2024-01-15T11:30:00Z",
    },
    {
        "id": 4,
        "driver_id": "D-002",
        "load_id": "LD-4798",
        "alert_type": "hos_warning",
        "severity": "info",
        "title": "Break Ending Soon — Sandra Kim (22 min)",
        "description": "Sandra's mandatory break ends in 22 minutes. LD-4798 pickup window opens in 45 minutes.",
        "is_read": True,
        "is_resolved": False,
        "created_at": "2024-01-15T11:00:00Z",
    },
]

MOCK_FLEET_SNAPSHOT: dict = {
    "drivers": _DRIVERS,
    "loads": _LOADS,
    "alerts": MOCK_ALERTS,
    "generated_at": datetime.now(timezone.utc).isoformat(),
}


# ── Live event generator ─────────────────────────────────────────────────────

# Small bounding boxes for realistic position drift
_ROUTE_CORRIDORS: dict[str, tuple[float, float, float, float]] = {
    "D-001": (33.4, -112.5, 33.9, -112.3),   # PHX → DAL corridor start
    "D-003": (35.0, -106.8, 35.2, -106.5),   # ABQ → PHX
    "D-005": (35.1, -111.8, 35.3, -111.5),   # ABQ → FLG
    "D-007": (34.7, -111.9, 35.0, -111.6),   # PHX → FLG
    "D-008": (33.9, -114.7, 34.1, -114.4),   # PHX → LAS
}


def _drift(lat: float, lng: float, corridor: tuple) -> tuple[float, float]:
    """Move driver position slightly within corridor bounds."""
    lat_min, lng_min, lat_max, lng_max = corridor
    new_lat = max(lat_min, min(lat_max, lat + random.uniform(-0.015, 0.025)))
    new_lng = max(lng_min, min(lng_max, lng + random.uniform(0.010, 0.030)))
    return round(new_lat, 6), round(new_lng, 6)


async def fleet_event_generator() -> AsyncGenerator[dict, None]:
    """
    Yields a full fleet snapshot every 5 seconds with:
    - Simulated GPS drift for en-route drivers
    - Slowly declining HOS hours
    - Random minor alert generation
    - Fuel slowly decreasing
    """
    state = deepcopy(MOCK_FLEET_SNAPSHOT)
    drivers = {d["id"]: d for d in state["drivers"]}
    tick = 0

    while True:
        tick += 1

        for driver_id, driver in drivers.items():
            if driver["status"] != "en_route":
                continue

            # GPS drift
            corridor = _ROUTE_CORRIDORS.get(driver_id)
            if corridor:
                lat, lng = _drift(driver["current_lat"], driver["current_lng"], corridor)
                driver["current_lat"] = lat
                driver["current_lng"] = lng

            # HOS slowly decreases (5 sec tick ≈ 5 sec of real time → ~0.0014 hr)
            driver["hours_remaining"] = max(
                0.0, round(driver["hours_remaining"] - 0.002, 3)
            )

            # Fuel slowly decreases
            if tick % 3 == 0:
                driver["fuel_pct"] = max(0, driver["fuel_pct"] - 1)

            # Load progress creeps up
            if driver.get("load"):
                driver["load"]["progress_pct"] = min(
                    100, driver["load"]["progress_pct"] + random.randint(0, 1)
                )

        # Random new alert (rare)
        new_alerts = []
        if random.random() < 0.05:  # 5% chance per tick
            new_alerts.append({
                "id": 100 + tick,
                "alert_type": random.choice(["fuel_low", "delay", "hos_warning"]),
                "severity": "warning",
                "title": "Simulated live alert",
                "description": f"Auto-generated at tick {tick}",
                "is_read": False,
                "is_resolved": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

        yield {
            "type": "fleet_update",
            "tick": tick,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "drivers": list(drivers.values()),
            "alerts": state["alerts"] + new_alerts,
        }

        await asyncio.sleep(5)


# ── Quick sanity check ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import json
    print(json.dumps(MOCK_FLEET_SNAPSHOT, indent=2, default=str))