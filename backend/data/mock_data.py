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

_BASE_DRIVERS: list[dict] = [
    {
        "driver_id": 12154,
        "full_name": "Marcus Rivera",
        "carrier": "DispatchIQ Freight",
        "work_status": "IN_TRANSIT",
        "terminal": "Phoenix Terminal",
        "driver_type": "COMPANY_DRIVER",
        "phone": "+1-602-555-0101",
        "email": "marcus.rivera@dispatchiq.test",
        "last_known_location": "Buckeye, AZ",
        "timezone": "MST",
        "current_load": {
            "load_id": 700101,
            "load_show_id": "LD-4821",
            "origin": "Phoenix, AZ",
            "destination": "Dallas, TX",
            "pickup_offset_hours": -10,
            "delivery_offset_hours": 12,
        },
    },
    {
        "driver_id": 12155,
        "full_name": "Sandra Kim",
        "carrier": "DispatchIQ Freight",
        "work_status": "ON_DUTY",
        "terminal": "Los Angeles Terminal",
        "driver_type": "COMPANY_DRIVER",
        "phone": "+1-602-555-0102",
        "email": "sandra.kim@dispatchiq.test",
        "last_known_location": "Los Angeles, CA",
        "timezone": "PDT",
        "current_load": {
            "load_id": 700102,
            "load_show_id": "LD-4798",
            "origin": "Los Angeles, CA",
            "destination": "Albuquerque, NM",
            "pickup_offset_hours": -3,
            "delivery_offset_hours": 9,
        },
    },
    {
        "driver_id": 12156,
        "full_name": "James Okafor",
        "carrier": "DispatchIQ Freight",
        "work_status": "DRIVING",
        "terminal": "Albuquerque Terminal",
        "driver_type": "OWNER_OPERATOR_OO",
        "phone": "+1-602-555-0103",
        "email": "james.okafor@dispatchiq.test",
        "last_known_location": "Albuquerque, NM",
        "timezone": "MDT",
        "current_load": {
            "load_id": 700103,
            "load_show_id": "LD-4809",
            "origin": "Albuquerque, NM",
            "destination": "Phoenix, AZ",
            "pickup_offset_hours": -6,
            "delivery_offset_hours": 3,
        },
    },
    {
        "driver_id": 12157,
        "full_name": "Tanya Reyes",
        "carrier": "DispatchIQ Freight",
        "work_status": "AVAILABLE",
        "terminal": "Phoenix Terminal",
        "driver_type": "COMPANY_DRIVER",
        "phone": "+1-602-555-0104",
        "email": "tanya.reyes@dispatchiq.test",
        "last_known_location": "Phoenix, AZ",
        "timezone": "MST",
        "current_load": None,
    },
    {
        "driver_id": 12158,
        "full_name": "Devon Carter",
        "carrier": "DispatchIQ Freight",
        "work_status": "IN_TRANSIT",
        "terminal": "Flagstaff Terminal",
        "driver_type": "COMPANY_DRIVER",
        "phone": "+1-602-555-0105",
        "email": "devon.carter@dispatchiq.test",
        "last_known_location": "Flagstaff, AZ",
        "timezone": "MST",
        "current_load": {
            "load_id": 700104,
            "load_show_id": "LD-4815",
            "origin": "Albuquerque, NM",
            "destination": "Flagstaff, AZ",
            "pickup_offset_hours": -5,
            "delivery_offset_hours": 4,
        },
    },
    {
        "driver_id": 12159,
        "full_name": "Priya Nair",
        "carrier": "DispatchIQ Freight",
        "work_status": "OFF_DUTY",
        "terminal": "Tempe Terminal",
        "driver_type": "COMPANY_DRIVER",
        "phone": "+1-602-555-0106",
        "email": "priya.nair@dispatchiq.test",
        "last_known_location": "Tempe, AZ",
        "timezone": "MST",
        "current_load": None,
    },
    {
        "driver_id": 12160,
        "full_name": "Luis Mendoza",
        "carrier": "DispatchIQ Freight",
        "work_status": "IN_TRANSIT",
        "terminal": "Phoenix Terminal",
        "driver_type": "OWNER_OPERATOR_OO",
        "phone": "+1-602-555-0107",
        "email": "luis.mendoza@dispatchiq.test",
        "last_known_location": "Camp Verde, AZ",
        "timezone": "MST",
        "current_load": {
            "load_id": 700105,
            "load_show_id": "LD-4822",
            "origin": "Phoenix, AZ",
            "destination": "Flagstaff, AZ",
            "pickup_offset_hours": -2,
            "delivery_offset_hours": 2,
        },
    },
    {
        "driver_id": 12161,
        "full_name": "Rachel Stone",
        "carrier": "DispatchIQ Freight",
        "work_status": "IN_TRANSIT",
        "terminal": "Phoenix Terminal",
        "driver_type": "COMPANY_DRIVER",
        "phone": "+1-602-555-0108",
        "email": "rachel.stone@dispatchiq.test",
        "last_known_location": "Quartzsite, AZ",
        "timezone": "MST",
        "current_load": {
            "load_id": 700106,
            "load_show_id": "LD-4817",
            "origin": "Phoenix, AZ",
            "destination": "Las Vegas, NV",
            "pickup_offset_hours": -4,
            "delivery_offset_hours": 5,
        },
    },
]

