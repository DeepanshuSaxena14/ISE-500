import { useState, useEffect, useRef } from "react";
import { fleetService } from "../api";

// ─── DATA ───────────────────────────────────────────────────────────────────

const DRIVERS_RAW = [
  {
    id: "D-001", name: "Marcus Rivera", avatar: "MR", truckId: "TRK-114",
    location: "I-10 E, near Lordsburg NM", lat: 32.35, lng: -108.71,
    status: "En Route", hosRemaining: 9.5, hosDriven: 1.5,
    load: { id: "LD-4821", origin: "Phoenix AZ", dest: "Dallas TX", progress: 34 },
    eta: "Tomorrow 07:42", etaStatus: "on_time",
    speed: 67, fuelLevel: 71, odometer: 312441,
    onTimeRate: 96, rating: 4.8,
    alerts: [],
  },
  {
    id: "D-002", name: "Sandra Kim", avatar: "SK", truckId: "TRK-089",
    location: "Tempe, AZ — Truck Stop", lat: 33.42, lng: -111.93,
    status: "On Break", hosRemaining: 7.2, hosDriven: 3.8,
    load: { id: "LD-4798", origin: "LA CA", dest: "Albuquerque NM", progress: 0 },
    eta: "Pending dispatch", etaStatus: "pending",
    speed: 0, fuelLevel: 52, odometer: 287012,
    onTimeRate: 98, rating: 4.9,
    alerts: [{ type: "info", msg: "Break ends in 22 min" }],
  },
  {
    id: "D-003", name: "James Okafor", avatar: "JO", truckId: "TRK-201",
    location: "US-60 W, near Globe AZ", lat: 33.39, lng: -110.78,
    status: "En Route", hosRemaining: 2.1, hosDriven: 8.9,
    load: { id: "LD-4809", origin: "Albuquerque NM", dest: "Phoenix AZ", progress: 71 },
    eta: "Today 18:30", etaStatus: "at_risk",
    speed: 58, fuelLevel: 29, odometer: 198334,
    onTimeRate: 88, rating: 4.5,
    alerts: [
      { type: "critical", msg: "HOS critical — 2.1h remaining" },
      { type: "warning", msg: "Fuel below 30% — nearest stop 14mi" },
    ],
  },
  {
    id: "D-004", name: "Tanya Reyes", avatar: "TR", truckId: "TRK-177",
    location: "Tucson, AZ — Delivered", lat: 32.22, lng: -110.97,
    status: "Available", hosRemaining: 10.0, hosDriven: 1.0,
    load: null,
    eta: "—", etaStatus: "available",
    speed: 0, fuelLevel: 91, odometer: 254188,
    onTimeRate: 93, rating: 4.7,
    alerts: [],
  },
  {
    id: "D-005", name: "Devon Carter", avatar: "DC", truckId: "TRK-033",
    location: "I-40 W, near Gallup NM", lat: 35.52, lng: -108.74,
    status: "En Route", hosRemaining: 5.5, hosDriven: 5.5,
    load: { id: "LD-4815", origin: "Albuquerque NM", dest: "Flagstaff AZ", progress: 55 },
    eta: "Today 21:15", etaStatus: "delayed",
    speed: 62, fuelLevel: 48, odometer: 441009,
    onTimeRate: 81, rating: 4.3,
    alerts: [
      { type: "critical", msg: "Running 47 min behind schedule" },
      { type: "warning", msg: "Weather: wind advisory on I-40" },
    ],
  },
  {
    id: "D-006", name: "Priya Nair", avatar: "PN", truckId: "TRK-158",
    location: "Phoenix, AZ — Yard", lat: 33.44, lng: -112.07,
    status: "Off Duty", hosRemaining: 0, hosDriven: 11.0,
    load: null,
    eta: "—", etaStatus: "off_duty",
    speed: 0, fuelLevel: 64, odometer: 178902,
    onTimeRate: 95, rating: 4.6,
    alerts: [{ type: "info", msg: "34h reset — available tomorrow 09:00" }],
  },
  {
    id: "D-007", name: "Luis Mendoza", avatar: "LM", truckId: "TRK-092",
    location: "I-17 N, near Camp Verde AZ", lat: 34.55, lng: -111.85,
    status: "En Route", hosRemaining: 6.8, hosDriven: 4.2,
    load: { id: "LD-4822", origin: "Phoenix AZ", dest: "Flagstaff AZ", progress: 62 },
    eta: "Today 16:50", etaStatus: "on_time",
    speed: 71, fuelLevel: 83, odometer: 321770,
    onTimeRate: 92, rating: 4.7,
    alerts: [],
  },
  {
    id: "D-008", name: "Rachel Stone", avatar: "RS", truckId: "TRK-245",
    location: "US-93 N, near Wikieup AZ", lat: 34.70, lng: -113.60,
    status: "En Route", hosRemaining: 8.3, hosDriven: 2.7,
    load: { id: "LD-4817", origin: "Phoenix AZ", dest: "Las Vegas NV", progress: 28 },
    eta: "Today 20:10", etaStatus: "on_time",
    speed: 65, fuelLevel: 77, odometer: 209811,
    onTimeRate: 94, rating: 4.8,
    alerts: [],
  },
];

