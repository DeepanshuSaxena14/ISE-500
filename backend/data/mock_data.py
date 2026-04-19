from __future__ import annotations

import asyncio
import json
import random
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

"""
Backend-compatible mock data for app.py

This file generates payloads that comply with these routes:

- POST /ingest/drivers
- POST /ingest/vehicles
- POST /ingest/driver-performance
- POST /loads

and also provides an async event generator that emits incremental snapshots
in the same backend-ingestible shapes.

Usage:

    from mock_data import (
        MOCK_DRIVERS_PAYLOAD,
        MOCK_VEHICLES_PAYLOAD,
        MOCK_DRIVER_PERFORMANCE_PAYLOAD,
        MOCK_LOAD_REQUESTS,
        BACKEND_SNAPSHOT,
        backend_event_generator,
    )

Optional quick dump:

    python mock_data.py
"""


# ============================================================
# Helpers
# ============================================================

UTC = timezone.utc


def now_utc() -> datetime:
    return datetime.now(UTC)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def epoch_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def city_state(name: str) -> str:
    return name


# ============================================================
# Canonical base entities
# These are internal convenience records; exported payloads below
# are shaped for your Flask backend.
# ============================================================

_BASE_DRIVERS: list[dict] = []
_BASE_VEHICLES: list[dict] = []
_BASE_PERFORMANCE: list[dict] = []

import random

# Fix the seed so restarts generate identical mock environments unless changed
random.seed(42)

FIRST_NAMES = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles", "Sandra", "Tanya", "Priya", "Marcus", "Luis", "Devon", "Rachel", "Sarah", "Jessica", "Ashley", "Brian", "Kevin", "Jason", "Matthew", "Gary", "Timothy", "Jose", "Larry", "Jeffrey"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Reyes", "Nair", "Mendoza", "Carter", "Stone", "Anderson", "Taylor", "Thomas", "Hernandez", "Moore", "Martin", "Jackson", "Thompson", "White"]

# 10 specific regions mirroring the 10 exact loads
CITIES = [
    "Phoenix, AZ", "Los Angeles, CA", "Dallas, TX", "Seattle, WA", 
    "Chicago, IL", "Atlanta, GA", "New York, NY", "Miami, FL", 
    "Denver, CO", "Salt Lake City, UT"
]

# We want exactly 5 drivers per city to ensure proper competitive variance. 
# 1 flatbed, 1 reefer, 2 vans, 1 pneumatic for each city.
TRAILER_DISTRIBUTION = ["VAN", "VAN", "REEFER", "FLATBED", "PNEUMATIC"]

for i in range(50):
    driver_id = 12000 + i + 1
    fname = random.choice(FIRST_NAMES)
    lname = random.choice(LAST_NAMES)
    
    # Exactly 5 drivers per city
    city_idx = i // 5
    city = CITIES[city_idx]
    terminal = city.split(",")[0] + " Hub"
    
    # Ensuring exact variance of trailer types perfectly evenly distributed per city
    trailer_type = TRAILER_DISTRIBUTION[i % 5]
    
    # Base configuration: 3 AVAILABLE, 2 IN_TRANSIT per city
    _BASE_DRIVERS.append({
        "driver_id": driver_id,
        "full_name": f"{fname} {lname}",
        "carrier": "DispatchIQ Freight",
        "work_status": "AVAILABLE" if (i % 5) < 3 else "IN_TRANSIT",
        "terminal": terminal,
        "driver_type": "COMPANY_DRIVER" if i % 2 == 0 else "OWNER_OPERATOR_OO",
        "phone": f"+1-602-555-{driver_id:04d}",
        "email": f"{fname.lower()}.{lname.lower()}{driver_id}@dispatchiq.test",
        "last_known_location": city,
        "timezone": "UTC",
        "current_load": None
    })

    _BASE_VEHICLES.append({
        "vehicle_id": 840000 + i + 1,
        "owner_id": 49845,
        "owner_name": "DispatchIQ Freight",
        "vehicle_status": "ACTIVE",
        "vehicle_no": f"TRK-{300+driver_id}",
        "vehicle_type": "TRUCK",
        "vehicle_vin": f"1DQM30{driver_id:03d}0000{driver_id}",
        "gross_vehicle_weight": 80000,
        "trailer_type": trailer_type,
        "vehicle_make": "Freightliner",
        "vehicle_model": "Cascadia",
        "assigned_driver_ids": [driver_id],
    })

    # To guarantee a UNIQUE top driver among identically configured drivers, 
    # we vary the actual_time/actual_miles ratio. The lower the index in the city block, the better the performance.
    quality_modifier = 1.0 + ( (i % 5) * 0.05 )
    sched_mi = 500.0
    actual_mi = sched_mi * quality_modifier
    oor_mi = actual_mi - sched_mi
    sched_t = 500 # minutes
    actual_t = int(sched_t * quality_modifier)
    
    _BASE_PERFORMANCE.append({
        "driver_id": driver_id,
        "oor_miles": round(oor_mi, 1),
        "schedule_miles": round(sched_mi, 1),
        "actual_miles": round(actual_mi, 1),
        "schedule_time": int(sched_t),
        "actual_time": int(actual_t),
    })

