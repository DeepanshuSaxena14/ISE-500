from __future__ import annotations

import os
import uuid
from typing import Any

from dotenv import load_dotenv
from supabase import create_client, Client

from mock_data import (
    MOCK_DRIVERS_PAYLOAD,
    MOCK_VEHICLES_PAYLOAD,
    MOCK_DRIVER_PERFORMANCE_PAYLOAD,
    MOCK_LOAD_REQUESTS,
)

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def chunked(items: list[dict], size: int = 200) -> list[list[dict]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def upsert_rows(table: str, rows: list[dict], on_conflict: str | None = None) -> None:
    if not rows:
        return

    for batch in chunked(rows):
        query = supabase.table(table).upsert(
            batch,
            on_conflict=on_conflict,
            returning="minimal",
        )
        query.execute()


def insert_rows(table: str, rows: list[dict]) -> None:
    if not rows:
        return

    for batch in chunked(rows):
        supabase.table(table).insert(batch, returning="minimal").execute()


def map_drivers(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for item in payload["data"]:
        basic = item.get("basic_info", {})
        loc = item.get("driver_location", {})
        current_load = item.get("loads", {}).get("driver_current_load")

        first_name = basic.get("driver_first_name")
        last_name = basic.get("driver_last_name")
        full_name = " ".join(x for x in [first_name, last_name] if x).strip()

        rows.append(
            {
                "driver_id": item["driver_id"],
                "first_name": first_name,
                "last_name": last_name,
                "full_name": full_name,
                "carrier": basic.get("carrier"),
                "work_status": basic.get("work_status"),
                "terminal": basic.get("terminal"),
                "driver_type": basic.get("driver_type"),
                "phone": basic.get("driver_phone_number"),
                "email": basic.get("driver_email"),
                "last_known_location": loc.get("last_known_location"),
                "latest_update": loc.get("latest_update"),
                "timezone": loc.get("timezone"),
                "current_load_id": str(current_load["load_id"]) if current_load else None,
                "current_load_show_id": current_load.get("load_show_id") if current_load else None,
                "current_load_origin": current_load.get("origin") if current_load else None,
                "current_load_destination": current_load.get("destination") if current_load else None,
                "current_load_pickup_date": current_load.get("pickup_date") if current_load else None,
                "current_load_delivery_date": current_load.get("delivery_date") if current_load else None,
            }
        )

    return rows


def map_vehicles(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    vehicle_rows: list[dict[str, Any]] = []
    assignment_rows: list[dict[str, Any]] = []

    for item in payload["data"]:
        vehicle_rows.append(
            {
                "vehicle_id": item["vehicle_id"],
                "owner_id": item.get("owner_id"),
                "owner_name": item.get("owner_name"),
                "vehicle_status": item.get("vehicle_status"),
                "vehicle_no": item.get("vehicle_no"),
                "vehicle_type": item.get("vehicle_type"),
                "vehicle_vin": item.get("vehicle_vin"),
                "gross_vehicle_weight": item.get("gross_vehicle_weight"),
                "trailer_type": item.get("trailer_type"),
                "vehicle_make": item.get("vehicle_make"),
                "vehicle_model": item.get("vehicle_model"),
                "created_date": item.get("created_date"),
            }
        )

        driver_ids = item.get("assignments_drivers", {}).get("driver_ids", [])
        for driver_id in driver_ids:
            assignment_rows.append(
                {
                    "vehicle_id": item["vehicle_id"],
                    "driver_id": driver_id,
                }
            )

    return vehicle_rows, assignment_rows


def map_driver_performance(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "driver_id": item["driver_id"],
            "oor_miles": item.get("oor_miles", 0),
            "schedule_miles": item.get("schedule_miles", 0),
            "actual_miles": item.get("actual_miles", 0),
            "schedule_time": item.get("schedule_time", 0),
            "actual_time": item.get("actual_time", 0),
        }
        for item in payload["data"]
    ]


def map_load_requests(load_requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for req in load_requests:
        rows.append(
            {
                "id": str(uuid.uuid4()),
                "pickup_name": req["pickup_name"],
                "pickup_address": req["pickup_address"],
                "pickup_lat": req["pickup_lat"],
                "pickup_lng": req["pickup_lng"],
                "dropoff_name": req["dropoff_name"],
                "dropoff_address": req["dropoff_address"],
                "dropoff_lat": req["dropoff_lat"],
                "dropoff_lng": req["dropoff_lng"],
                "pickup_time": req["pickup_time"],   # ISO string is fine for timestamptz
                "dropoff_time": req["dropoff_time"],
                "required_trailer_type": req.get("required_trailer_type"),
                "required_vehicle_type": req.get("required_vehicle_type", "TRUCK"),
            }
        )

    return rows


def main() -> None:
    driver_rows = map_drivers(MOCK_DRIVERS_PAYLOAD)
    vehicle_rows, assignment_rows = map_vehicles(MOCK_VEHICLES_PAYLOAD)
    performance_rows = map_driver_performance(MOCK_DRIVER_PERFORMANCE_PAYLOAD)
    load_rows = map_load_requests(MOCK_LOAD_REQUESTS)

    # Parent tables first
    upsert_rows("drivers", driver_rows, on_conflict="driver_id")
    upsert_rows("vehicles", vehicle_rows, on_conflict="vehicle_id")
    upsert_rows("driver_performance", performance_rows, on_conflict="driver_id")

    # Join table after parent rows exist
    upsert_rows("vehicle_driver_assignments", assignment_rows, on_conflict="vehicle_id,driver_id")

    # Optional loads
    insert_rows("loads", load_rows)

    print("Seed complete.")
    print(f"drivers: {len(driver_rows)}")
    print(f"vehicles: {len(vehicle_rows)}")
    print(f"vehicle_driver_assignments: {len(assignment_rows)}")
    print(f"driver_performance: {len(performance_rows)}")
    print(f"loads: {len(load_rows)}")


if __name__ == "__main__":
    main()