// ─── CONSTANTS ───────────────────────────────────────────────────────────────

const STATUS_META = {
  "En Route":  { color: "#34d399", bg: "rgba(52,211,153,.12)",  dot: "#34d399" },
  "On Break":  { color: "#fbbf24", bg: "rgba(251,191,36,.12)",  dot: "#fbbf24" },
  "Available": { color: "#60a5fa", bg: "rgba(96,165,250,.12)",  dot: "#60a5fa" },
  "Off Duty":  { color: "#6b7280", bg: "rgba(107,114,128,.12)", dot: "#6b7280" },
};

const ETA_META = {
  on_time:   { label: "On Time",  color: "#34d399" },
  at_risk:   { label: "At Risk",  color: "#fbbf24" },
  delayed:   { label: "Delayed",  color: "#f87171" },
  pending:   { label: "Pending",  color: "#94a3b8" },
  available: { label: "Available",color: "#60a5fa" },
  off_duty:  { label: "Off Duty", color: "#6b7280" },
};

const ALERT_META = {
  critical: { color: "#f87171", bg: "rgba(248,113,113,.12)", icon: "⚠" },
  warning:  { color: "#fbbf24", bg: "rgba(251,191,36,.10)",  icon: "⚡" },
  info:     { color: "#60a5fa", bg: "rgba(96,165,250,.10)",  icon: "ℹ" },
};

// ─── SUBCOMPONENTS ───────────────────────────────────────────────────────────

function HOSBar({ remaining, driven }) {
  const total = 11;
  const pctRemaining = Math.max(0, Math.min(100, (remaining / total) * 100));
  const color = remaining <= 2 ? "#f87171" : remaining <= 4 ? "#fbbf24" : "#34d399";
  return (
    <div style={{ width: "100%" }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: "rgba(255,255,255,.35)", marginBottom: 3 }}>
        <span style={{ color }}>{remaining.toFixed(1)}h left</span>
        <span>{driven.toFixed(1)}h driven</span>
      </div>
      <div style={{ width: "100%", height: 4, background: "rgba(255,255,255,.08)", borderRadius: 2, overflow: "hidden" }}>
        <div style={{ width: pctRemaining + "%", height: "100%", background: color, borderRadius: 2, transition: "width .6s ease" }} />
      </div>
    </div>
  );
}

function ProgressBar({ pct }) {
  return (
    <div style={{ width: "100%" }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: "rgba(255,255,255,.35)", marginBottom: 3 }}>
        <span>Progress</span>
        <span style={{ color: "rgba(255,255,255,.6)" }}>{pct}%</span>
      </div>
      <div style={{ width: "100%", height: 4, background: "rgba(255,255,255,.08)", borderRadius: 2, overflow: "hidden" }}>
        <div style={{ width: pct + "%", height: "100%", background: "rgba(96,165,250,.7)", borderRadius: 2, transition: "width .6s ease" }} />
      </div>
    </div>
  );
}

