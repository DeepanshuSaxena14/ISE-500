-- ================================================================
-- DispatchIQ — PostgreSQL Schema v2
-- Aligned with: DriverProfile, VehicleRecord, DriverPerformance,
--               LoadRecord (app.py)
--
-- Run entirely in Supabase SQL Editor (fresh install only).
-- Click "Run without RLS" on every prompt.
-- ================================================================

-- Enable pgvector (required for load_embeddings RAG table)
CREATE EXTENSION IF NOT EXISTS vector;


-- ================================================================
-- 1. DRIVERS
--    Source: DriverProfile in app.py
-- ================================================================
CREATE TABLE drivers (

    -- Internal identity
    id                          TEXT PRIMARY KEY,       -- e.g. "D-001"
    driver_id_external          INTEGER UNIQUE,         -- NavPro integer driver_id

    -- Personal info
    first_name                  TEXT,
    last_name                   TEXT,
    name                        TEXT,                   -- full_name (first + last)
    email                       TEXT,
    phone                       TEXT,

    -- Classification
    carrier                     TEXT,
    terminal                    TEXT,
    driver_type                 TEXT,                   -- e.g. OWNER_OPERATOR_OO, COMPANY_DRIVER
    license_number              TEXT,
    license_state               TEXT,
    cdl_class                   TEXT DEFAULT 'A',

    -- Status
    work_status                 TEXT,                   -- raw NavPro: IN_TRANSIT, AVAILABLE, OFF_DUTY, etc.
    status                      TEXT NOT NULL DEFAULT 'available'
                                    CHECK (status IN (
                                        'available', 'en_route', 'on_break', 'off_duty', 'maintenance'
                                    )),

    -- Location
    current_lat                 NUMERIC(9,6),
    current_lng                 NUMERIC(9,6),
    last_known_location         TEXT,                   -- human-readable string from NavPro
    latest_update               BIGINT,                 -- epoch ms of last GPS ping
    timezone                    TEXT,                   -- e.g. "PDT", "MST"

    -- HOS & telemetry (DispatchIQ-specific, fed by ELD/mock)
    hours_remaining             NUMERIC(4,1) NOT NULL DEFAULT 11.0,
    hos_reset_at                TIMESTAMPTZ,
    fuel_pct                    INTEGER DEFAULT 100 CHECK (fuel_pct BETWEEN 0 AND 100),
    cpm                         NUMERIC(5,2),           -- cost per mile
    on_time_rate                NUMERIC(4,1),           -- % on-time deliveries

    -- Current load (denormalized for fast reads — mirrors app.py DriverProfile fields)
    current_load_id             TEXT,                   -- FK added after loads table below
    current_load_show_id        TEXT,                   -- human-readable load number
    current_load_origin         TEXT,
    current_load_destination    TEXT,
    current_load_pickup_date    BIGINT,                 -- epoch ms
    current_load_delivery_date  BIGINT,                 -- epoch ms

    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ DEFAULT NOW()
);


