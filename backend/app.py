from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from flask import Flask, jsonify, request

app = Flask(__name__)


# ============================================================
# In-memory stores
# ============================================================

DRIVERS: Dict[int, "DriverProfile"] = {}
VEHICLES: Dict[int, "VehicleRecord"] = {}
PERFORMANCE: Dict[int, "DriverPerformance"] = {}
LOADS: Dict[str, "LoadRecord"] = {}


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
    assigned_driver_ids: List[int]


@dataclass
class DriverPerformance:
    driver_id: int
    oor_miles: float
    schedule_miles: float
    actual_miles: float
    schedule_time: int
    actual_time: int


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


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def epoch_ms_to_datetime(value: Optional[int]) -> Optional[datetime]:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def format_eta_label(delivery_date_ms: Optional[int]) -> Optional[str]:
    dt = epoch_ms_to_datetime(delivery_date_ms)
    if not dt:
        return None

    now = datetime.now(timezone.utc)
    local_dt = dt

    if local_dt.date() == now.date():
        return f"Today {local_dt.strftime('%H:%M')}"
    if (local_dt.date() - now.date()).days == 1:
        return f"Tomorrow {local_dt.strftime('%H:%M')}"
    return local_dt.strftime("%Y-%m-%d %H:%M UTC")


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

    # Vehicle alerts
    if vehicle is None:
        alerts.append({"severity": "high", "text": "No assigned vehicle found"})
    else:
        if vehicle.vehicle_status != "ACTIVE":
            alerts.append({"severity": "high", "text": f"Vehicle status is {vehicle.vehicle_status}"})

    # Driver operational alerts
    if driver.current_load_id is not None:
        alerts.append({"severity": "low", "text": "Driver currently assigned to an active load"})

    if driver.work_status in {"OFF_DUTY", "INACTIVE"}:
        alerts.append({"severity": "high", "text": f"Driver work status is {driver.work_status}"})

    # Performance alerts
    if perf is not None:
        oor_ratio = safe_ratio(perf.oor_miles, perf.schedule_miles)
        time_ratio = safe_ratio(float(perf.actual_time), float(perf.schedule_time))
        mile_ratio = safe_ratio(perf.actual_miles, perf.schedule_miles)

        if oor_ratio > 0.10:
            alerts.append({"severity": "high", "text": f"High out-of-route ratio: {oor_ratio:.1%}"})
        elif oor_ratio > 0.05:
            alerts.append({"severity": "medium", "text": f"Moderate out-of-route ratio: {oor_ratio:.1%}"})

        if time_ratio > 1.15:
            alerts.append({"severity": "medium", "text": f"Actual time exceeds schedule by {(time_ratio - 1) * 100:.1f}%"})

        if mile_ratio > 1.10:
            alerts.append({"severity": "medium", "text": f"Actual miles exceed scheduled miles by {(mile_ratio - 1) * 100:.1f}%"})
    else:
        alerts.append({"severity": "low", "text": "No driver performance record found"})

    return alerts


def build_vehicle_index_by_driver() -> Dict[int, VehicleRecord]:
    vehicle_by_driver: Dict[int, VehicleRecord] = {}
    for vehicle in VEHICLES.values():
        for driver_id in vehicle.assigned_driver_ids:
            vehicle_by_driver[driver_id] = vehicle
    return vehicle_by_driver


def build_dispatch_candidates() -> List[DispatchCandidate]:
    vehicle_by_driver = build_vehicle_index_by_driver()

    candidates: List[DispatchCandidate] = []
    for driver in DRIVERS.values():
        candidates.append(
            DispatchCandidate(
                driver=driver,
                vehicle=vehicle_by_driver.get(driver.driver_id),
                performance=PERFORMANCE.get(driver.driver_id),
            )
        )
    return candidates


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
        current_load_id=current_load.get("load_id"),
        current_load_show_id=current_load.get("load_show_id"),
        current_load_origin=current_load.get("origin"),
        current_load_destination=current_load.get("destination"),
        current_load_pickup_date=current_load.get("pickup_date"),
        current_load_delivery_date=current_load.get("delivery_date"),
    )


def normalize_vehicle(item: dict) -> VehicleRecord:
    assignments = item.get("assignments_drivers", {}) or {}
    driver_ids = assignments.get("driver_ids", []) or []

    if not driver_ids:
        driver_ids = [
            d.get("assign_driver_id")
            for d in assignments.get("assign_driver_info", [])
            if d.get("assign_driver_id") is not None
        ]

    driver_ids = [int(d) for d in driver_ids]

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
        assigned_driver_ids=driver_ids,
    )


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
# Frontend-ready driver card shape
# ============================================================