function FuelDot({ level }) {
  const color = level < 30 ? "#f87171" : level < 50 ? "#fbbf24" : "#34d399";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
      <svg width="10" height="12" viewBox="0 0 10 12" fill="none">
        <rect x="1" y="2" width="6" height="9" rx="1" stroke={color} strokeWidth="1" fill="none" opacity=".6"/>
        <rect x="2" y={2 + (9 * (1 - level / 100))} width="4" height={9 * (level / 100)} rx=".5" fill={color} opacity=".7"/>
        <path d="M7 4h1.5a.5.5 0 01.5.5v2a.5.5 0 01-.5.5H7" stroke={color} strokeWidth=".8" fill="none" opacity=".5"/>
      </svg>
      <span style={{ fontSize: 11, color, fontWeight: 600 }}>{level}%</span>
    </div>
  );
}

function AlertBadge({ alerts }) {
  if (!alerts.length) return <span style={{ fontSize: 10, color: "rgba(255,255,255,.2)" }}>—</span>;
  const top = alerts[0];
  const m = ALERT_META[top.type];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
      {alerts.map((a, i) => {
        const am = ALERT_META[a.type];
        return (
          <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 4, background: am.bg, border: `0.5px solid ${am.color}33`, borderRadius: 5, padding: "3px 6px", maxWidth: 220 }}>
            <span style={{ fontSize: 9, color: am.color, flexShrink: 0, marginTop: 1 }}>{am.icon}</span>
            <span style={{ fontSize: 9, color: am.color, lineHeight: 1.4 }}>{a.msg}</span>
          </div>
        );
      })}
    </div>
  );
}