# Define 10 distinct, unique loads tightly coupled to the 10 Cities above
_BASE_LOAD_REQUESTS = [
    {
        # Phoenix, AZ Load (Needs VAN) -> Target: Phoenix Driver #0 (Perfect VAN)
        "pickup_name": "Phoenix DC", "pickup_address": "400 Phoenix Way, Phoenix, AZ",
        "pickup_lat": 33.4374, "pickup_lng": -112.1521,
        "dropoff_name": "Vegas Hub", "dropoff_address": "12 Vegas Blvd, Las Vegas, NV",
        "dropoff_lat": 36.1699, "dropoff_lng": -115.1398,
        "pickup_time": iso_z(now_utc() + timedelta(hours=2)),
        "dropoff_time": iso_z(now_utc() + timedelta(hours=18)),
        "required_trailer_type": "VAN", "required_vehicle_type": "TRUCK",
    },
    {
        # Los Angeles, CA Load (Needs REEFER) -> Target: LA Driver #2 (REEFER)
        "pickup_name": "LA Fresh Produce", "pickup_address": "88 LA Market, Los Angeles, CA",
        "pickup_lat": 34.0522, "pickup_lng": -118.2437,
        "dropoff_name": "San Jose Distribution", "dropoff_address": "90 San Jose Dr, San Jose, CA",
        "dropoff_lat": 37.3382, "dropoff_lng": -121.8863,
        "pickup_time": iso_z(now_utc() + timedelta(hours=1)),
        "dropoff_time": iso_z(now_utc() + timedelta(hours=12)),
        "required_trailer_type": "REEFER", "required_vehicle_type": "TRUCK",
    },
    {
        # Dallas, TX Load (Needs FLATBED) -> Target: Dallas Driver #3 (FLATBED)
        "pickup_name": "Dallas Steel Yard", "pickup_address": "100 Steel Rd, Dallas, TX",
        "pickup_lat": 32.7876, "pickup_lng": -96.8044,
        "dropoff_name": "Austin Assembly", "dropoff_address": "55 Austin Ave, Austin, TX",
        "dropoff_lat": 30.2672, "dropoff_lng": -97.7431,
        "pickup_time": iso_z(now_utc() + timedelta(hours=4)),
        "dropoff_time": iso_z(now_utc() + timedelta(hours=10)),
        "required_trailer_type": "FLATBED", "required_vehicle_type": "TRUCK",
    },
    {
        # Seattle, WA Load (Needs VAN) -> Target: Seattle Driver #0
        "pickup_name": "Seattle Tech Depot", "pickup_address": "1 Array St, Seattle, WA",
        "pickup_lat": 47.6062, "pickup_lng": -122.3321,
        "dropoff_name": "Portland Terminal", "dropoff_address": "400 PDX Blvd, Portland, OR",
        "dropoff_lat": 45.5152, "dropoff_lng": -122.6784,
        "pickup_time": iso_z(now_utc() + timedelta(hours=2)),
        "dropoff_time": iso_z(now_utc() + timedelta(hours=6)),
        "required_trailer_type": "VAN", "required_vehicle_type": "TRUCK",
    },
    {
        # Chicago, IL Load (Needs REEFER) -> Target: Chicago Driver #2
        "pickup_name": "Chicago Meats", "pickup_address": "Meatpacking Dr, Chicago, IL",
        "pickup_lat": 41.8781, "pickup_lng": -87.6298,
        "dropoff_name": "Detroit Markets", "dropoff_address": "808 Motor City Way, Detroit, MI",
        "dropoff_lat": 42.3314, "dropoff_lng": -83.0458,
        "pickup_time": iso_z(now_utc() + timedelta(hours=5)),
        "dropoff_time": iso_z(now_utc() + timedelta(hours=14)),
        "required_trailer_type": "REEFER", "required_vehicle_type": "TRUCK",
    },
    {
        # Atlanta, GA Load (Needs FLATBED) -> Target: Atlanta Driver #3
        "pickup_name": "Atlanta Lumber", "pickup_address": "Timber Rd, Atlanta, GA",
        "pickup_lat": 33.7490, "pickup_lng": -84.3880,
        "dropoff_name": "Nashville Builders", "dropoff_address": "700 Country Ln, Nashville, TN",
        "dropoff_lat": 36.1627, "dropoff_lng": -86.7816,
        "pickup_time": iso_z(now_utc() + timedelta(hours=3)),
        "dropoff_time": iso_z(now_utc() + timedelta(hours=9)),
        "required_trailer_type": "FLATBED", "required_vehicle_type": "TRUCK",
    },
    {
        # New York, NY Load (Needs VAN) -> Target: NY Driver #0
        "pickup_name": "NY Port Authority", "pickup_address": "1 Port Way, New York, NY",
        "pickup_lat": 40.7128, "pickup_lng": -74.0060,
        "dropoff_name": "Philadelphia DC", "dropoff_address": "300 Liberty St, Philadelphia, PA",
        "dropoff_lat": 39.9526, "dropoff_lng": -75.1652,
        "pickup_time": iso_z(now_utc() + timedelta(hours=1)),
        "dropoff_time": iso_z(now_utc() + timedelta(hours=4)),
        "required_trailer_type": "VAN", "required_vehicle_type": "TRUCK",
    },
    {
        # Miami, FL Load (Needs REEFER) -> Target: Miami Driver #2
        "pickup_name": "Miami Ports Imports", "pickup_address": "Ocean Blvd, Miami, FL",
        "pickup_lat": 25.7617, "pickup_lng": -80.1918,
        "dropoff_name": "Orlando Wholesale", "dropoff_address": "Disney Dr, Orlando, FL",
        "dropoff_lat": 28.5383, "dropoff_lng": -81.3792,
        "pickup_time": iso_z(now_utc() + timedelta(hours=2)),
        "dropoff_time": iso_z(now_utc() + timedelta(hours=7)),
        "required_trailer_type": "REEFER", "required_vehicle_type": "TRUCK",
    },
    {
        # Denver, CO Load (Needs FLATBED) -> Target: Denver Driver #3
        "pickup_name": "Denver Machining", "pickup_address": "Mile High Way, Denver, CO",
        "pickup_lat": 39.7392, "pickup_lng": -104.9903,
        "dropoff_name": "Cheyenne Outpost", "dropoff_address": "Wyoming Rd, Cheyenne, WY",
        "dropoff_lat": 41.1400, "dropoff_lng": -104.8202,
        "pickup_time": iso_z(now_utc() + timedelta(hours=3)),
        "dropoff_time": iso_z(now_utc() + timedelta(hours=6)),
        "required_trailer_type": "FLATBED", "required_vehicle_type": "TRUCK",
    },
    {
        # Salt Lake City, UT Load (Needs VAN) -> Target: SLC Driver #0
        "pickup_name": "Salt Lake Tech", "pickup_address": "Silicon Slopes, Salt Lake City, UT",
        "pickup_lat": 40.7608, "pickup_lng": -111.8910,
        "dropoff_name": "Boise Depot", "dropoff_address": "Potato Ln, Boise, ID",
        "dropoff_lat": 43.6150, "dropoff_lng": -116.2023,
        "pickup_time": iso_z(now_utc() + timedelta(hours=2)),
        "dropoff_time": iso_z(now_utc() + timedelta(hours=10)),
        "required_trailer_type": "VAN", "required_vehicle_type": "TRUCK",
    }
]


