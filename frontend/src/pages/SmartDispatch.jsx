import { useState, useEffect, useRef } from "react";
import { dispatchService } from "../api";

const DEFAULT_LOAD = {
  id: "LD-4821",
  origin: "Phoenix, AZ",
  originShort: "PHX",
  destination: "Dallas, TX",
  destinationShort: "DAL",
  miles: "1,072",
  pickupTime: "Today 14:00",
  deliveryDeadline: "Tomorrow 08:00",
  commodity: "Dry Goods — Electronics",
  weight: "42,000 lbs",
  rate: "$2,890",
  ratePerMile: "$2.70",
  specialNotes: "Liftgate required. No-touch freight.",
};

const MOCK_DRIVERS = [
  {
    id: "D-001", name: "Marcus Rivera", avatar: "MR",
    location: "Mesa, AZ", distanceToPickup: 18,
    hosRemaining: 9.5, hosStatus: "Available",
    lastLoad: "Tucson → Phoenix", truckId: "TRK-114",
    fuelLevel: 78, rating: 4.8, totalMiles: 312000,
    recentOnTime: 96, deadheadMiles: 18,
    estimatedCostPerMile: 2.61, estimatedFuelCost: 198,
  },
  {
    id: "D-002", name: "Sandra Kim", avatar: "SK",
    location: "Tempe, AZ", distanceToPickup: 22,
    hosRemaining: 7.2, hosStatus: "Available",
    lastLoad: "Flagstaff → Tempe", truckId: "TRK-089",
    fuelLevel: 52, rating: 4.9, totalMiles: 287000,
    recentOnTime: 98, deadheadMiles: 22,
    estimatedCostPerMile: 2.68, estimatedFuelCost: 211,
  },
  {
    id: "D-003", name: "James Okafor", avatar: "JO",
    location: "Chandler, AZ", distanceToPickup: 31,
    hosRemaining: 6.0, hosStatus: "At Risk",
    lastLoad: "Albuquerque → Chandler", truckId: "TRK-201",
    fuelLevel: 34, rating: 4.5, totalMiles: 198000,
    recentOnTime: 88, deadheadMiles: 31,
    estimatedCostPerMile: 2.74, estimatedFuelCost: 228,
  },
  {
    id: "D-004", name: "Tanya Reyes", avatar: "TR",
    location: "Gilbert, AZ", distanceToPickup: 41,
    hosRemaining: 10.0, hosStatus: "Available",
    lastLoad: "Tucson → Gilbert", truckId: "TRK-177",
    fuelLevel: 91, rating: 4.7, totalMiles: 254000,
    recentOnTime: 93, deadheadMiles: 41,
    estimatedCostPerMile: 2.79, estimatedFuelCost: 245,
  },
];

const HOS_NEEDED = 8.5;

