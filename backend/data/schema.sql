-- ============================================================
-- DispatchIQ backend schema
-- Matches app.py + backend-compatible mock_data.py
-- PostgreSQL
-- ============================================================

begin;

-- ------------------------------------------------------------
-- Drivers
-- ------------------------------------------------------------
create table if not exists drivers (
    driver_id bigint primary key,
    first_name text,
    last_name text,
    full_name text,
    carrier text,
    work_status text,
    terminal text,
    driver_type text,
    phone text,
    email text,
    last_known_location text,
    latest_update bigint,
    timezone text,

    current_load_id text,
    current_load_show_id text,
    current_load_origin text,
    current_load_destination text,
    current_load_pickup_date bigint,
    current_load_delivery_date bigint,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_drivers_work_status
    on drivers(work_status);

create index if not exists idx_drivers_terminal
    on drivers(terminal);

create index if not exists idx_drivers_current_load_id
    on drivers(current_load_id);


-- ------------------------------------------------------------
-- Vehicles
-- ------------------------------------------------------------
create table if not exists vehicles (
    vehicle_id bigint primary key,
    owner_id bigint,
    owner_name text,
    vehicle_status text,
    vehicle_no text,
    vehicle_type text,
    vehicle_vin text,
    gross_vehicle_weight integer,
    trailer_type text,
    vehicle_make text,
    vehicle_model text,
    created_date text,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists idx_vehicles_vehicle_no
    on vehicles(vehicle_no);

create index if not exists idx_vehicles_vehicle_status
    on vehicles(vehicle_status);

create index if not exists idx_vehicles_vehicle_type
    on vehicles(vehicle_type);

create index if not exists idx_vehicles_trailer_type
    on vehicles(trailer_type);


-- ------------------------------------------------------------
-- Driver <-> Vehicle assignment
-- Your app currently stores assigned_driver_ids on vehicle records.
-- In SQL, use a join table.
-- ------------------------------------------------------------
create table if not exists vehicle_driver_assignments (
    vehicle_id bigint not null references vehicles(vehicle_id) on delete cascade,
    driver_id bigint not null references drivers(driver_id) on delete cascade,
    assigned_at timestamptz not null default now(),
    primary key (vehicle_id, driver_id)
);

create index if not exists idx_vehicle_driver_assignments_driver_id
    on vehicle_driver_assignments(driver_id);


-- ------------------------------------------------------------
-- Driver performance
-- One current record per driver, matching PERFORMANCE dict in app.py
-- ------------------------------------------------------------
create table if not exists driver_performance (
    driver_id bigint primary key references drivers(driver_id) on delete cascade,
    oor_miles numeric(10,2) not null default 0,
    schedule_miles numeric(10,2) not null default 0,
    actual_miles numeric(10,2) not null default 0,
    schedule_time integer not null default 0,
    actual_time integer not null default 0,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


-- ------------------------------------------------------------
-- Loads
-- Matches LoadRecord in app.py
-- ------------------------------------------------------------
create table if not exists loads (
    id uuid primary key,
    pickup_name text not null,
    pickup_address text not null,
    pickup_lat numeric(9,6) not null,
    pickup_lng numeric(9,6) not null,
    dropoff_name text not null,
    dropoff_address text not null,
    dropoff_lat numeric(9,6) not null,
    dropoff_lng numeric(9,6) not null,
    pickup_time timestamptz not null,
    dropoff_time timestamptz not null,
    required_trailer_type text,
    required_vehicle_type text not null default 'TRUCK',
    created_at timestamptz not null default now()
);

create index if not exists idx_loads_pickup_time
    on loads(pickup_time);

create index if not exists idx_loads_dropoff_time
    on loads(dropoff_time);

create index if not exists idx_loads_required_vehicle_type
    on loads(required_vehicle_type);

create index if not exists idx_loads_required_trailer_type
    on loads(required_trailer_type);


-- ------------------------------------------------------------
-- Optional: persisted recommendations
-- Useful if you want to cache recommendation output
-- Not required by current app.py, but useful for growth.
-- ------------------------------------------------------------
create table if not exists load_recommendations (
    id bigserial primary key,
    load_id uuid not null references loads(id) on delete cascade,
    driver_id bigint not null references drivers(driver_id) on delete cascade,
    vehicle_id bigint references vehicles(vehicle_id) on delete set null,
    vehicle_no text,
    score numeric(6,2) not null,
    feasible boolean not null,
    reasons jsonb not null default '[]'::jsonb,
    warnings jsonb not null default '[]'::jsonb,
    driver_card jsonb not null,
    generated_at timestamptz not null default now()
);

create index if not exists idx_load_recommendations_load_id
    on load_recommendations(load_id);

create index if not exists idx_load_recommendations_driver_id
    on load_recommendations(driver_id);

create index if not exists idx_load_recommendations_feasible_score
    on load_recommendations(load_id, feasible desc, score desc);


-- ------------------------------------------------------------
-- Optional raw ingestion audit tables
-- These store upstream payloads exactly as received.
-- Useful for debugging / replay / observability.
-- ------------------------------------------------------------
create table if not exists ingest_driver_batches (
    id bigserial primary key,
    payload jsonb not null,
    received_at timestamptz not null default now()
);

create table if not exists ingest_vehicle_batches (
    id bigserial primary key,
    payload jsonb not null,
    received_at timestamptz not null default now()
);

create table if not exists ingest_driver_performance_batches (
    id bigserial primary key,
    payload jsonb not null,
    received_at timestamptz not null default now()
);


-- ------------------------------------------------------------
-- Optional trigger to auto-maintain updated_at
-- ------------------------------------------------------------
create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_drivers_set_updated_at on drivers;
create trigger trg_drivers_set_updated_at
before update on drivers
for each row
execute function set_updated_at();

drop trigger if exists trg_vehicles_set_updated_at on vehicles;
create trigger trg_vehicles_set_updated_at
before update on vehicles
for each row
execute function set_updated_at();

drop trigger if exists trg_driver_performance_set_updated_at on driver_performance;
create trigger trg_driver_performance_set_updated_at
before update on driver_performance
for each row
execute function set_updated_at();

commit;