# ============================================================
# Conversion to app.py-compatible payloads
# ============================================================

def build_driver_payload() -> dict:
    ts = epoch_ms(now_utc())

    data: list[dict] = []
    for base in _BASE_DRIVERS:
        first_name, last_name = split_name(base["full_name"])
        current_load = base["current_load"]

        load_block = {}
        if current_load:
            pickup_dt = now_utc() + timedelta(hours=current_load["pickup_offset_hours"])
            delivery_dt = now_utc() + timedelta(hours=current_load["delivery_offset_hours"])
            load_block = {
                "driver_current_load": {
                    "load_id": current_load["load_id"],
                    "load_show_id": current_load["load_show_id"],
                    "origin": current_load["origin"],
                    "destination": current_load["destination"],
                    "pickup_date": epoch_ms(pickup_dt),
                    "delivery_date": epoch_ms(delivery_dt),
                }
            }

        data.append(
            {
                "driver_id": base["driver_id"],
                "basic_info": {
                    "driver_first_name": first_name,
                    "driver_last_name": last_name,
                    "carrier": base["carrier"],
                    "work_status": base["work_status"],
                    "terminal": base["terminal"],
                    "driver_type": base["driver_type"],
                    "driver_phone_number": base["phone"],
                    "driver_email": base["email"],
                },
                "driver_location": {
                    "last_known_location": base["last_known_location"],
                    "latest_update": ts,
                    "timezone": base["timezone"],
                },
                "loads": load_block,
            }
        )

    return {"data": data}