function ScoreBar({ value, max = 100, color }) {
  const pct = Math.round((value / max) * 100);
  const colorMap = {
    teal: "bg-teal-400",
    amber: "bg-amber-400",
    red: "bg-red-400",
    blue: "bg-blue-400",
  };
  return (
    <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full ${colorMap[color] || "bg-teal-400"} transition-all duration-700`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

function StatPill({ label, value, warn }) {
  return (
    <div className={`flex flex-col items-center px-3 py-1.5 rounded-md border ${warn ? "border-amber-500/40 bg-amber-500/10" : "border-white/10 bg-white/5"}`}>
      <span className={`text-xs font-semibold leading-tight ${warn ? "text-amber-300" : "text-white"}`}>{value}</span>
      <span className="text-[10px] text-white/40 mt-0.5 whitespace-nowrap">{label}</span>
    </div>
  );
}

function DriverCard({ driver, rank, selected, onClick, aiResult, loading }) {
  const hosOk = driver.hosRemaining >= HOS_NEEDED;
  const rankColors = ["text-teal-300 border-teal-400/50 bg-teal-400/10", "text-blue-300 border-blue-400/50 bg-blue-400/10", "text-white/60 border-white/20 bg-white/5", "text-white/40 border-white/10 bg-white/5"];
  const rankLabels = ["#1 Recommended", "#2 Strong", "#3 Viable", "#4 Not ideal"];
  const borderColors = ["border-teal-400/40", "border-blue-400/30", "border-white/15", "border-white/10"];

  return (
    <div
      onClick={onClick}
      className={`relative rounded-xl border cursor-pointer transition-all duration-200 overflow-hidden
        ${selected ? "border-teal-400/60 bg-teal-900/20 shadow-lg shadow-teal-900/20" : `${borderColors[rank]} bg-white/[0.03] hover:bg-white/[0.06]`}`}
    >
      <div className={`absolute top-3 right-3 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${rankColors[rank]}`}>
        {rankLabels[rank]}
      </div>

      <div className="p-4">
        <div className="flex items-start gap-3 mb-3">
          <div className={`w-9 h-9 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0
            ${rank === 0 ? "bg-teal-500/20 text-teal-300" : "bg-white/10 text-white/70"}`}>
            {driver.avatar}
          </div>
          <div className="flex-1 min-w-0 pr-24">
            <div className="text-sm font-semibold text-white leading-tight">{driver.name}</div>
            <div className="text-[11px] text-white/50 mt-0.5">{driver.truckId} · {driver.location}</div>
          </div>
        </div>

        <div className="flex gap-2 mb-3 flex-wrap">
          <StatPill label="HOS left" value={driver.hosRemaining != null ? `${driver.hosRemaining}h` : 'N/A'} warn={driver.hosRemaining < 8.5} />
          <StatPill label="To pickup" value={driver.distanceToPickup != null ? `${driver.distanceToPickup}mi` : 'N/A'} />
          <StatPill label="Fuel" value={driver.fuelLevel != null ? `${driver.fuelLevel}%` : 'N/A'} warn={driver.fuelLevel < 40} />
          <StatPill label="OOR Mi" value={driver.oorMiles != null ? `${driver.oorMiles} mi` : 'N/A'} warn={driver.oorMiles > driver.scheduleMiles * 0.05} />
        </div>

        {/* Alerts bar */}
        {driver.alerts && driver.alerts.length > 0 && (
          <div className="mb-3 space-y-1">
            {driver.alerts.map((alert, idx) => (
              <div key={idx} className={`text-[10px] px-2 py-1 rounded border ${alert.severity === 'high' ? 'bg-red-500/20 border-red-500/40 text-red-200' : alert.severity === 'medium' ? 'bg-amber-500/20 border-amber-500/40 text-amber-200' : 'bg-blue-500/20 border-blue-500/40 text-blue-200'}`}>
                ⚠ {alert.text}
              </div>
            ))}
          </div>
        )}

        <div className={`rounded-lg border p-3 mt-2 transition-all duration-300 min-h-[56px]
          ${selected ? "border-teal-500/30 bg-teal-900/20" : "border-white/8 bg-black/20"}`}>
          <div className="text-[10px] font-semibold text-white/40 uppercase tracking-wider mb-1.5">AI Reasoning</div>
          {loading ? (
            <div className="flex items-center gap-2">
              <div className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <div key={i} className="w-1.5 h-1.5 rounded-full bg-teal-400/60 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                ))}
              </div>
              <span className="text-[11px] text-white/30">Analyzing driver profile...</span>
            </div>
          ) : aiResult ? (
            <p className="text-[11px] text-white/70 leading-relaxed">{aiResult}</p>
          ) : (
            <p className="text-[11px] text-white/25 italic">Click "Run AI Dispatch" to generate reasoning</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default function SmartDispatch() {
  const [load, setLoad] = useState(DEFAULT_LOAD);
  const [loadsList, setLoadsList] = useState([]);
  const [aiResults, setAiResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [dispatched, setDispatched] = useState(false);
  const [overallLoading, setOverallLoading] = useState(false);
  const [rankedDrivers, setRankedDrivers] = useState([]);
  const [analysisPhase, setAnalysisPhase] = useState("");

  useEffect(() => {
    dispatchService.getLoads()
      .then(loads => {
        if (loads && loads.length > 0) {
          setLoadsList(loads);
          setLoad(loads[0]);
        }
      })
      .catch(console.error);
  }, []);

  const fetchRecommendations = async () => {
    setOverallLoading(true);
    setAnalysisPhase("Fetching driver HOS & GPS data...");

    try {
      setAnalysisPhase("Scoring proximity & route efficiency...");
      await new Promise(r => setTimeout(r, 800)); // Visual feedback

      setAnalysisPhase("Ranking 100% of available fleet with backend scoring engine...");
      // Fetch full ranking across all drivers
      const recommendationsFull = await dispatchService.getRecommendations(load.id);
      if (!recommendationsFull) throw new Error("No fleet data returned");

      // Concurrently fetch AI reasoning for why the top matches were selected
      setAnalysisPhase("Applying LLM reasoning for top candidates...");
      let aiRationale = null;
      let topDriverId = null;
      try {
        const explained = await dispatchService.getRecommendationsExplained(load.id);
        if (explained && explained.top_candidate) {
          aiRationale = explained.ai_rationale;
          topDriverId = explained.top_candidate.driver_id.toString();
        }
      } catch (err) {
        console.warn("AI generation error handled:", err);
      }

      const mappedDrivers = recommendationsFull.map(r => ({
        id: r.driver_id.toString(),
        name: r.driver_name,
        avatar: r.driver_name.split(' ').map(n => n[0] || '').join(''),
        location: r.driver_card.location_label,
        truckId: r.vehicle_no,
        status: r.driver_card.status_label,
        alerts: r.driver_card.alerts || [],
        hosRemaining: r.driver_card.hos_remaining_hours,
        distanceToPickup: r.driver_card.distance_to_pickup,
        fuelLevel: r.driver_card.fuel_pct,
        oorMiles: r.driver_card.performance ? r.driver_card.performance.oor_miles : null,
        scheduleMiles: r.driver_card.performance ? r.driver_card.performance.schedule_miles : null,
        actualMiles: r.driver_card.performance ? r.driver_card.performance.actual_miles : null,
        scheduleTime: r.driver_card.performance ? r.driver_card.performance.schedule_time : null,
        actualTime: r.driver_card.performance ? r.driver_card.performance.actual_time : null,
      }));

      const reasoning = {};
      recommendationsFull.forEach(r => {
        reasoning[r.driver_id.toString()] = r.reasons.join(". ") + (r.warnings.length ? ". Warnings: " + r.warnings.join(". ") : "");
      });

      // Override the top candidate's algorithmic reasoning with the actual Groq LLM logic
      if (topDriverId && aiRationale) {
        reasoning[topDriverId] = aiRationale;
      }

      setRankedDrivers(mappedDrivers);
      setAiResults(reasoning);
      setSelectedDriver(mappedDrivers[0]?.id || null);
    } catch (error) {
      console.error("Failed to fetch recommendations:", error);
    } finally {
      setOverallLoading(false);
      setAnalysisPhase("");
    }
  };

  const runDispatch = async () => {
    if (loading || overallLoading) return;
    setAiResults({});
    setSelectedDriver(null);
    setDispatched(false);
    setStreamedText("");
    setOverallLoading(true);

    const phases = ["Fetching driver HOS & GPS data...", "Scoring proximity & deadhead miles...", "Evaluating fuel costs & route efficiency...", "Ranking drivers with AI..."];
    for (let p of phases) {
      setAnalysisPhase(p);
      await new Promise(r => setTimeout(r, 600));
    }
    setAnalysisPhase("");

    const driversInfo = MOCK_DRIVERS.map((d, i) => `Driver ${i + 1}: ${d.name} (${d.id})
- Location: ${d.location}, ${d.distanceToPickup} miles from pickup
- HOS remaining: ${d.hosRemaining}h (need ${HOS_NEEDED}h minimum)
- Fuel level: ${d.fuelLevel}%
- Recent on-time rate: ${d.recentOnTime}%
- Deadhead miles: ${d.deadheadMiles}
- Estimated cost per mile: $${d.estimatedCostPerMile}
- Rating: ${d.rating}/5`).join("\n\n");

    const prompt = `You are an AI dispatch assistant for a trucking fleet. Analyze these drivers for Load ${LOAD.id}:

LOAD DETAILS:
- Route: ${LOAD.origin} → ${LOAD.destination} (${LOAD.miles} miles)
- Pickup: ${LOAD.pickupTime}
- Delivery deadline: ${LOAD.deliveryDeadline}
- Weight: ${LOAD.weight}
- Notes: ${LOAD.specialNotes}
- HOS required: at least ${HOS_NEEDED} hours

AVAILABLE DRIVERS:
${driversInfo}

Return ONLY a valid JSON object with this exact structure, no markdown, no explanation:
{
  "ranking": ["D-001","D-002","D-003","D-004"],
  "reasoning": {
    "D-001": "2-sentence dispatch reasoning for this driver for this specific load",
    "D-002": "2-sentence dispatch reasoning",
    "D-003": "2-sentence dispatch reasoning",
    "D-004": "2-sentence dispatch reasoning"
  }
}

Focus reasoning on: HOS fit, proximity to pickup, cost efficiency, on-time history, and any risks. Be specific and decisive.`;

    const OPS_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

    try {
      let parsed = null;

      // Try Flask /loads/<id>/recommendations first (live backend)
      const flaskRes = await fetch(`${OPS_URL}/loads/${LOAD.id}/recommendations`).catch(() => null);
      if (flaskRes && flaskRes.ok) {
        const flaskData = await flaskRes.json();
        if (flaskData.recommendations && Array.isArray(flaskData.recommendations)) {
          const ranking = flaskData.recommendations.map(r => r.driver_id || r.id).filter(Boolean);
          const reasoning = {};
          flaskData.recommendations.forEach(r => {
            const id = r.driver_id || r.id;
            if (id) reasoning[id] = r.reasoning || r.summary || "Recommended by dispatch engine.";
          });
          parsed = { ranking, reasoning };
        }
      }

      // If Flask unavailable, fall back to direct Anthropic call
      if (!parsed) {
        const response = await fetch("https://api.anthropic.com/v1/messages", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            model: "claude-sonnet-4-20250514",
            max_tokens: 1000,
            messages: [{ role: "user", content: prompt }],
          }),
        });
        const data = await response.json();
        const text = data.content?.map(b => b.text || "").join("") || "";
        const clean = text.replace(/```json|```/g, "").trim();
        parsed = JSON.parse(clean);
      }

      // Reorder drivers by AI ranking
      const ordered = parsed.ranking.map(id => MOCK_DRIVERS.find(d => d.id === id)).filter(Boolean);
      setRankedDrivers(ordered);
      setAiResults(parsed.reasoning || {});
      setSelectedDriver(ordered[0]?.id || null);
    } catch (e) {
      const fallback = {
        "D-001": "Marcus is the top pick — 18 miles from pickup with 9.5h HOS comfortably covers the 8.5h requirement, and his 96% on-time rate and lowest deadhead cost make him the most cost-efficient assignment.",
        "D-002": "Sandra has the highest on-time rate in the fleet at 98% and is only 22 miles out, but her 7.2h HOS is tighter and her fuel level at 52% will require a fill stop that adds cost.",
        "D-003": "James is borderline — his 6.0h HOS is below the 8.5h needed for this run, creating a compliance risk. Assign only if Marcus and Sandra are unavailable and HOS can be recalculated.",
        "D-004": "Tanya has maximum HOS and high fuel, but at 41 deadhead miles she's the most expensive option. Reserve her for loads that originate further east.",
      };
      setAiResults(fallback);
      setSelectedDriver("D-001");
    }

    setOverallLoading(false);
  };

  const confirmDispatch = () => {
    if (!selectedDriver) return;
    setDispatched(true);
  };

  const selectedInfo = rankedDrivers.find(d => d.id === selectedDriver);
  const selectedRank = rankedDrivers.findIndex(d => d.id === selectedDriver);
  const hasResults = Object.keys(aiResults).length > 0;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold tracking-tight">Smart Dispatch</h2>
        <div className="flex items-center gap-2 text-[11px] text-brand-muted">
          <div className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-pulse" />
          Analyzing Fleet in Real-time
        </div>
      </div>

      <div className="grid grid-cols-[1fr_340px] gap-6">

        {/* LEFT: drivers */}
        <div>
          {/* Load Selector */}
          {loadsList.length > 0 && (
            <div className="mb-4">
              <label className="text-[10px] text-white/40 uppercase tracking-widest block mb-1">Select Load</label>
              <select
                className="w-full bg-black/40 border border-white/10 rounded-lg p-2.5 text-sm font-semibold text-white/90 outline-none focus:border-teal-500/50 transition-colors"
                value={load.id}
                onChange={(e) => {
                  const selected = loadsList.find(l => l.id === e.target.value);
                  if (selected) {
                    setLoad(selected);
                    setRankedDrivers([]);
                    setAiResults({});
                  }
                }}
              >
                {loadsList.map(l => (
                  <option key={l.id} value={l.id}>
                    {l.pickup_name || l.origin} → {l.dropoff_name || l.destination} ({new Date(l.pickup_time || l.pickupTime).toLocaleString()})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Load card */}
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 mb-5">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-semibold tracking-widest text-white/40 uppercase">Load</span>
                  <span className="text-xs font-bold text-teal-300 bg-teal-900/30 border border-teal-500/30 px-2 py-0.5 rounded">{load.id}</span>
                  <span className="text-[10px] text-amber-400 bg-amber-900/20 border border-amber-500/30 px-2 py-0.5 rounded">Unassigned</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-bold text-white tracking-tight">
                    {load.originShort || (load.origin ? load.origin.slice(0, 3) : load.pickup_name ? load.pickup_name.slice(0, 3) : 'UNK').toUpperCase()}
                  </span>
                  <div className="flex-1 flex items-center gap-1 px-2">
                    <div className="flex-1 h-px bg-white/20" />
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6h8M7 3l3 3-3 3" stroke="white" strokeOpacity=".5" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
                    <div className="flex-1 h-px bg-white/20" />
                  </div>
                  <span className="text-xl font-bold text-white tracking-tight">
                    {load.destinationShort || (load.destination ? load.destination.slice(0, 3) : load.dropoff_name ? load.dropoff_name.slice(0, 3) : 'UNK').toUpperCase()}
                  </span>
                </div>
                <div className="text-[11px] text-white/40 mt-0.5">{load.origin || load.pickup_name || 'N/A'} → {load.destination || load.dropoff_name || 'N/A'}</div>
              </div>
              <div className="text-right">
                <div className="text-xl font-bold text-teal-300">{load.rate || '$2,450'}</div>
                <div className="text-[11px] text-white/40">{load.ratePerMile || '$2.25'}/mi</div>
              </div>
            </div>
            <div className="grid grid-cols-4 gap-3 pt-3 border-t border-white/8">
              {[
                ["Distance", `${load.miles || 850} mi`],
                ["Pickup", load.pickupTime || load.pickup_time],
                ["Deadline", load.deliveryDeadline || load.dropoff_time],
                ["Weight", load.weight || '42,000 lbs'],
              ].map(([label, val]) => (
                <div key={label}>
                  <div className="text-[10px] text-white/35 uppercase tracking-wider">{label}</div>
                  <div className="text-xs text-white/80 font-semibold mt-0.5">{val}</div>
                </div>
              ))}
            </div>
            <div className="mt-2 pt-2 border-t border-white/8 text-[11px] text-white/40">
              <span className="text-white/25">Commodity:</span> {load.commodity || 'General Freight'} &nbsp;·&nbsp; <span className="text-white/25">Notes:</span> {load.specialNotes || 'Standard delivery.'}
            </div>
          </div>

          {overallLoading && (
            <div className="rounded-xl border border-teal-500/30 bg-teal-900/10 px-5 py-4 mb-4 flex items-center gap-3">
              <div className="flex gap-1 flex-shrink-0">
                {[0, 1, 2, 3].map(i => (
                  <div key={i} className="w-1 h-4 bg-teal-400/70 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.1}s` }} />
                ))}
              </div>
              <div>
                <div className="text-xs font-semibold text-teal-300">AI Analysis in Progress</div>
                <div className="text-[11px] text-teal-300/60 mt-0.5">{analysisPhase}</div>
              </div>
            </div>
          )}

          <div className="space-y-3">
            {rankedDrivers.map((driver, i) => (
              <DriverCard
                key={driver.id}
                driver={driver}
                rank={i}
                selected={selectedDriver === driver.id}
                onClick={() => !dispatched && setSelectedDriver(driver.id)}
                aiResult={aiResults[driver.id]}
                loading={overallLoading}
              />
            ))}
          </div>
        </div>

        {/* RIGHT: action panel */}
        <div className="space-y-4">

          <button
            onClick={runDispatch}
            disabled={overallLoading || dispatched}
            className={`w-full py-3.5 rounded-xl font-bold text-sm tracking-wider transition-all duration-200 border
              ${dispatched
                ? "bg-white/5 border-white/10 text-white/30 cursor-not-allowed"
                : overallLoading
                  ? "bg-teal-900/30 border-teal-500/30 text-teal-400/60 cursor-not-allowed"
                  : "bg-brand-primary border-brand-primary text-black hover:opacity-90 active:scale-95 shadow-lg shadow-teal-900/40"
              }`}
          >
            {overallLoading ? "ANALYZING FLEET..." : dispatched ? "DISPATCHED ✓" : hasResults ? "RE-RUN AI DISPATCH" : "▶  RUN AI DISPATCH"}
          </button>

          {selectedInfo && !dispatched && (
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <div className="text-[10px] text-white/35 uppercase tracking-widest mb-3">Selected Assignment</div>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-teal-500/20 text-teal-300 flex items-center justify-center font-bold text-sm">
                  {selectedInfo.avatar}
                </div>
                <div>
                  <div className="text-sm font-bold text-white">{selectedInfo.name}</div>
                  <div className="text-[11px] text-white/40">{selectedInfo.truckId} · Rank #{selectedRank + 1}</div>
                </div>
              </div>
              <div className="space-y-2 mb-4">
                {[
                  ["Status", selectedInfo.status || 'Unknown'],
                  ["Distance to Pickup", selectedInfo.distanceToPickup != null ? `${selectedInfo.distanceToPickup} mi` : 'N/A'],
                  ["HOS Available", selectedInfo.hosRemaining != null ? `${selectedInfo.hosRemaining}h` : 'N/A'],
                  ["Fuel Level", selectedInfo.fuelLevel != null ? `${selectedInfo.fuelLevel}%` : 'N/A'],
                  ["Scheduled Miles", selectedInfo.scheduleMiles != null ? `${selectedInfo.scheduleMiles} mi` : 'N/A'],
                  ["Actual Miles", selectedInfo.actualMiles != null ? `${selectedInfo.actualMiles} mi` : 'N/A'],
                  ["Out-of-Route Miles", selectedInfo.oorMiles != null ? `${selectedInfo.oorMiles} mi` : 'N/A'],
                ].map(([label, val]) => (
                  <div key={label} className="flex justify-between text-[11px]">
                    <span className="text-white/40">{label}</span>
                    <span className="text-white/80 font-semibold">{val}</span>
                  </div>
                ))}
              </div>
              <button
                onClick={confirmDispatch}
                className="w-full py-2.5 rounded-lg bg-white text-black font-bold text-xs tracking-widest hover:bg-white/90 active:scale-95 transition-all"
              >
                CONFIRM DISPATCH →
              </button>
              <button
                onClick={() => setSelectedDriver(null)}
                className="w-full py-2 rounded-lg text-white/30 text-xs hover:text-white/50 mt-1 transition-colors"
              >
                Cancel
              </button>
            </div>
          )}

          {dispatched && selectedInfo && (
            <div className="rounded-xl border border-teal-400/40 bg-teal-900/20 p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-5 h-5 rounded-full bg-teal-400 flex items-center justify-center flex-shrink-0">
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2 5l2.5 2.5L8 2.5" stroke="black" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
                </div>
                <span className="text-sm font-bold text-teal-300">Load Assigned</span>
              </div>
              <p className="text-[11px] text-teal-300/70 leading-relaxed">
                {LOAD.id} dispatched to <strong className="text-teal-200">{selectedInfo.name}</strong> ({selectedInfo.truckId}). Notification sent. ETA calculated.
              </p>
              <div className="mt-3 pt-3 border-t border-teal-500/20 text-[11px] text-teal-300/50">
                Dispatched at {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          )}

          <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
            <div className="text-[10px] text-white/30 uppercase tracking-widest mb-3">Scoring Factors</div>
            <div className="space-y-2">
              {[
                ["HOS Compliance", "Must have ≥8.5h remaining"],
                ["Proximity", "Deadhead miles to pickup"],
                ["Cost Efficiency", "Estimated CPM including deadhead"],
                ["Reliability", "Recent on-time delivery rate"],
                ["Fuel Status", "Avoid stops that add delay"],
              ].map(([factor, desc]) => (
                <div key={factor} className="flex gap-2 text-[11px]">
                  <div className="w-1 h-1 rounded-full bg-teal-400/60 mt-1.5 flex-shrink-0" />
                  <div>
                    <span className="text-white/60 font-semibold">{factor}</span>
                    <span className="text-white/30"> — {desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Performance summary */}
          {hasResults && !overallLoading && (
            <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
              <div className="text-[10px] text-white/30 uppercase tracking-widest mb-3">Performance Comparison</div>
              <div className="space-y-2">
                {rankedDrivers.map((d, i) => {
                  const scheduleSpeed = (d.scheduleTime && d.scheduleMiles) ? (d.scheduleMiles / (d.scheduleTime / 60)).toFixed(1) : 'N/A';
                  return (
                    <div key={d.id} className={`flex items-center gap-2 text-[11px] p-1.5 rounded-md transition-colors ${selectedDriver === d.id ? "bg-teal-900/20" : ""}`}>
                      <span className={`w-4 text-center font-bold ${i === 0 ? "text-teal-400" : "text-white/30"}`}>{i + 1}</span>
                      <span className="text-white/60 flex-1 truncate">{d.name.split(" ")[0]}</span>
                      <span className={`font-semibold ${i === 0 ? "text-teal-300" : "text-white/50"}`}>{scheduleSpeed} mph av.</span>
                      {i === 0 && <span className="text-[9px] text-teal-400 bg-teal-900/40 px-1.5 py-0.5 rounded">BEST</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}