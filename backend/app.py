from __future__ import annotations

import os
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from dotenv import load_dotenv
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import Client, create_client

from ai.tools.llm import generate_text

app = Flask(__name__)
CORS(app)

# ------------------------------------------------------------
# Geospatial helpers
# ------------------------------------------------------------

CITY_COORDS = {
    "Phoenix, AZ": (33.4484, -112.0740),
    "Los Angeles, CA": (34.0522, -118.2437),
    "Dallas, TX": (32.7767, -96.7970),
    "Seattle, WA": (47.6062, -122.3321),
    "Chicago, IL": (41.8781, -87.6298),
    "Atlanta, GA": (33.7490, -84.3880),
    "New York, NY": (40.7128, -74.0060),
    "Miami, FL": (25.7617, -80.1918),
    "Denver, CO": (39.7392, -104.9903),
    "Salt Lake City, UT": (40.7608, -111.8910),
}

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8 # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ------------------------------------------------------------
# .env diagnostics
# ------------------------------------------------------------
ENV_PATH = Path("/app/.env")
cwd = Path.cwd()

print("[startup] Current working directory:", cwd)
print("[startup] Expected .env path:", ENV_PATH)
print("[startup] .env exists:", ENV_PATH.exists())

if ENV_PATH.exists():
    print("[startup] .env file found, loading it now")
    load_dotenv(dotenv_path=ENV_PATH)
else:
    print("[startup] .env file not found at /app/.env, trying default load_dotenv()")
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
PORT = int(os.getenv("PORT", "8000"))

print("[startup] SUPABASE_URL present:", bool(SUPABASE_URL))
print("[startup] SUPABASE_SERVICE_ROLE_KEY present:", bool(SUPABASE_SERVICE_ROLE_KEY))
print("[startup] PORT:", PORT)

if SUPABASE_URL:
    print("[startup] SUPABASE_URL preview:", SUPABASE_URL[:40] + "...")
else:
    print("[startup] SUPABASE_URL is missing")

if SUPABASE_SERVICE_ROLE_KEY:
    print("[startup] SUPABASE_SERVICE_ROLE_KEY preview:", SUPABASE_SERVICE_ROLE_KEY[:8] + "..." + SUPABASE_SERVICE_ROLE_KEY[-4:])
else:
    print("[startup] SUPABASE_SERVICE_ROLE_KEY is missing")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# ============================================================
# Data models
# ============================================================

@dataclass
class LoadRecord:
    id: str
    pickup_name: str
    pickup_address: str
    pickup_lat: float
    pickup_lng: float
    dropoff_name: str
    dropoff_address: str
    dropoff_lat: float
    dropoff_lng: float
    pickup_time: str
    dropoff_time: str
    required_trailer_type: Optional[str] = None
    required_vehicle_type: Optional[str] = "TRUCK"
    weight_lbs: Optional[float] = 0.0
    created_at: Optional[str] = None


@dataclass
class DriverProfile:
    driver_id: int
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    carrier: Optional[str]
    work_status: Optional[str]
    terminal: Optional[str]
    driver_type: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    last_known_location: Optional[str]
    latest_update: Optional[int]
    timezone: Optional[str]
    current_load_id: Optional[str]
    current_load_show_id: Optional[str]
    current_load_origin: Optional[str]
    current_load_destination: Optional[str]
    current_load_pickup_date: Optional[int]
    current_load_delivery_date: Optional[int]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class VehicleRecord:
    vehicle_id: int
    owner_id: Optional[int]
    owner_name: Optional[str]
    vehicle_status: Optional[str]
    vehicle_no: Optional[str]
    vehicle_type: Optional[str]
    vehicle_vin: Optional[str]
    gross_vehicle_weight: Optional[int]
    trailer_type: Optional[str]
    vehicle_make: Optional[str]
    vehicle_model: Optional[str]
    created_date: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class DriverPerformance:
    driver_id: int
    oor_miles: float
    schedule_miles: float
    actual_miles: float
    schedule_time: int
    actual_time: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class DispatchCandidate:
    driver: DriverProfile
    vehicle: Optional[VehicleRecord]
    performance: Optional[DriverPerformance]


# ============================================================
# Utility helpers
# ============================================================

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def epoch_ms_to_datetime(value: Optional[int]) -> Optional[datetime]:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def format_eta_label(delivery_date_ms: Optional[int]) -> Optional[str]:
    dt = epoch_ms_to_datetime(delivery_date_ms)
    if not dt:
        return None

    now = datetime.now(timezone.utc)

    if dt.date() == now.date():
        return f"Today {dt.strftime('%H:%M')}"
    if (dt.date() - now.date()).days == 1:
        return f"Tomorrow {dt.strftime('%H:%M')}"
    return dt.strftime("%Y-%m-%d %H:%M UTC")
    if dt.date() == now.date():
        return f"Today {dt.strftime('%H:%M')}"
    if (dt.date() - now.date()).days == 1:
        return f"Tomorrow {dt.strftime('%H:%M')}"
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def estimate_progress_pct(pickup_ms: Optional[int], delivery_ms: Optional[int]) -> Optional[int]:
    if pickup_ms is None or delivery_ms is None:
        return None
    if delivery_ms <= pickup_ms:
        return None

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    if now_ms <= pickup_ms:
        return 0
    if now_ms >= delivery_ms:
        return 100

    pct = ((now_ms - pickup_ms) / (delivery_ms - pickup_ms)) * 100
    return max(0, min(100, int(round(pct))))