def build_driver_card(candidate: DispatchCandidate) -> dict:
    driver = candidate.driver
    vehicle = candidate.vehicle
    perf = candidate.performance

    progress_pct = estimate_progress_pct(
        driver.current_load_pickup_date,
        driver.current_load_delivery_date,
    )

    alerts = build_alerts(driver, vehicle, perf)

    card = {
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
        "hos_remaining_hours": None,
        "load_progress_pct": progress_pct,
        "eta_label": format_eta_label(driver.current_load_delivery_date),
        "fuel_pct": None,
        "alerts": alerts,
        "performance": {
            "oor_miles": perf.oor_miles,
            "schedule_miles": perf.schedule_miles,
            "actual_miles": perf.actual_miles,
            "schedule_time": perf.schedule_time,
            "actual_time": perf.actual_time,
        } if perf else None,
    }

    return card


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

    # Driver status / availability
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

    # Vehicle compatibility
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

    # Performance quality
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

    score = max(0.0, min(100.0, round(score, 2)))
    feasible = score >= 50

    return {
        "driver_id": driver.driver_id,
        "driver_name": driver.full_name,
        "vehicle_id": vehicle.vehicle_id if vehicle else None,
        "vehicle_no": vehicle.vehicle_no if vehicle else None,
        "score": score,
        "feasible": feasible,
        "reasons": reasons,
        "warnings": warnings,
        "driver_card": build_driver_card(candidate),
    }


# ============================================================
# Routes
# ============================================================

@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "drivers": len(DRIVERS),
        "vehicles": len(VEHICLES),
        "performance": len(PERFORMANCE),
        "loads": len(LOADS),
    })


@app.post("/ingest/drivers")
def ingest_drivers():
    payload = request.get_json(force=True)
    items = payload.get("data", [])

    for item in items:
        driver = normalize_driver(item)
        DRIVERS[driver.driver_id] = driver

    return jsonify({
        "success": True,
        "ingested_count": len(items),
        "total_drivers": len(DRIVERS),
    })


@app.post("/ingest/vehicles")
def ingest_vehicles():
    payload = request.get_json(force=True)
    items = payload.get("data", [])

    for item in items:
        vehicle = normalize_vehicle(item)
        VEHICLES[vehicle.vehicle_id] = vehicle

    return jsonify({
        "success": True,
        "ingested_count": len(items),
        "total_vehicles": len(VEHICLES),
    })


@app.post("/ingest/driver-performance")
def ingest_driver_performance():
    payload = request.get_json(force=True)
    items = payload.get("data", [])

    for item in items:
        perf = normalize_performance(item)
        PERFORMANCE[perf.driver_id] = perf

    return jsonify({
        "success": True,
        "ingested_count": len(items),
        "total_performance_records": len(PERFORMANCE),
    })


@app.get("/debug/drivers")
def debug_drivers():
    return jsonify([asdict(d) for d in DRIVERS.values()])


@app.get("/debug/vehicles")
def debug_vehicles():
    return jsonify([asdict(v) for v in VEHICLES.values()])


@app.get("/debug/performance")
def debug_performance():
    return jsonify([asdict(p) for p in PERFORMANCE.values()])


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
    load = LoadRecord(
        id=load_id,
        pickup_name=payload["pickup_name"],
        pickup_address=payload["pickup_address"],
        pickup_lat=float(payload["pickup_lat"]),
        pickup_lng=float(payload["pickup_lng"]),
        dropoff_name=payload["dropoff_name"],
        dropoff_address=payload["dropoff_address"],
        dropoff_lat=float(payload["dropoff_lat"]),
        dropoff_lng=float(payload["dropoff_lng"]),
        pickup_time=payload["pickup_time"],
        dropoff_time=payload["dropoff_time"],
        required_trailer_type=payload.get("required_trailer_type"),
        required_vehicle_type=payload.get("required_vehicle_type", "TRUCK"),
        created_at=now_iso(),
    )
    LOADS[load_id] = load

    return jsonify(asdict(load)), 201


@app.get("/loads")
def list_loads():
    return jsonify([asdict(load) for load in LOADS.values()])


@app.get("/loads/<load_id>")
def get_load(load_id: str):
    load = LOADS.get(load_id)
    if not load:
        return jsonify({"error": "Load not found"}), 404
    return jsonify(asdict(load))


@app.get("/loads/<load_id>/recommendations")
def get_load_recommendations(load_id: str):
    load = LOADS.get(load_id)
    if not load:
        return jsonify({"error": "Load not found"}), 404

    candidates = build_dispatch_candidates()
    ranked = [score_candidate(load, candidate) for candidate in candidates]
    ranked.sort(key=lambda x: (x["feasible"], x["score"]), reverse=True)

    return jsonify(ranked)