-- ================================================================
-- 2. LOADS
--    Source: LoadRecord in app.py
-- ================================================================
CREATE TABLE loads (

    id                      TEXT PRIMARY KEY,           -- e.g. "LD-4821"

    -- Pickup
    pickup_name             TEXT,                       -- facility / shipper name
    pickup_address          TEXT,                       -- full address string
    origin_city             TEXT,                       -- city (UI display)
    origin_state            TEXT,
    origin_lat              NUMERIC(9,6),               -- app.py: pickup_lat
    origin_lng              NUMERIC(9,6),               -- app.py: pickup_lng
    pickup_eta              TIMESTAMPTZ,                -- app.py: pickup_time

    -- Dropoff
    dropoff_name            TEXT,                       -- facility / receiver name
    dropoff_address         TEXT,                       -- full address string
    dest_city               TEXT,
    dest_state              TEXT,
    dest_lat                NUMERIC(9,6),               -- app.py: dropoff_lat
    dest_lng                NUMERIC(9,6),               -- app.py: dropoff_lng
    delivery_eta            TIMESTAMPTZ,                -- app.py: dropoff_time
    actual_delivery         TIMESTAMPTZ,

    -- Vehicle requirements (used by score_candidate in app.py)
    required_trailer_type   TEXT,                       -- app.py: required_trailer_type
    required_vehicle_type   TEXT DEFAULT 'TRUCK',       -- app.py: required_vehicle_type

    -- Load details
    distance_miles          NUMERIC(7,1),
    commodity               TEXT,
    weight_lbs              INTEGER,
    rate_usd                NUMERIC(8,2),
    progress_pct            INTEGER DEFAULT 0 CHECK (progress_pct BETWEEN 0 AND 100),

    -- Status & assignment
    status                  TEXT NOT NULL DEFAULT 'pending'
                                CHECK (status IN (
                                    'pending', 'assigned', 'en_route', 'delivered', 'cancelled'
                                )),
    driver_id               TEXT REFERENCES drivers(id),

    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Circular FK: drivers.current_load_id → loads.id
-- Must be added after both tables exist
ALTER TABLE drivers
    ADD CONSTRAINT fk_driver_current_load
    FOREIGN KEY (current_load_id) REFERENCES loads(id);


-- ================================================================
-- 3. VEHICLES
--    Source: VehicleRecord in app.py
-- ================================================================
CREATE TABLE vehicles (
    id                      INTEGER PRIMARY KEY,        -- app.py: vehicle_id
    owner_id                INTEGER,
    owner_name              TEXT,
    vehicle_status          TEXT,                       -- e.g. ACTIVE, INACTIVE
    vehicle_no              TEXT,                       -- e.g. "TRK-201"
    vehicle_type            TEXT,                       -- e.g. "TRUCK"
    vehicle_vin             TEXT,
    gross_vehicle_weight    INTEGER,
    trailer_type            TEXT,                       -- e.g. "VAN", "FLATBED", "REEFER"
    vehicle_make            TEXT,
    vehicle_model           TEXT,
    created_date            TEXT,                       -- date string as returned by NavPro
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);


-- ================================================================
-- 4. VEHICLE ↔ DRIVER ASSIGNMENTS
--    Source: VehicleRecord.assigned_driver_ids in app.py
--    Many-to-many join table
-- ================================================================
CREATE TABLE vehicle_driver_assignments (
    vehicle_id              INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    driver_id_external      INTEGER NOT NULL,           -- matches drivers.driver_id_external
    assigned_at             TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (vehicle_id, driver_id_external)
);

CREATE INDEX idx_vda_driver ON vehicle_driver_assignments (driver_id_external);


-- ================================================================
-- 5. DRIVER PERFORMANCE
--    Source: DriverPerformance in app.py
--    Powers score_candidate() scoring logic
-- ================================================================
CREATE TABLE driver_performance (
    driver_id_external      INTEGER PRIMARY KEY
                                REFERENCES drivers(driver_id_external),
    oor_miles               NUMERIC(10,2) DEFAULT 0,   -- out-of-route miles
    schedule_miles          NUMERIC(10,2) DEFAULT 0,
    actual_miles            NUMERIC(10,2) DEFAULT 0,
    schedule_time           INTEGER DEFAULT 0,          -- minutes
    actual_time             INTEGER DEFAULT 0,          -- minutes
    recorded_at             TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);


-- ================================================================
-- 6. ROUTES
-- ================================================================
CREATE TABLE routes (
    id          SERIAL PRIMARY KEY,
    load_id     TEXT NOT NULL REFERENCES loads(id) ON DELETE CASCADE,
    driver_id   TEXT REFERENCES drivers(id),
    waypoints   JSONB,                                  -- [{lat, lng, name, eta}]
    polyline    TEXT,                                   -- encoded polyline or GeoJSON string
    total_miles NUMERIC(7,1),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);


-- ================================================================
-- 7. GPS EVENTS
-- ================================================================
CREATE TABLE gps_events (
    id          BIGSERIAL PRIMARY KEY,
    driver_id   TEXT NOT NULL REFERENCES drivers(id),
    load_id     TEXT REFERENCES loads(id),
    lat         NUMERIC(9,6) NOT NULL,
    lng         NUMERIC(9,6) NOT NULL,
    speed_mph   NUMERIC(5,1),
    heading_deg INTEGER,
    event_type  TEXT DEFAULT 'position'
                    CHECK (event_type IN (
                        'position', 'geofence_enter', 'geofence_exit',
                        'stop', 'idle', 'hard_brake'
                    )),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gps_driver_time ON gps_events (driver_id, recorded_at DESC);
CREATE INDEX idx_gps_load        ON gps_events (load_id,   recorded_at DESC);


-- ================================================================
-- 8. ALERTS
-- ================================================================
CREATE TABLE alerts (
    id          BIGSERIAL PRIMARY KEY,
    driver_id   TEXT REFERENCES drivers(id),
    load_id     TEXT REFERENCES loads(id),
    alert_type  TEXT NOT NULL
                    CHECK (alert_type IN (
                        'hos_warning', 'hos_critical',
                        'fuel_low', 'fuel_critical',
                        'delay', 'weather',
                        'geofence', 'hard_brake',
                        'cost_overrun', 'compliance'
                    )),
    severity    TEXT NOT NULL DEFAULT 'warning'
                    CHECK (severity IN ('info', 'warning', 'critical')),
    title       TEXT NOT NULL,
    description TEXT,
    is_read     BOOLEAN DEFAULT FALSE,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_unread ON alerts (is_read, created_at DESC) WHERE NOT is_read;
CREATE INDEX idx_alerts_driver  ON alerts (driver_id, created_at DESC);


-- ================================================================
-- 9. COSTS
-- ================================================================
CREATE TABLE costs (
    id              BIGSERIAL PRIMARY KEY,
    load_id         TEXT REFERENCES loads(id),
    driver_id       TEXT REFERENCES drivers(id),
    cost_type       TEXT NOT NULL
                        CHECK (cost_type IN (
                            'fuel', 'driver_pay', 'maintenance',
                            'tolls', 'detention', 'other'
                        )),
    amount_usd      NUMERIC(10,2) NOT NULL,
    miles_driven    NUMERIC(7,1),
    fuel_gallons    NUMERIC(6,2),
    fuel_price_gal  NUMERIC(4,3),
    notes           TEXT,
    incurred_at     TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_costs_load   ON costs (load_id);
CREATE INDEX idx_costs_driver ON costs (driver_id);


-- ================================================================
-- 10. BRIEFINGS
-- ================================================================
CREATE TABLE briefings (
    id              BIGSERIAL PRIMARY KEY,
    fleet_snapshot  JSONB,
    summary_text    TEXT NOT NULL,
    voice_audio_url TEXT,
    critical_alerts JSONB,
    generated_by    TEXT DEFAULT 'claude-sonnet-4',
    generated_at    TIMESTAMPTZ DEFAULT NOW()
);


-- ================================================================
-- 11. LOAD EMBEDDINGS  (RAG / pgvector)
-- ================================================================
CREATE TABLE load_embeddings (
    id          BIGSERIAL PRIMARY KEY,
    load_id     TEXT REFERENCES loads(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    embedding   vector(1536),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_load_embeddings_vec
    ON load_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 50);


-- ================================================================
-- TRIGGERS — keep updated_at current automatically
-- ================================================================
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_drivers_updated
    BEFORE UPDATE ON drivers
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_loads_updated
    BEFORE UPDATE ON loads
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_vehicles_updated
    BEFORE UPDATE ON vehicles
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_performance_updated
    BEFORE UPDATE ON driver_performance
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();