def map_work_status_to_label(work_status: Optional[str]) -> str:
    mapping = {
        "IN_TRANSIT": "En Route",
        "AVAILABLE": "Available",
        "OFF_DUTY": "Off Duty",
        "DRIVING": "Driving",
        "ON_DUTY": "On Duty",
        "INACTIVE": "Inactive",
    }
    return mapping.get(work_status or "", work_status or "Unknown")


def build_load_label(driver: DriverProfile) -> Optional[str]:
    if driver.current_load_origin and driver.current_load_destination:
        return f"{driver.current_load_origin} -> {driver.current_load_destination}"
    return None


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def build_alerts(
    driver: DriverProfile,
    vehicle: Optional[VehicleRecord],
    perf: Optional[DriverPerformance],
) -> List[dict]:
    alerts: List[dict] = []

    if vehicle is None:
        alerts.append({"severity": "high", "text": "No assigned vehicle found"})
    else:
        if vehicle.vehicle_status != "ACTIVE":
            alerts.append({"severity": "high", "text": f"Vehicle status is {vehicle.vehicle_status}"})

    if driver.current_load_id is not None:
        alerts.append({"severity": "low", "text": "Driver currently assigned to an active load"})

    if driver.work_status in {"OFF_DUTY", "INACTIVE"}:
        alerts.append({"severity": "high", "text": f"Driver work status is {driver.work_status}"})

    if perf is not None:
        oor_ratio = safe_ratio(perf.oor_miles, perf.schedule_miles)
        time_ratio = safe_ratio(float(perf.actual_time), float(perf.schedule_time))
        mile_ratio = safe_ratio(perf.actual_miles, perf.schedule_miles)

        if oor_ratio > 0.10:
            alerts.append({"severity": "high", "text": f"High out-of-route ratio: {oor_ratio:.1%}"})
        elif oor_ratio > 0.05:
            alerts.append({"severity": "medium", "text": f"Moderate out-of-route ratio: {oor_ratio:.1%}"})

        if time_ratio > 1.15:
            alerts.append({
                "severity": "medium",
                "text": f"Actual time exceeds schedule by {(time_ratio - 1) * 100:.1f}%"
            })
            alerts.append({
                "severity": "medium",
                "text": f"Actual time exceeds schedule by {(time_ratio - 1) * 100:.1f}%"
            })

        if mile_ratio > 1.10:
            alerts.append({
                "severity": "medium",
                "text": f"Actual miles exceed scheduled miles by {(mile_ratio - 1) * 100:.1f}%"
            })
            alerts.append({
                "severity": "medium",
                "text": f"Actual miles exceed scheduled miles by {(mile_ratio - 1) * 100:.1f}%"
            })
    else:
        alerts.append({"severity": "low", "text": "No driver performance record found"})

    return alerts


# ============================================================
# Normalizers for upstream payloads
# ============================================================

def normalize_driver(item: dict) -> DriverProfile:
    basic = item.get("basic_info", {}) or {}
    loc = item.get("driver_location", {}) or {}
    loads = item.get("loads", {}) or {}
    current_load = loads.get("driver_current_load") or {}

    first = basic.get("driver_first_name")
    last = basic.get("driver_last_name")
    full_name = " ".join(part for part in [first, last] if part).strip() or None

    raw_load_id = current_load.get("load_id")
    normalized_load_id = str(raw_load_id) if raw_load_id is not None else None

    return DriverProfile(
        driver_id=int(item["driver_id"]),
        first_name=first,
        last_name=last,
        full_name=full_name,
        carrier=basic.get("carrier"),
        work_status=basic.get("work_status"),
        terminal=basic.get("terminal"),
        driver_type=basic.get("driver_type"),
        phone=basic.get("driver_phone_number"),
        email=basic.get("driver_email"),
        last_known_location=loc.get("last_known_location"),
        latest_update=loc.get("latest_update"),
        timezone=loc.get("timezone"),
        current_load_id=normalized_load_id,
        current_load_show_id=current_load.get("load_show_id"),
        current_load_origin=current_load.get("origin"),
        current_load_destination=current_load.get("destination"),
        current_load_pickup_date=current_load.get("pickup_date"),
        current_load_delivery_date=current_load.get("delivery_date"),
    )


def normalize_vehicle(item: dict) -> VehicleRecord:
    return VehicleRecord(
        vehicle_id=int(item["vehicle_id"]),
        owner_id=item.get("owner_id"),
        owner_name=item.get("owner_name"),
        vehicle_status=item.get("vehicle_status"),
        vehicle_no=item.get("vehicle_no"),
        vehicle_type=item.get("vehicle_type"),
        vehicle_vin=item.get("vehicle_vin"),
        gross_vehicle_weight=item.get("gross_vehicle_weight"),
        trailer_type=item.get("trailer_type"),
        vehicle_make=item.get("vehicle_make"),
        vehicle_model=item.get("vehicle_model"),
        created_date=item.get("created_date"),
    )