@app.get("/loads/<load_id>/recommendation/top")
def get_top_load_recommendation(load_id: str):
    load = LOADS.get(load_id)
    if not load:
        return jsonify({"error": "Load not found"}), 404

    candidates = build_dispatch_candidates()
    ranked = [score_candidate(load, candidate) for candidate in candidates]
    ranked.sort(key=lambda x: (x["feasible"], x["score"]), reverse=True)

    if not ranked:
        return jsonify({"error": "No candidates found"}), 404

    return jsonify(ranked[0])


# ============================================================
# Optional seed data for local testing
# ============================================================

def seed_demo_data():
    if DRIVERS:
        return

    driver_payload = {
        "data": [
            {
                "driver_id": 12154,
                "basic_info": {
                    "driver_first_name": "John",
                    "driver_last_name": "Doe",
                    "carrier": "Big Fleet Co.",
                    "work_status": "IN_TRANSIT",
                    "terminal": "Terminal A",
                    "driver_type": "OWNER_OPERATOR_OO",
                    "driver_phone_number": "111-222-3333",
                    "driver_email": "johndoe@driver.com",
                },
                "driver_location": {
                    "last_known_location": "S Martin L King Blvd, Las Vegas, NV",
                    "latest_update": 1681440338089,
                    "timezone": "PDT",
                },
                "loads": {
                    "driver_current_load": {
                        "load_id": 9964234,
                        "load_show_id": "10",
                        "origin": "Pueblo, CO",
                        "destination": "Los Angeles, CA",
                        "pickup_date": 1680310861000,
                        "delivery_date": 1981794989000,
                    }
                },
            },
            {
                "driver_id": 12155,
                "basic_info": {
                    "driver_first_name": "Sara",
                    "driver_last_name": "Lee",
                    "carrier": "Big Fleet Co.",
                    "work_status": "AVAILABLE",
                    "terminal": "Terminal B",
                    "driver_type": "COMPANY_DRIVER",
                    "driver_phone_number": "222-333-4444",
                    "driver_email": "saralee@driver.com",
                },
                "driver_location": {
                    "last_known_location": "Phoenix, AZ",
                    "latest_update": 1681440338089,
                    "timezone": "MST",
                },
                "loads": {},
            },
        ]
    }

    vehicle_payload = {
        "data": [
            {
                "created_date": "Apr 14, 2023",
                "vehicle_id": 840215,
                "owner_id": 49845,
                "owner_name": "Operator A",
                "vehicle_status": "ACTIVE",
                "vehicle_no": "TRK-201",
                "vehicle_type": "TRUCK",
                "vehicle_vin": "1HGCM82633A123456",
                "gross_vehicle_weight": 3500,
                "trailer_type": "VAN",
                "vehicle_make": "Freightliner",
                "vehicle_model": "Cascadia",
                "assignments_drivers": {
                    "driver_ids": [12154],
                    "assign_driver_info": [
                        {
                            "assign_driver_id": 12154,
                            "assign_driver_name": "John Doe",
                        }
                    ],
                },
            },
            {
                "created_date": "Apr 15, 2023",
                "vehicle_id": 840216,
                "owner_id": 49845,
                "owner_name": "Operator A",
                "vehicle_status": "ACTIVE",
                "vehicle_no": "TRK-202",
                "vehicle_type": "TRUCK",
                "vehicle_vin": "1HGCM82633A123457",
                "gross_vehicle_weight": 3500,
                "trailer_type": "VAN",
                "vehicle_make": "Peterbilt",
                "vehicle_model": "579",
                "assignments_drivers": {
                    "driver_ids": [12155],
                    "assign_driver_info": [
                        {
                            "assign_driver_id": 12155,
                            "assign_driver_name": "Sara Lee",
                        }
                    ],
                },
            },
        ]
    }

    performance_payload = {
        "data": [
            {
                "driver_id": 12154,
                "oor_miles": 12.5,
                "schedule_miles": 500,
                "actual_miles": 512.5,
                "schedule_time": 480,
                "actual_time": 495,
            },
            {
                "driver_id": 12155,
                "oor_miles": 3.0,
                "schedule_miles": 450,
                "actual_miles": 452.0,
                "schedule_time": 470,
                "actual_time": 468,
            },
        ]
    }

    for item in driver_payload["data"]:
        driver = normalize_driver(item)
        DRIVERS[driver.driver_id] = driver

    for item in vehicle_payload["data"]:
        vehicle = normalize_vehicle(item)
        VEHICLES[vehicle.vehicle_id] = vehicle

    for item in performance_payload["data"]:
        perf = normalize_performance(item)
        PERFORMANCE[perf.driver_id] = perf


seed_demo_data()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)