_BASE_VEHICLES: list[dict] = [
    {
        "vehicle_id": 840301,
        "owner_id": 49845,
        "owner_name": "DispatchIQ Freight",
        "vehicle_status": "ACTIVE",
        "vehicle_no": "TRK-301",
        "vehicle_type": "TRUCK",
        "vehicle_vin": "1DQM3010000000001",
        "gross_vehicle_weight": 80000,
        "trailer_type": "VAN",
        "vehicle_make": "Freightliner",
        "vehicle_model": "Cascadia",
        "assigned_driver_ids": [12154],
    },
    {
        "vehicle_id": 840302,
        "owner_id": 49845,
        "owner_name": "DispatchIQ Freight",
        "vehicle_status": "ACTIVE",
        "vehicle_no": "TRK-302",
        "vehicle_type": "TRUCK",
        "vehicle_vin": "1DQM3020000000002",
        "gross_vehicle_weight": 80000,
        "trailer_type": "REEFER",
        "vehicle_make": "Peterbilt",
        "vehicle_model": "579",
        "assigned_driver_ids": [12155],
    },
    {
        "vehicle_id": 840303,
        "owner_id": 49845,
        "owner_name": "DispatchIQ Freight",
        "vehicle_status": "ACTIVE",
        "vehicle_no": "TRK-303",
        "vehicle_type": "TRUCK",
        "vehicle_vin": "1DQM3030000000003",
        "gross_vehicle_weight": 80000,
        "trailer_type": "VAN",
        "vehicle_make": "Kenworth",
        "vehicle_model": "T680",
        "assigned_driver_ids": [12156],
    },
    {
        "vehicle_id": 840304,
        "owner_id": 49845,
        "owner_name": "DispatchIQ Freight",
        "vehicle_status": "ACTIVE",
        "vehicle_no": "TRK-304",
        "vehicle_type": "TRUCK",
        "vehicle_vin": "1DQM3040000000004",
        "gross_vehicle_weight": 80000,
        "trailer_type": "VAN",
        "vehicle_make": "Volvo",
        "vehicle_model": "VNL",
        "assigned_driver_ids": [12157],
    },
    {
        "vehicle_id": 840305,
        "owner_id": 49845,
        "owner_name": "DispatchIQ Freight",
        "vehicle_status": "ACTIVE",
        "vehicle_no": "TRK-305",
        "vehicle_type": "TRUCK",
        "vehicle_vin": "1DQM3050000000005",
        "gross_vehicle_weight": 80000,
        "trailer_type": "FLATBED",
        "vehicle_make": "Mack",
        "vehicle_model": "Anthem",
        "assigned_driver_ids": [12158],
    },
    {
        "vehicle_id": 840306,
        "owner_id": 49845,
        "owner_name": "DispatchIQ Freight",
        "vehicle_status": "INACTIVE",
        "vehicle_no": "TRK-306",
        "vehicle_type": "TRUCK",
        "vehicle_vin": "1DQM3060000000006",
        "gross_vehicle_weight": 80000,
        "trailer_type": "VAN",
        "vehicle_make": "International",
        "vehicle_model": "LT",
        "assigned_driver_ids": [12159],
    },
    {
        "vehicle_id": 840307,
        "owner_id": 49845,
        "owner_name": "DispatchIQ Freight",
        "vehicle_status": "ACTIVE",
        "vehicle_no": "TRK-307",
        "vehicle_type": "TRUCK",
        "vehicle_vin": "1DQM3070000000007",
        "gross_vehicle_weight": 80000,
        "trailer_type": "VAN",
        "vehicle_make": "Freightliner",
        "vehicle_model": "Cascadia",
        "assigned_driver_ids": [12160],
    },
    {
        "vehicle_id": 840308,
        "owner_id": 49845,
        "owner_name": "DispatchIQ Freight",
        "vehicle_status": "ACTIVE",
        "vehicle_no": "TRK-308",
        "vehicle_type": "TRUCK",
        "vehicle_vin": "1DQM3080000000008",
        "gross_vehicle_weight": 80000,
        "trailer_type": "VAN",
        "vehicle_make": "Peterbilt",
        "vehicle_model": "567",
        "assigned_driver_ids": [12161],
    },
]