def extract_vehicle_driver_assignments(item: dict) -> list[dict]:
    assignments = item.get("assignments_drivers", {}) or {}
    driver_ids = assignments.get("driver_ids", []) or []

    if not driver_ids:
        driver_ids = [
            d.get("assign_driver_id")
            for d in assignments.get("assign_driver_info", [])
            if d.get("assign_driver_id") is not None
        ]

    return [
        {
            "vehicle_id": int(item["vehicle_id"]),
            "driver_id": int(driver_id),
        }
        for driver_id in driver_ids
    ]

def extract_vehicle_driver_assignments(item: dict) -> list[dict]:
    assignments = item.get("assignments_drivers", {}) or {}
    driver_ids = assignments.get("driver_ids", []) or []

    if not driver_ids:
        driver_ids = [
            d.get("assign_driver_id")
            for d in assignments.get("assign_driver_info", [])
            if d.get("assign_driver_id") is not None
        ]

    return [
        {
            "vehicle_id": int(item["vehicle_id"]),
            "driver_id": int(driver_id),
        }
        for driver_id in driver_ids
    ]


def normalize_performance(item: dict) -> DriverPerformance:
    return DriverPerformance(
        driver_id=int(item["driver_id"]),
        oor_miles=float(item.get("oor_miles", 0) or 0),
        schedule_miles=float(item.get("schedule_miles", 0) or 0),
        actual_miles=float(item.get("actual_miles", 0) or 0),
        schedule_time=int(item.get("schedule_time", 0) or 0),
        actual_time=int(item.get("actual_time", 0) or 0),
    )


# ============================================================
# Supabase fetch helpers
# ============================================================

def fetch_all_drivers() -> list[DriverProfile]:
    res = supabase.table("drivers").select("*").execute()
    return [DriverProfile(**row) for row in (res.data or [])]


def fetch_all_vehicles() -> list[VehicleRecord]:
    res = supabase.table("vehicles").select("*").execute()
    return [VehicleRecord(**row) for row in (res.data or [])]