function StatCard({ label, value, sub, color }) {
  return (
    <div style={{ background: "rgba(255,255,255,.03)", border: "0.5px solid rgba(255,255,255,.08)", borderRadius: 10, padding: "12px 14px" }}>
      <div style={{ fontSize: 9, color: "rgba(255,255,255,.3)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color: color || "#f1f5f9", lineHeight: 1, letterSpacing: "-0.02em" }}>{value}</div>
      {sub && <div style={{ fontSize: 10, color: "rgba(255,255,255,.35)", marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

// ─── MAIN COMPONENT ──────────────────────────────────────────────────────────

export default function FleetDashboard() {
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);
  const [filter, setFilter] = useState("all");
  const [sortKey, setSortKey] = useState("alerts");
  const [sortDir, setSortDir] = useState("desc");
  const [search, setSearch] = useState("");
  const [tick, setTick] = useState(0);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const fetchDrivers = async () => {
    try {
      const data = await fleetService.getDrivers();
      // Map backend shape to frontend shape
      const mapped = data.map(d => ({
        id: d.driver_id,
        name: d.name || 'Unknown Driver',
        avatar: d.name ? d.name.split(' ').map(n => n[0]).join('') : '??',
        truckId: d.vehicle_no || 'N/A',
        location: d.location_label || 'Unknown',
        status: d.status_label || 'Offline',
        hosRemaining: d.performance ? (d.performance.schedule_time / 60) : 10.0,
        hosDriven: d.performance ? (d.performance.actual_time / 60) : 1.0,
        load: d.current_load ? {
          id: d.current_load.load_show_id || d.current_load.load_id,
          origin: d.current_load.origin,
          dest: d.current_load.destination,
          progress: d.load_progress_pct || 0
        } : null,
        eta: d.eta_label || '—',
        etaStatus: d.load_progress_pct > 90 ? 'on_time' : 'pending',
        speed: d.status_label === 'Driving' ? 65 : 0,
        fuelLevel: d.fuel_pct || 75,
        odometer: 250000,
        onTimeRate: 95,
        rating: 4.5,
        alerts: (d.alerts || []).map(a => ({
          type: a.severity === 'high' ? 'critical' : a.severity === 'medium' ? 'warning' : 'info',
          msg: a.text
        }))
      }));
      setDrivers(mapped);
    } catch (error) {
      console.error("Failed to fetch drivers:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDrivers();
  }, []);

  // Simulate live GPS + speed updates every 8s
  useEffect(() => {
    const iv = setInterval(() => {
      setDrivers(prev => prev.map(d => {
        if (d.status !== "En Route") return d;
        const speedJitter = (Math.random() - 0.5) * 4;
        const newSpeed = Math.max(45, Math.min(75, d.speed + speedJitter));
        const newProgress = d.load ? Math.min(99, d.load.progress + (Math.random() > 0.6 ? 1 : 0)) : 0;
        const newHos = Math.max(0, d.hosRemaining - 8 / 3600);
        return {
          ...d,
          speed: Math.round(newSpeed),
          hosRemaining: parseFloat(newHos.toFixed(2)),
          hosDriven: parseFloat((d.hosDriven + 8 / 3600).toFixed(2)),
          load: d.load ? { ...d.load, progress: newProgress } : null,
        };
      }));
      setLastUpdate(new Date());
      setTick(t => t + 1);
    }, 8000);
    return () => clearInterval(iv);
  }, []);

  // Derived
  const alertCount = drivers.reduce((n, d) => n + d.alerts.filter(a => a.type === "critical").length, 0);
  const enRouteCount = drivers.filter(d => d.status === "En Route").length;
  const availableCount = drivers.filter(d => d.status === "Available").length;
  const delayedCount = drivers.filter(d => d.etaStatus === "delayed" || d.etaStatus === "at_risk").length;

  // Filter + sort
  const filtered = drivers
    .filter(d => {
      if (filter === "alerts") return d.alerts.length > 0;
      if (filter === "delayed") return d.etaStatus === "delayed" || d.etaStatus === "at_risk";
      if (filter === "available") return d.status === "Available";
      if (filter === "enroute") return d.status === "En Route";
      return true;
    })
    .filter(d => {
      if (!search) return true;
      const q = search.toLowerCase();
      return d.name.toLowerCase().includes(q) || d.truckId.toLowerCase().includes(q) || d.location.toLowerCase().includes(q) || (d.load?.id || "").toLowerCase().includes(q);
    })
    .sort((a, b) => {
      let va, vb;
      if (sortKey === "alerts") { va = a.alerts.filter(x => x.type === "critical").length; vb = b.alerts.filter(x => x.type === "critical").length; }
      else if (sortKey === "hos") { va = a.hosRemaining; vb = b.hosRemaining; }
      else if (sortKey === "name") { va = a.name; vb = b.name; return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va); }
      else if (sortKey === "status") { va = a.status; vb = b.status; return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va); }
      else { va = a.hosRemaining; vb = b.hosRemaining; }
      return sortDir === "asc" ? va - vb : vb - va;
    });

  const selectedDriver = drivers.find(d => d.id === selectedId);

  function toggleSort(key) {
    if (sortKey === key) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortKey(key); setSortDir("desc"); }
  }

  const ColHeader = ({ label, k, style }) => (
    <th onClick={() => toggleSort(k)} style={{ padding: "10px 12px", textAlign: "left", fontSize: 9, fontWeight: 600, color: sortKey === k ? "#34d399" : "rgba(255,255,255,.3)", textTransform: "uppercase", letterSpacing: "0.08em", cursor: "pointer", userSelect: "none", whiteSpace: "nowrap", ...style }}>
      {label} {sortKey === k ? (sortDir === "asc" ? "↑" : "↓") : ""}
    </th>
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold tracking-tight">Fleet Overview</h2>
        <div className="flex items-center gap-2 text-[11px] text-brand-muted">
          <div className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-pulse" />
          {drivers.length} Units Online
        </div>
      </div>

      <div>

        {/* ── STAT CARDS ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 16 }}>
          <StatCard label="En Route" value={enRouteCount} sub={`of ${drivers.length} total drivers`} color="#34d399" />
          <StatCard label="Available" value={availableCount} sub="ready for dispatch" color="#60a5fa" />
          <StatCard label="Delayed / At Risk" value={delayedCount} sub="need attention" color={delayedCount > 0 ? "#f87171" : "#6b7280"} />
          <StatCard label="Critical Alerts" value={alertCount} sub="require action" color={alertCount > 0 ? "#f87171" : "#6b7280"} />
        </div>

        {/* ── FILTERS + SEARCH ── */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          {[["all", "All Drivers"], ["enroute", "En Route"], ["alerts", "Has Alerts"], ["delayed", "Delayed"], ["available", "Available"]].map(([k, l]) => (
            <button key={k} onClick={() => setFilter(k)} style={{
              padding: "5px 12px", borderRadius: 7, fontSize: 10, fontWeight: 600, cursor: "pointer", border: "0.5px solid",
              background: filter === k ? "rgba(29,158,117,.15)" : "rgba(255,255,255,.03)",
              borderColor: filter === k ? "rgba(29,158,117,.5)" : "rgba(255,255,255,.08)",
              color: filter === k ? "#34d399" : "rgba(255,255,255,.45)",
              transition: "all .15s",
            }}>{l}{k === "alerts" && alertCount > 0 ? ` (${alertCount})` : k === "delayed" && delayedCount > 0 ? ` (${delayedCount})` : ""}</button>
          ))}
          <div style={{ flex: 1 }} />
          <div style={{ position: "relative" }}>
            <input
              placeholder="Search driver, truck, load…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{
                background: "rgba(255,255,255,.04)", border: "0.5px solid rgba(255,255,255,.1)", borderRadius: 8,
                padding: "6px 10px 6px 28px", fontSize: 11, color: "#f1f5f9", outline: "none", width: 220,
              }}
            />
            <span style={{ position: "absolute", left: 9, top: "50%", transform: "translateY(-50%)", fontSize: 11, color: "rgba(255,255,255,.3)" }}>🔍</span>
          </div>
        </div>

        {/* ── TABLE ── */}
        <div style={{ borderRadius: 12, border: "0.5px solid rgba(255,255,255,.08)", overflow: "hidden", marginBottom: selectedDriver ? 12 : 0 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "0.5px solid rgba(255,255,255,.07)", background: "rgba(255,255,255,.02)" }}>
                <ColHeader label="Driver" k="name" />
                <ColHeader label="Status" k="status" />
                <ColHeader label="Location / Load" k="location" />
                <ColHeader label="HOS Remaining" k="hos" />
                <ColHeader label="Load Progress" k="progress" />
                <ColHeader label="ETA" k="eta" />
                <ColHeader label="Fuel" k="fuel" />
                <ColHeader label="Alerts" k="alerts" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((d, idx) => {
                const sm = STATUS_META[d.status] || STATUS_META["Off Duty"];
                const em = ETA_META[d.etaStatus];
                const isSelected = selectedId === d.id;
                const hasCritical = d.alerts.some(a => a.type === "critical");
                return (
                  <tr
                    key={d.id}
                    onClick={() => setSelectedId(isSelected ? null : d.id)}
                    style={{
                      borderBottom: "0.5px solid rgba(255,255,255,.05)",
                      background: isSelected ? "rgba(29,158,117,.08)" : hasCritical ? "rgba(248,113,113,.04)" : idx % 2 === 0 ? "transparent" : "rgba(255,255,255,.01)",
                      cursor: "pointer",
                      transition: "background .15s",
                      outline: isSelected ? "1px solid rgba(29,158,117,.25)" : "none",
                    }}
                    onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = "rgba(255,255,255,.04)"; }}
                    onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = hasCritical ? "rgba(248,113,113,.04)" : idx % 2 === 0 ? "transparent" : "rgba(255,255,255,.01)"; }}
                  >
                    {/* Driver */}
                    <td style={{ padding: "11px 12px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
                        <div style={{ width: 32, height: 32, borderRadius: 8, background: isSelected ? "rgba(29,158,117,.2)" : "rgba(255,255,255,.07)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 700, color: isSelected ? "#34d399" : "rgba(255,255,255,.6)", flexShrink: 0 }}>
                          {d.avatar}
                        </div>
                        <div>
                          <div style={{ fontSize: 12, fontWeight: 600, color: "#f1f5f9" }}>{d.name}</div>
                          <div style={{ fontSize: 10, color: "rgba(255,255,255,.35)", marginTop: 1 }}>{d.truckId}</div>
                        </div>
                      </div>
                    </td>

                    {/* Status */}
                    <td style={{ padding: "11px 12px" }}>
                      <div style={{ display: "inline-flex", alignItems: "center", gap: 5, background: sm.bg, border: `0.5px solid ${sm.color}33`, borderRadius: 6, padding: "3px 8px" }}>
                        <div style={{ width: 5, height: 5, borderRadius: "50%", background: sm.dot, flexShrink: 0 }} />
                        <span style={{ fontSize: 10, fontWeight: 600, color: sm.color, whiteSpace: "nowrap" }}>{d.status}</span>
                      </div>
                      {d.status === "En Route" && (
                        <div style={{ fontSize: 9, color: "rgba(255,255,255,.3)", marginTop: 3 }}>{d.speed} mph</div>
                      )}
                    </td>

                    {/* Location / Load */}
                    <td style={{ padding: "11px 12px", maxWidth: 200 }}>
                      <div style={{ fontSize: 11, color: "rgba(255,255,255,.7)", marginBottom: d.load ? 3 : 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{d.location}</div>
                      {d.load && (
                        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                          <span style={{ fontSize: 9, color: "#60a5fa", background: "rgba(96,165,250,.1)", border: "0.5px solid rgba(96,165,250,.25)", borderRadius: 4, padding: "1px 5px" }}>{d.load.id}</span>
                          <span style={{ fontSize: 9, color: "rgba(255,255,255,.35)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{d.load.origin} → {d.load.dest}</span>
                        </div>
                      )}
                    </td>

                    {/* HOS */}
                    <td style={{ padding: "11px 12px", minWidth: 120 }}>
                      {d.hosRemaining > 0 ? (
                        <HOSBar remaining={d.hosRemaining} driven={d.hosDriven} />
                      ) : (
                        <span style={{ fontSize: 10, color: "#6b7280" }}>34h reset</span>
                      )}
                    </td>

                    {/* Load Progress */}
                    <td style={{ padding: "11px 12px", minWidth: 110 }}>
                      {d.load ? <ProgressBar pct={d.load.progress} /> : <span style={{ fontSize: 10, color: "rgba(255,255,255,.2)" }}>No active load</span>}
                    </td>

                    {/* ETA */}
                    <td style={{ padding: "11px 12px" }}>
                      <div style={{ fontSize: 10, fontWeight: 600, color: em.color }}>{em.label}</div>
                      <div style={{ fontSize: 9, color: "rgba(255,255,255,.35)", marginTop: 2, whiteSpace: "nowrap" }}>{d.eta}</div>
                    </td>

                    {/* Fuel */}
                    <td style={{ padding: "11px 12px" }}>
                      <FuelDot level={d.fuelLevel} />
                    </td>

                    {/* Alerts */}
                    <td style={{ padding: "11px 12px", minWidth: 180 }}>
                      <AlertBadge alerts={d.alerts} />
                    </td>
                  </tr>
                );
              })}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ padding: 32, textAlign: "center", color: "rgba(255,255,255,.25)", fontSize: 12 }}>
                    No drivers match current filter
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* ── DRIVER DETAIL DRAWER ── */}
        {selectedDriver && (
          <div style={{ borderRadius: 12, border: "0.5px solid rgba(29,158,117,.3)", background: "rgba(29,158,117,.05)", padding: 16, display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 14 }}>
            {/* Identity */}
            <div>
              <div style={{ fontSize: 9, color: "rgba(255,255,255,.3)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Driver Profile</div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                <div style={{ width: 40, height: 40, borderRadius: 10, background: "rgba(29,158,117,.2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: "#34d399" }}>{selectedDriver.avatar}</div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700 }}>{selectedDriver.name}</div>
                  <div style={{ fontSize: 10, color: "rgba(255,255,255,.4)" }}>{selectedDriver.truckId}</div>
                </div>
              </div>
              {[
                ["Location", selectedDriver.location],
                ["On-Time Rate", selectedDriver.onTimeRate + "%"],
                ["Rating", selectedDriver.rating + " / 5.0"],
                ["Odometer", selectedDriver.odometer.toLocaleString() + " mi"],
              ].map(([l, v]) => (
                <div key={l} style={{ display: "flex", justifyContent: "space-between", fontSize: 10, padding: "4px 0", borderBottom: "0.5px solid rgba(255,255,255,.05)" }}>
                  <span style={{ color: "rgba(255,255,255,.35)" }}>{l}</span>
                  <span style={{ color: "rgba(255,255,255,.75)", fontWeight: 600 }}>{v}</span>
                </div>
              ))}
            </div>

            {/* HOS Detail */}
            <div>
              <div style={{ fontSize: 9, color: "rgba(255,255,255,.3)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Hours of Service</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: selectedDriver.hosRemaining <= 2 ? "#f87171" : selectedDriver.hosRemaining <= 4 ? "#fbbf24" : "#34d399", marginBottom: 4 }}>
                {selectedDriver.hosRemaining.toFixed(1)}h
              </div>
              <div style={{ fontSize: 10, color: "rgba(255,255,255,.4)", marginBottom: 12 }}>remaining of 11h daily limit</div>
              <HOSBar remaining={selectedDriver.hosRemaining} driven={selectedDriver.hosDriven} />
              <div style={{ marginTop: 10 }}>
                {[
                  ["Driven today", selectedDriver.hosDriven.toFixed(1) + "h"],
                  ["Status", selectedDriver.hosRemaining <= 2 ? "⚠ Critical" : selectedDriver.hosRemaining <= 4 ? "⚡ Low" : "✓ Good"],
                ].map(([l, v]) => (
                  <div key={l} style={{ display: "flex", justifyContent: "space-between", fontSize: 10, padding: "4px 0", borderBottom: "0.5px solid rgba(255,255,255,.05)" }}>
                    <span style={{ color: "rgba(255,255,255,.35)" }}>{l}</span>
                    <span style={{ color: "rgba(255,255,255,.75)", fontWeight: 600 }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Load Detail */}
            <div>
              <div style={{ fontSize: 9, color: "rgba(255,255,255,.3)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Active Load</div>
              {selectedDriver.load ? (
                <>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: "#60a5fa" }}>{selectedDriver.load.id}</span>
                    <span style={{ fontSize: 9, color: ETA_META[selectedDriver.etaStatus].color, background: `${ETA_META[selectedDriver.etaStatus].color}18`, border: `0.5px solid ${ETA_META[selectedDriver.etaStatus].color}44`, borderRadius: 4, padding: "1px 6px" }}>
                      {ETA_META[selectedDriver.etaStatus].label}
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: "rgba(255,255,255,.6)", marginBottom: 10 }}>{selectedDriver.load.origin} → {selectedDriver.load.dest}</div>
                  <ProgressBar pct={selectedDriver.load.progress} />
                  <div style={{ marginTop: 10 }}>
                    {[
                      ["ETA", selectedDriver.eta],
                      ["Speed", selectedDriver.speed > 0 ? selectedDriver.speed + " mph" : "Stationary"],
                      ["Fuel", selectedDriver.fuelLevel + "%"],
                    ].map(([l, v]) => (
                      <div key={l} style={{ display: "flex", justifyContent: "space-between", fontSize: 10, padding: "4px 0", borderBottom: "0.5px solid rgba(255,255,255,.05)" }}>
                        <span style={{ color: "rgba(255,255,255,.35)" }}>{l}</span>
                        <span style={{ color: "rgba(255,255,255,.75)", fontWeight: 600 }}>{v}</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div style={{ fontSize: 11, color: "rgba(255,255,255,.3)", fontStyle: "italic" }}>No active load</div>
              )}
            </div>

            {/* Actions */}
            <div>
              <div style={{ fontSize: 9, color: "rgba(255,255,255,.3)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Actions</div>
              {[
                ["Assign New Load", "#1d9e75", "#000"],
                ["Send Message", "rgba(255,255,255,.08)", "rgba(255,255,255,.7)"],
                ["View Trip History", "rgba(255,255,255,.08)", "rgba(255,255,255,.7)"],
                ["Flag for Review", "rgba(248,113,113,.12)", "#f87171"],
              ].map(([label, bg, color]) => (
                <button key={label} style={{
                  display: "block", width: "100%", padding: "8px 12px", borderRadius: 8, fontSize: 11, fontWeight: 600,
                  background: bg, color, border: "0.5px solid rgba(255,255,255,.08)", cursor: "pointer",
                  marginBottom: 6, textAlign: "left", transition: "opacity .15s",
                }}>{label}</button>
              ))}
              <button onClick={() => setSelectedId(null)} style={{
                display: "block", width: "100%", padding: "6px", borderRadius: 8, fontSize: 10,
                background: "transparent", color: "rgba(255,255,255,.25)", border: "none", cursor: "pointer", marginTop: 4,
              }}>Collapse ↑</button>
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
        input::placeholder { color: rgba(255,255,255,.2); }
        input:focus { border-color: rgba(29,158,117,.4) !important; }
        button:hover { opacity:.85; }
        * { box-sizing: border-box; }
      `}</style>
    </div>
  );
}