def build_vehicle_payload() -> dict:
    created_date = now_utc().strftime("%b %d, %Y")
    data: list[dict] = []

    for base in _BASE_VEHICLES:
        data.append(
            {
                "created_date": created_date,
                "vehicle_id": base["vehicle_id"],
                "owner_id": base["owner_id"],
                "owner_name": base["owner_name"],
                "vehicle_status": base["vehicle_status"],
                "vehicle_no": base["vehicle_no"],
                "vehicle_type": base["vehicle_type"],
                "vehicle_vin": base["vehicle_vin"],
                "gross_vehicle_weight": base["gross_vehicle_weight"],
                "trailer_type": base["trailer_type"],
                "vehicle_make": base["vehicle_make"],
                "vehicle_model": base["vehicle_model"],
                "assignments_drivers": {
                    "driver_ids": base["assigned_driver_ids"],
                    "assign_driver_info": [
                        {
                            "assign_driver_id": driver_id,
                            "assign_driver_name": next(
                                d["full_name"]
                                for d in _BASE_DRIVERS
                                if d["driver_id"] == driver_id
                            ),
                        }
                        for driver_id in base["assigned_driver_ids"]
                    ],
                },
            }
        )

    return {"data": data}


def build_driver_performance_payload() -> dict:
    return {"data": deepcopy(_BASE_PERFORMANCE)}


# ============================================================
# Exported backend-compatible payloads
# ============================================================

MOCK_DRIVERS_PAYLOAD: dict = build_driver_payload()
MOCK_VEHICLES_PAYLOAD: dict = build_vehicle_payload()
MOCK_DRIVER_PERFORMANCE_PAYLOAD: dict = build_driver_performance_payload()

# Valid request bodies for POST /loads
MOCK_LOAD_REQUESTS: list[dict] = deepcopy(_BASE_LOAD_REQUESTS)

# Convenience combined snapshot for local bootstrap scripts
BACKEND_SNAPSHOT: dict = {
    "drivers_payload": MOCK_DRIVERS_PAYLOAD,
    "vehicles_payload": MOCK_VEHICLES_PAYLOAD,
    "driver_performance_payload": MOCK_DRIVER_PERFORMANCE_PAYLOAD,
    "load_requests": MOCK_LOAD_REQUESTS,
    "generated_at": iso_z(now_utc()),
}


# ============================================================
# Live event generator
# Emits backend-ingestible payloads for periodic refresh.
# This does not match your current Flask routes directly for streaming,
# but every emitted block can be posted to the same ingest routes.
# ============================================================

_DRIVER_LOCATIONS = {
    12154: ("Buckeye, AZ", "Tonopah, AZ", "Goodyear, AZ"),
    12155: ("Los Angeles, CA", "Pasadena, CA", "Pomona, CA"),
    12156: ("Albuquerque, NM", "Gallup, NM", "Holbrook, AZ"),
    12157: ("Phoenix, AZ", "Tolleson, AZ", "Glendale, AZ"),
    12158: ("Flagstaff, AZ", "Winslow, AZ", "Holbrook, AZ"),
    12159: ("Tempe, AZ", "Mesa, AZ", "Chandler, AZ"),
    12160: ("Camp Verde, AZ", "Cordes Lakes, AZ", "Black Canyon City, AZ"),
    12161: ("Quartzsite, AZ", "Kingman, AZ", "Boulder City, NV"),
}