def fetch_all_performance() -> dict[int, DriverPerformance]:
    res = supabase.table("driver_performance").select("*").execute()
    perf_map: dict[int, DriverPerformance] = {}

    for row in (res.data or []):
        perf = DriverPerformance(
            driver_id=int(row["driver_id"]),
            oor_miles=float(row["oor_miles"]),
            schedule_miles=float(row["schedule_miles"]),
            actual_miles=float(row["actual_miles"]),
            schedule_time=int(row["schedule_time"]),
            actual_time=int(row["actual_time"]),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
        perf_map[perf.driver_id] = perf

    return perf_map


def fetch_vehicle_assignments() -> dict[int, VehicleRecord]:
    assignments_res = supabase.table("vehicle_driver_assignments").select("vehicle_id,driver_id").execute()
    vehicles = fetch_all_vehicles()
    vehicle_by_id = {vehicle.vehicle_id: vehicle for vehicle in vehicles}

    vehicle_by_driver: dict[int, VehicleRecord] = {}
    for row in (assignments_res.data or []):
        vehicle = vehicle_by_id.get(int(row["vehicle_id"]))
        if vehicle:
            vehicle_by_driver[int(row["driver_id"])] = vehicle

    return vehicle_by_driver


def fetch_load(load_id: str) -> Optional[LoadRecord]:
    res = supabase.table("loads").select("*").eq("id", load_id).limit(1).execute()
    if not res.data:
        return None

    row = res.data[0]
    return LoadRecord(
        id=row["id"],
        pickup_name=row["pickup_name"],
        pickup_address=row["pickup_address"],
        pickup_lat=float(row["pickup_lat"]),
        pickup_lng=float(row["pickup_lng"]),
        dropoff_name=row["dropoff_name"],
        dropoff_address=row["dropoff_address"],
        dropoff_lat=float(row["dropoff_lat"]),
        dropoff_lng=float(row["dropoff_lng"]),
        pickup_time=row["pickup_time"],
        dropoff_time=row["dropoff_time"],
        required_trailer_type=row.get("required_trailer_type"),
        required_vehicle_type=row.get("required_vehicle_type"),
        weight_lbs=float(row.get("weight_lbs", 0.0) or 0.0),
        created_at=row.get("created_at"),
    )


def build_dispatch_candidates() -> List[DispatchCandidate]:
    drivers = fetch_all_drivers()
    vehicle_by_driver = fetch_vehicle_assignments()
    performance_by_driver = fetch_all_performance()

    candidates: List[DispatchCandidate] = []
    for driver in drivers:
        candidates.append(
            DispatchCandidate(
                driver=driver,
                vehicle=vehicle_by_driver.get(driver.driver_id),
                performance=performance_by_driver.get(driver.driver_id),
            )
        )
    return candidates


# ============================================================
# Supabase fetch helpers
# ============================================================

def fetch_all_drivers() -> list[DriverProfile]:
    res = supabase.table("drivers").select("*").execute()
    return [DriverProfile(**row) for row in (res.data or [])]


def fetch_all_vehicles() -> list[VehicleRecord]:
    res = supabase.table("vehicles").select("*").execute()
    return [VehicleRecord(**row) for row in (res.data or [])]


def fetch_all_performance() -> dict[int, DriverPerformance]:
    res = supabase.table("driver_performance").select("*").execute()
    perf_map: dict[int, DriverPerformance] = {}

    for row in (res.data or []):
        perf = DriverPerformance(
            driver_id=int(row["driver_id"]),
            oor_miles=float(row["oor_miles"]),
            schedule_miles=float(row["schedule_miles"]),
            actual_miles=float(row["actual_miles"]),
            schedule_time=int(row["schedule_time"]),
            actual_time=int(row["actual_time"]),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
        perf_map[perf.driver_id] = perf

    return perf_map


def fetch_vehicle_assignments() -> dict[int, VehicleRecord]:
    assignments_res = supabase.table("vehicle_driver_assignments").select("vehicle_id,driver_id").execute()
    vehicles = fetch_all_vehicles()
    vehicle_by_id = {vehicle.vehicle_id: vehicle for vehicle in vehicles}

    vehicle_by_driver: dict[int, VehicleRecord] = {}
    for row in (assignments_res.data or []):
        vehicle = vehicle_by_id.get(int(row["vehicle_id"]))
        if vehicle:
            vehicle_by_driver[int(row["driver_id"])] = vehicle

    return vehicle_by_driver


def fetch_load(load_id: str) -> Optional[LoadRecord]:
    res = supabase.table("loads").select("*").eq("id", load_id).limit(1).execute()
    if not res.data:
        return None

    row = res.data[0]
    return LoadRecord(
        id=row["id"],
        pickup_name=row["pickup_name"],
        pickup_address=row["pickup_address"],
        pickup_lat=float(row["pickup_lat"]),
        pickup_lng=float(row["pickup_lng"]),
        dropoff_name=row["dropoff_name"],
        dropoff_address=row["dropoff_address"],
        dropoff_lat=float(row["dropoff_lat"]),
        dropoff_lng=float(row["dropoff_lng"]),
        pickup_time=row["pickup_time"],
        dropoff_time=row["dropoff_time"],
        required_trailer_type=row.get("required_trailer_type"),
        required_vehicle_type=row.get("required_vehicle_type"),
        created_at=row.get("created_at"),
    )


def build_dispatch_candidates() -> List[DispatchCandidate]:
    drivers = fetch_all_drivers()
    vehicle_by_driver = fetch_vehicle_assignments()
    performance_by_driver = fetch_all_performance()

    candidates: List[DispatchCandidate] = []
    for driver in drivers:
        candidates.append(
            DispatchCandidate(
                driver=driver,
                vehicle=vehicle_by_driver.get(driver.driver_id),
                performance=performance_by_driver.get(driver.driver_id),
            )
        )
    return candidates


# ============================================================
# Supabase fetch helpers
# ============================================================

def fetch_all_drivers() -> list[DriverProfile]:
    res = supabase.table("drivers").select("*").execute()
    return [DriverProfile(**row) for row in (res.data or [])]


def fetch_all_vehicles() -> list[VehicleRecord]:
    res = supabase.table("vehicles").select("*").execute()
    return [VehicleRecord(**row) for row in (res.data or [])]


def fetch_all_performance() -> dict[int, DriverPerformance]:
    res = supabase.table("driver_performance").select("*").execute()
    perf_map: dict[int, DriverPerformance] = {}

    for row in (res.data or []):
        perf = DriverPerformance(
            driver_id=int(row["driver_id"]),
            oor_miles=float(row["oor_miles"]),
            schedule_miles=float(row["schedule_miles"]),
            actual_miles=float(row["actual_miles"]),
            schedule_time=int(row["schedule_time"]),
            actual_time=int(row["actual_time"]),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
        perf_map[perf.driver_id] = perf

    return perf_map


def fetch_vehicle_assignments() -> dict[int, VehicleRecord]:
    assignments_res = supabase.table("vehicle_driver_assignments").select("vehicle_id,driver_id").execute()
    vehicles = fetch_all_vehicles()
    vehicle_by_id = {vehicle.vehicle_id: vehicle for vehicle in vehicles}

    vehicle_by_driver: dict[int, VehicleRecord] = {}
    for row in (assignments_res.data or []):
        vehicle = vehicle_by_id.get(int(row["vehicle_id"]))
        if vehicle:
            vehicle_by_driver[int(row["driver_id"])] = vehicle

    return vehicle_by_driver


def fetch_load(load_id: str) -> Optional[LoadRecord]:
    res = supabase.table("loads").select("*").eq("id", load_id).limit(1).execute()
    if not res.data:
        return None

    row = res.data[0]
    return LoadRecord(
        id=row["id"],
        pickup_name=row["pickup_name"],
        pickup_address=row["pickup_address"],
        pickup_lat=float(row["pickup_lat"]),
        pickup_lng=float(row["pickup_lng"]),
        dropoff_name=row["dropoff_name"],
        dropoff_address=row["dropoff_address"],
        dropoff_lat=float(row["dropoff_lat"]),
        dropoff_lng=float(row["dropoff_lng"]),
        pickup_time=row["pickup_time"],
        dropoff_time=row["dropoff_time"],
        required_trailer_type=row.get("required_trailer_type"),
        required_vehicle_type=row.get("required_vehicle_type"),
        created_at=row.get("created_at"),
    )


def build_dispatch_candidates() -> List[DispatchCandidate]:
    drivers = fetch_all_drivers()
    vehicle_by_driver = fetch_vehicle_assignments()
    performance_by_driver = fetch_all_performance()

    candidates: List[DispatchCandidate] = []
    for driver in drivers:
        candidates.append(
            DispatchCandidate(
                driver=driver,
                vehicle=vehicle_by_driver.get(driver.driver_id),
                performance=performance_by_driver.get(driver.driver_id),
            )
        )
    return candidates


def build_driver_card(candidate: DispatchCandidate, load: Optional[LoadRecord] = None) -> dict:
    driver = candidate.driver
    vehicle = candidate.vehicle
    perf = candidate.performance

    progress_pct = estimate_progress_pct(
        driver.current_load_pickup_date,
        driver.current_load_delivery_date,
    )

    alerts = build_alerts(driver, vehicle, perf)

    # Calculate Distance/Proximity
    distance = 0.0
    if load and driver.last_known_location in CITY_COORDS:
        d_lat, d_lon = CITY_COORDS[driver.last_known_location]
        distance = haversine(d_lat, d_lon, load.pickup_lat, load.pickup_lng)

    # Calculate Mock HOS (Hours of Service)
    # Available = full 11h, In Transit = partial
    hos_base = 11.0 if driver.work_status == "AVAILABLE" else 5.5
    # Deterministic drift based on ID
    hos_remaining = max(0.0, hos_base - ((driver.driver_id % 10) * 0.5))

    # Calculate Distance/Proximity
    distance = 0.0
    if load and driver.last_known_location in CITY_COORDS:
        d_lat, d_lon = CITY_COORDS[driver.last_known_location]
        distance = haversine(d_lat, d_lon, load.pickup_lat, load.pickup_lng)

    # Calculate Mock HOS (Hours of Service)
    # Available = full 11h, In Transit = partial
    hos_base = 11.0 if driver.work_status == "AVAILABLE" else 5.5
    # Deterministic drift based on ID
    hos_remaining = max(0.0, hos_base - ((driver.driver_id % 10) * 0.5))

    return {
        "driver_id": driver.driver_id,
        "name": driver.full_name,
        "vehicle_no": vehicle.vehicle_no if vehicle else None,
        "vehicle_id": vehicle.vehicle_id if vehicle else None,
        "vehicle_status": vehicle.vehicle_status if vehicle else None,
        "vehicle_type": vehicle.vehicle_type if vehicle else None,
        "trailer_type": vehicle.trailer_type if vehicle else None,
        "status_label": map_work_status_to_label(driver.work_status),
        "location_label": driver.last_known_location,
        "load_label": build_load_label(driver),
        "current_load": {
            "load_id": driver.current_load_id,
            "load_show_id": driver.current_load_show_id,
            "origin": driver.current_load_origin,
            "destination": driver.current_load_destination,
            "pickup_date": driver.current_load_pickup_date,
            "delivery_date": driver.current_load_delivery_date,
        } if driver.current_load_id is not None else None,
        "hos_remaining_hours": hos_remaining,
        "distance_to_pickup": round(distance, 1),
        "load_progress_pct": progress_pct,
        "eta_label": format_eta_label(driver.current_load_delivery_date),
        "fuel_pct": 80 - (driver.driver_id % 40), # Mocked but stable
        "alerts": alerts,
        "performance": {
            "oor_miles": perf.oor_miles,
            "schedule_miles": perf.schedule_miles,
            "actual_miles": perf.actual_miles,
            "schedule_time": perf.schedule_time,
            "actual_time": perf.actual_time,
        } if perf else None,
    }


# ============================================================
# Recommendation logic
# ============================================================

def score_candidate(load: LoadRecord, candidate: DispatchCandidate) -> dict:
    score = 100.0
    reasons: List[str] = []
    warnings: List[str] = []

    driver = candidate.driver
    vehicle = candidate.vehicle
    perf = candidate.performance

    if driver.work_status in {"OFF_DUTY", "INACTIVE"}:
        score -= 50
        warnings.append(f"Driver work status is {driver.work_status}")
    else:
        reasons.append(f"Driver work status is {driver.work_status}")

    if driver.current_load_id is not None:
        score -= 35
        warnings.append("Driver already has a current load assigned")
    else:
        reasons.append("Driver has no current active load")

    if vehicle is None:
        score -= 40
        warnings.append("No assigned vehicle found")
    else:
        if vehicle.vehicle_status != "ACTIVE":
            score -= 40
            warnings.append(f"Vehicle status is {vehicle.vehicle_status}")
        else:
            reasons.append("Assigned vehicle is active")

        if load.required_vehicle_type and vehicle.vehicle_type != load.required_vehicle_type:
            score -= 20
            warnings.append("Vehicle type mismatch")
        else:
            reasons.append(f"Vehicle type matches: {vehicle.vehicle_type}")

        if load.required_trailer_type:
            if vehicle.trailer_type != load.required_trailer_type:
                score -= 25
                warnings.append("Trailer type mismatch")
            else:
                reasons.append(f"Trailer type matches: {vehicle.trailer_type}")

    if perf:
        oor_ratio = safe_ratio(perf.oor_miles, perf.schedule_miles)
        time_ratio = safe_ratio(float(perf.actual_time), float(perf.schedule_time))
        mile_ratio = safe_ratio(perf.actual_miles, perf.schedule_miles)

        if oor_ratio > 0.05:
            penalty = min(oor_ratio * 100, 20)
            score -= penalty
            warnings.append(f"High out-of-route ratio: {oor_ratio:.2%}")
        else:
            reasons.append(f"Low out-of-route ratio: {oor_ratio:.2%}")

        if time_ratio > 1.10:
            score -= 10
            warnings.append(f"Actual time exceeds schedule: {time_ratio:.2f}x")
        else:
            reasons.append("Time performance is within tolerance")

        if mile_ratio > 1.10:
            score -= 10
            warnings.append(f"Actual miles exceed schedule: {mile_ratio:.2f}x")
        else:
            reasons.append("Mileage performance is within tolerance")
    else:
        warnings.append("No performance record found")

    # 1. Timing Feasibility Check (Edge Case: Driver too far for appointment)
    distance = 0.0
    if driver.last_known_location in CITY_COORDS:
        d_lat, d_lon = CITY_COORDS[driver.last_known_location]
        distance = haversine(d_lat, d_lon, load.pickup_lat, load.pickup_lng)
    
    avg_speed = 55.0 # mph
    transit_hours_required = distance / avg_speed
    
    try:
        pickup_dt = datetime.fromisoformat(load.pickup_time.replace("Z", "+00:00"))
        now_dt = datetime.now(timezone.utc)
        time_until_pickup = (pickup_dt - now_dt).total_seconds() / 3600.0
    except:
        time_until_pickup = 100.0 # Fallback

    if transit_hours_required > time_until_pickup:
        score -= 80
        warnings.append(f"INFEASIBLE: Arrival estimate ({transit_hours_required:.1f}h) exceeds pickup window ({time_until_pickup:.1f}h)")
    else:
        reasons.append(f"Timing is feasible: {transit_hours_required:.1f}h vs {time_until_pickup:.1f}h")

    # 2. Sequential & Consolidation Logic (Edge Case: On-Duty but fits/near)
    is_on_duty = driver.work_status in {"ON_DUTY", "IN_TRANSIT", "DRIVING"}
    
    if is_on_duty:
        # Check Deviation Delta
        if distance < 30: # If passing right by
            score += 25
            reasons.append(f"Strategic Pick: Driver is currently on-duty but passing near pickup ({distance:.1f} mi)")
        
        # Check Consolidation Capacity (Mocking current load weight as 20k for now if on-duty)
        max_capacity = vehicle.gross_vehicle_weight - 35000 if vehicle and vehicle.gross_vehicle_weight else 45000
        assumed_current_weight = 20000 
        new_load_weight = load.weight_lbs or 0.0
        
        if (assumed_current_weight + new_load_weight) <= max_capacity:
            score += 15
            reasons.append(f"LTL Opportunity: Vehicle has capacity for consolidation ({new_load_weight} lbs)")
        else:
            score -= 20
            warnings.append(f"Overweight Risk: Consolidation exceeds vehicle capacity")

    # 3. Proximity Scaling
    if distance > 350:
        penalty = min(30, (distance - 350) / 15)
        score -= penalty
        warnings.append(f"High Deadhead: Driver is {distance:.1f} mi away")
    elif distance < 50:
        score += 10
        reasons.append(f"Local Favorite: Driver is within 50mi hub ({distance:.1f} mi)")

    # HOS Penalty
    hos_base = 11.0 if driver.work_status == "AVAILABLE" else 5.5
    hos_remaining = max(0.0, hos_base - ((driver.driver_id % 10) * 0.5))
    
    if hos_remaining < 8.5:
        score -= 15
        warnings.append(f"HOS remaining is low: {hos_remaining:.1f}h")
    else:
        reasons.append(f"HOS compliance is solid: {hos_remaining:.1f}h")

    score = max(0.0, min(100.0, round(score, 2)))
    feasible = score >= 50 and hos_remaining >= 2.0 # Strict cutoff for feasibility

    return {
        "driver_id": driver.driver_id,
        "driver_name": driver.full_name,
        "vehicle_id": vehicle.vehicle_id if vehicle else None,
        "vehicle_no": vehicle.vehicle_no if vehicle else None,
        "score": score,
        "feasible": feasible,
        "reasons": reasons,
        "warnings": warnings,
        "driver_card": build_driver_card(candidate, load),
    }


# ============================================================
# Routes
# ============================================================

@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/health/db")
def health_db():
    try:
        res = supabase.table("drivers").select("driver_id", count="exact").limit(1).execute()
        return jsonify({
            "status": "ok",
            "drivers_count": res.count,
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500
    return jsonify({"status": "ok"})


@app.get("/health/db")
def health_db():
    try:
        res = supabase.table("drivers").select("driver_id", count="exact").limit(1).execute()
        return jsonify({
            "status": "ok",
            "drivers_count": res.count,
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500


@app.post("/ingest/drivers")
def ingest_drivers():
    payload = request.get_json(force=True)
    items = payload.get("data", [])

    rows = [asdict(normalize_driver(item)) for item in items]

    for row in rows:
        row.pop("created_at", None)
        row.pop("updated_at", None)

    if rows:
        supabase.table("drivers").upsert(rows).execute()
        supabase.table("ingest_driver_batches").insert({"payload": payload}).execute()
    rows = [asdict(normalize_driver(item)) for item in items]

    for row in rows:
        row.pop("created_at", None)
        row.pop("updated_at", None)

    if rows:
        supabase.table("drivers").upsert(rows).execute()
        supabase.table("ingest_driver_batches").insert({"payload": payload}).execute()

    return jsonify({
        "success": True,
        "ingested_count": len(rows),
        "ingested_count": len(rows),
    })


@app.post("/ingest/vehicles")
def ingest_vehicles():
    payload = request.get_json(force=True)
    items = payload.get("data", [])

    vehicle_rows = []
    assignment_rows = []

    vehicle_rows = []
    assignment_rows = []

    for item in items:
        vehicle_row = asdict(normalize_vehicle(item))
        vehicle_row.pop("created_at", None)
        vehicle_row.pop("updated_at", None)
        vehicle_rows.append(vehicle_row)

        assignment_rows.extend(extract_vehicle_driver_assignments(item))

    if vehicle_rows:
        supabase.table("vehicles").upsert(vehicle_rows).execute()
        supabase.table("ingest_vehicle_batches").insert({"payload": payload}).execute()

    affected_vehicle_ids = list({row["vehicle_id"] for row in assignment_rows})
    if affected_vehicle_ids:
        supabase.table("vehicle_driver_assignments").delete().in_("vehicle_id", affected_vehicle_ids).execute()

    if assignment_rows:
        supabase.table("vehicle_driver_assignments").upsert(
            assignment_rows,
            on_conflict="vehicle_id,driver_id"
        ).execute()
        vehicle_row = asdict(normalize_vehicle(item))
        vehicle_row.pop("created_at", None)
        vehicle_row.pop("updated_at", None)
        vehicle_rows.append(vehicle_row)

        assignment_rows.extend(extract_vehicle_driver_assignments(item))

    if vehicle_rows:
        supabase.table("vehicles").upsert(vehicle_rows).execute()
        supabase.table("ingest_vehicle_batches").insert({"payload": payload}).execute()

    affected_vehicle_ids = list({row["vehicle_id"] for row in assignment_rows})
    if affected_vehicle_ids:
        supabase.table("vehicle_driver_assignments").delete().in_("vehicle_id", affected_vehicle_ids).execute()

    if assignment_rows:
        supabase.table("vehicle_driver_assignments").upsert(
            assignment_rows,
            on_conflict="vehicle_id,driver_id"
        ).execute()

    return jsonify({
        "success": True,
        "ingested_count": len(vehicle_rows),
        "assignment_count": len(assignment_rows),
        "ingested_count": len(vehicle_rows),
        "assignment_count": len(assignment_rows),
    })


@app.post("/ingest/driver-performance")
def ingest_driver_performance():
    payload = request.get_json(force=True)
    items = payload.get("data", [])

    rows = [asdict(normalize_performance(item)) for item in items]

    for row in rows:
        row.pop("created_at", None)
        row.pop("updated_at", None)

    if rows:
        supabase.table("driver_performance").upsert(rows).execute()
        supabase.table("ingest_driver_performance_batches").insert({"payload": payload}).execute()
    rows = [asdict(normalize_performance(item)) for item in items]

    for row in rows:
        row.pop("created_at", None)
        row.pop("updated_at", None)

    if rows:
        supabase.table("driver_performance").upsert(rows).execute()
        supabase.table("ingest_driver_performance_batches").insert({"payload": payload}).execute()

    return jsonify({
        "success": True,
        "ingested_count": len(rows),
        "ingested_count": len(rows),
    })


@app.get("/debug/drivers")
def debug_drivers():
    return jsonify(supabase.table("drivers").select("*").execute().data)
    return jsonify(supabase.table("drivers").select("*").execute().data)


@app.get("/debug/vehicles")
def debug_vehicles():
    return jsonify(supabase.table("vehicles").select("*").execute().data)
    return jsonify(supabase.table("vehicles").select("*").execute().data)


@app.get("/debug/performance")
def debug_performance():
    return jsonify(supabase.table("driver_performance").select("*").execute().data)


@app.get("/debug/vehicle-assignments")
def debug_vehicle_assignments():
    return jsonify(supabase.table("vehicle_driver_assignments").select("*").execute().data)
    return jsonify(supabase.table("driver_performance").select("*").execute().data)


@app.get("/debug/vehicle-assignments")
def debug_vehicle_assignments():
    return jsonify(supabase.table("vehicle_driver_assignments").select("*").execute().data)


@app.get("/debug/candidates")
def debug_candidates():
    candidates = build_dispatch_candidates()
    return jsonify([
        {
            "driver": asdict(c.driver),
            "vehicle": asdict(c.vehicle) if c.vehicle else None,
            "performance": asdict(c.performance) if c.performance else None,
        }
        for c in candidates
    ])


@app.get("/driver-cards")
def get_driver_cards():
    candidates = build_dispatch_candidates()
    cards = [build_driver_card(candidate) for candidate in candidates]
    return jsonify(cards)


@app.get("/driver-cards/<int:driver_id>")
def get_driver_card(driver_id: int):
    candidates = build_dispatch_candidates()
    for candidate in candidates:
        if candidate.driver.driver_id == driver_id:
            return jsonify(build_driver_card(candidate))
    return jsonify({"error": "Driver not found"}), 404


@app.post("/loads")
def create_load():
    payload = request.get_json(force=True)

    load_id = str(uuid4())
    row = {
        "id": load_id,
        "pickup_name": payload["pickup_name"],
        "pickup_address": payload["pickup_address"],
        "pickup_lat": float(payload["pickup_lat"]),
        "pickup_lng": float(payload["pickup_lng"]),
        "dropoff_name": payload["dropoff_name"],
        "dropoff_address": payload["dropoff_address"],
        "dropoff_lat": float(payload["dropoff_lat"]),
        "dropoff_lng": float(payload["dropoff_lng"]),
        "pickup_time": payload["pickup_time"],
        "dropoff_time": payload["dropoff_time"],
        "required_trailer_type": payload.get("required_trailer_type"),
        "required_vehicle_type": payload.get("required_vehicle_type", "TRUCK"),
    }

    result = supabase.table("loads").insert(row).execute()
    return jsonify(result.data[0]), 201
    row = {
        "id": load_id,
        "pickup_name": payload["pickup_name"],
        "pickup_address": payload["pickup_address"],
        "pickup_lat": float(payload["pickup_lat"]),
        "pickup_lng": float(payload["pickup_lng"]),
        "dropoff_name": payload["dropoff_name"],
        "dropoff_address": payload["dropoff_address"],
        "dropoff_lat": float(payload["dropoff_lat"]),
        "dropoff_lng": float(payload["dropoff_lng"]),
        "pickup_time": payload["pickup_time"],
        "dropoff_time": payload["dropoff_time"],
        "required_trailer_type": payload.get("required_trailer_type"),
        "required_vehicle_type": payload.get("required_vehicle_type", "TRUCK"),
    }

    result = supabase.table("loads").insert(row).execute()
    return jsonify(result.data[0]), 201


@app.get("/loads")
def list_loads():
    res = supabase.table("loads").select("*").execute()
    return jsonify(res.data)
    res = supabase.table("loads").select("*").execute()
    return jsonify(res.data)


@app.get("/loads/<load_id>")
def get_load(load_id: str):
    load = fetch_load(load_id)
    load = fetch_load(load_id)
    if not load:
        return jsonify({"error": "Load not found"}), 404
    return jsonify(asdict(load))


@app.get("/loads/<load_id>/recommendations")
def get_load_recommendations(load_id: str):
    load = fetch_load(load_id)
    load = fetch_load(load_id)
    if not load:
        return jsonify({"error": "Load not found"}), 404

    candidates = build_dispatch_candidates()
    ranked = [score_candidate(load, candidate) for candidate in candidates]
    ranked.sort(key=lambda x: (x["feasible"], x["score"]), reverse=True)

    return jsonify(ranked)


@app.get("/loads/<load_id>/recommendation/top")
def get_top_load_recommendation(load_id: str):
    load = fetch_load(load_id)
    load = fetch_load(load_id)
    if not load:
        return jsonify({"error": "Load not found"}), 404

    candidates = build_dispatch_candidates()
    ranked = [score_candidate(load, candidate) for candidate in candidates]
    ranked.sort(key=lambda x: (x["feasible"], x["score"]), reverse=True)

    if not ranked:
        return jsonify({"error": "No candidates found"}), 404

    return jsonify(ranked[0])


@app.get("/loads/<load_id>/recommendation/explain")
def explain_load_recommendation(load_id: str):
    load = fetch_load(load_id)
    if not load:
        return jsonify({"error": "Load not found"}), 404

    candidates = build_dispatch_candidates()
    ranked = [score_candidate(load, candidate) for candidate in candidates]
    ranked.sort(key=lambda x: (x["feasible"], x["score"]), reverse=True)

    if not ranked:
        return jsonify({"error": "No candidates found"}), 404

    # Get the top a few candidates to provide context for the AI
    top_candidates = ranked[:3]
    top_driver = top_candidates[0]

    # Construction of prompt
    prompt_lines = [
        f"We need to recommend the best driver for load #{load_id} going from '{load.pickup_address}' to '{load.dropoff_address}'.",
        "Our deterministic algorithm has ranked the feasible drivers based on specific weights (e.g., active vehicle, current status in-transit vs off-duty, performance mileage out-of-route, and vehicle matching constraints).",
        "Please provide a 3-4 sentence professional explanation for dispatchers. Focus on how the weights split, the trade-offs, and why the top driver is fundamentally better. For instance, explain why sticking with an in-transit driver facing slight traffic/delay is better than picking an off-duty operator or switching out an assigned vehicle."
    ]

    for idx, c in enumerate(top_candidates):
        rank = idx + 1
        d = c["driver_card"]
        prompt_lines.append(
            f"Rank {rank}: {c['driver_name']} (Score: {c['score']}). "
            f"Status: {d.get('status_label')}. "
            f"ETA: {d.get('eta_label')}. "
            f"Reasons for score: {', '.join(c['reasons'])}. "
            f"Warnings/Penalties: {', '.join(c['warnings'])}."
        )

    prompt = "\\n".join(prompt_lines)
    
    try:
        rationale = generate_text(prompt)
    except Exception as e:
        rationale = f"AI Generation failed: {str(e)}"

    return jsonify({
        "top_candidate": top_driver,
        "ai_rationale": rationale,
        "runner_ups": top_candidates[1:]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
    app.run(host="0.0.0.0", port=PORT, debug=True)