_BASE_PERFORMANCE: list[dict] = [
    {
        "driver_id": 12154,
        "oor_miles": 12.5,
        "schedule_miles": 1027.0,
        "actual_miles": 1036.0,
        "schedule_time": 960,
        "actual_time": 995,
    },
    {
        "driver_id": 12155,
        "oor_miles": 18.0,
        "schedule_miles": 790.0,
        "actual_miles": 818.0,
        "schedule_time": 780,
        "actual_time": 860,
    },
    {
        "driver_id": 12156,
        "oor_miles": 31.0,
        "schedule_miles": 460.0,
        "actual_miles": 501.0,
        "schedule_time": 420,
        "actual_time": 498,
    },
    {
        "driver_id": 12157,
        "oor_miles": 2.0,
        "schedule_miles": 450.0,
        "actual_miles": 451.0,
        "schedule_time": 470,
        "actual_time": 466,
    },
    {
        "driver_id": 12158,
        "oor_miles": 22.0,
        "schedule_miles": 325.0,
        "actual_miles": 357.0,
        "schedule_time": 360,
        "actual_time": 421,
    },
    {
        "driver_id": 12159,
        "oor_miles": 0.0,
        "schedule_miles": 400.0,
        "actual_miles": 398.0,
        "schedule_time": 450,
        "actual_time": 448,
    },
    {
        "driver_id": 12160,
        "oor_miles": 4.0,
        "schedule_miles": 145.0,
        "actual_miles": 148.0,
        "schedule_time": 160,
        "actual_time": 163,
    },
    {
        "driver_id": 12161,
        "oor_miles": 6.0,
        "schedule_miles": 285.0,
        "actual_miles": 289.0,
        "schedule_time": 300,
        "actual_time": 309,
    },
]

_BASE_LOAD_REQUESTS: list[dict] = [
    {
        "pickup_name": "Phoenix DC",
        "pickup_address": "4300 W Buckeye Rd, Phoenix, AZ",
        "pickup_lat": 33.4374,
        "pickup_lng": -112.1521,
        "dropoff_name": "Dallas Hub",
        "dropoff_address": "1201 N Riverfront Blvd, Dallas, TX",
        "dropoff_lat": 32.7876,
        "dropoff_lng": -96.8044,
        "pickup_time": iso_z(now_utc() + timedelta(hours=2)),
        "dropoff_time": iso_z(now_utc() + timedelta(hours=22)),
        "required_trailer_type": "VAN",
        "required_vehicle_type": "TRUCK",
    },
    {
        "pickup_name": "Tolleson Cold Storage",
        "pickup_address": "8400 W Buckeye Rd, Tolleson, AZ",
        "pickup_lat": 33.4362,
        "pickup_lng": -112.2393,
        "dropoff_name": "Albuquerque Foods DC",
        "dropoff_address": "9001 San Mateo Blvd NE, Albuquerque, NM",
        "dropoff_lat": 35.1702,
        "dropoff_lng": -106.5851,
        "pickup_time": iso_z(now_utc() + timedelta(hours=1)),
        "dropoff_time": iso_z(now_utc() + timedelta(hours=11)),
        "required_trailer_type": "REEFER",
        "required_vehicle_type": "TRUCK",
    },
    {
        "pickup_name": "Mesa Metals Yard",
        "pickup_address": "7120 E Ray Rd, Mesa, AZ",
        "pickup_lat": 33.3191,
        "pickup_lng": -111.6837,
        "dropoff_name": "Flagstaff Materials Site",
        "dropoff_address": "3940 E Huntington Dr, Flagstaff, AZ",
        "dropoff_lat": 35.2230,
        "dropoff_lng": -111.5829,
        "pickup_time": iso_z(now_utc() + timedelta(hours=3)),
        "dropoff_time": iso_z(now_utc() + timedelta(hours=9)),
        "required_trailer_type": "FLATBED",
        "required_vehicle_type": "TRUCK",
    },
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