def _mutate_driver_payload(drivers_payload: dict) -> None:
    now_ms = epoch_ms(now_utc())

    for item in drivers_payload["data"]:
        driver_id = item["driver_id"]
        work_status = item["basic_info"]["work_status"]

        if work_status in {"IN_TRANSIT", "DRIVING", "ON_DUTY"}:
            item["driver_location"]["last_known_location"] = random.choice(
                _DRIVER_LOCATIONS.get(driver_id, ("Phoenix, AZ",))
            )

        item["driver_location"]["latest_update"] = now_ms

        current_load = item.get("loads", {}).get("driver_current_load")
        if current_load:
            pickup_ms = current_load.get("pickup_date")
            delivery_ms = current_load.get("delivery_date")

            if pickup_ms is not None and delivery_ms is not None and delivery_ms > pickup_ms:
                # advance delivery very slightly, simulating ETA movement
                delivery_shift_min = random.choice([-5, -2, 0, 1, 3, 5])
                current_load["delivery_date"] = delivery_ms + (delivery_shift_min * 60 * 1000)

        # occasional availability changes
        roll = random.random()
        if work_status == "AVAILABLE" and roll < 0.08:
            item["basic_info"]["work_status"] = "ON_DUTY"
        elif work_status == "ON_DUTY" and roll < 0.08:
            item["basic_info"]["work_status"] = "AVAILABLE"


def _mutate_performance_payload(perf_payload: dict) -> None:
    for item in perf_payload["data"]:
        # small drift; keep metrics plausible
        item["actual_miles"] = round(item["actual_miles"] + random.uniform(0.2, 1.8), 1)
        item["actual_time"] = int(item["actual_time"] + random.randint(0, 3))

        if random.random() < 0.15:
            item["oor_miles"] = round(item["oor_miles"] + random.uniform(0.0, 0.7), 1)


async def backend_event_generator() -> AsyncGenerator[dict, None]:
    """
    Yields a periodic snapshot in backend-ingestible shapes.

    Each event includes:
      - drivers_payload          -> POST /ingest/drivers
      - vehicles_payload         -> POST /ingest/vehicles
      - driver_performance_payload -> POST /ingest/driver-performance

    Example consumer:
        async for event in backend_event_generator():
            post("/ingest/drivers", json=event["drivers_payload"])
            post("/ingest/vehicles", json=event["vehicles_payload"])
            post("/ingest/driver-performance", json=event["driver_performance_payload"])
    """
    drivers_payload = deepcopy(MOCK_DRIVERS_PAYLOAD)
    vehicles_payload = deepcopy(MOCK_VEHICLES_PAYLOAD)
    perf_payload = deepcopy(MOCK_DRIVER_PERFORMANCE_PAYLOAD)

    tick = 0

    while True:
        tick += 1

        _mutate_driver_payload(drivers_payload)
        _mutate_performance_payload(perf_payload)

        yield {
            "type": "backend_snapshot",
            "tick": tick,
            "timestamp": iso_z(now_utc()),
            "drivers_payload": deepcopy(drivers_payload),
            "vehicles_payload": deepcopy(vehicles_payload),
            "driver_performance_payload": deepcopy(perf_payload),
        }

        await asyncio.sleep(5)


# ============================================================
# Optional tiny client helper for manual testing
# ============================================================

def print_curl_examples(base_url: str = "http://127.0.0.1:8000") -> None:
    print("\n# Ingest drivers")
    print(f"curl -X POST {base_url}/ingest/drivers -H 'Content-Type: application/json' -d '{json.dumps(MOCK_DRIVERS_PAYLOAD)}'")

    print("\n# Ingest vehicles")
    print(f"curl -X POST {base_url}/ingest/vehicles -H 'Content-Type: application/json' -d '{json.dumps(MOCK_VEHICLES_PAYLOAD)}'")

    print("\n# Ingest driver performance")
    print(f"curl -X POST {base_url}/ingest/driver-performance -H 'Content-Type: application/json' -d '{json.dumps(MOCK_DRIVER_PERFORMANCE_PAYLOAD)}'")

    print("\n# Create a load")
    print(f"curl -X POST {base_url}/loads -H 'Content-Type: application/json' -d '{json.dumps(MOCK_LOAD_REQUESTS[0])}'")


if __name__ == "__main__":
    print("# BACKEND_SNAPSHOT")
    print(json.dumps(BACKEND_SNAPSHOT, indent=2))

    print_curl_examples()