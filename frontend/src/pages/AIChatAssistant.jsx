import { useState, useEffect, useRef, useCallback } from "react";
import { chatService } from "../api";

// ─── FLEET CONTEXT (Initial placeholders, real data comes from backend) ──
const FLEET = [
  { id: "D-001", name: "Marcus Rivera", truck: "TRK-114", location: "I-10 E, Lordsburg NM", status: "En Route", hos: 9.5, load: { id: "LD-4821", origin: "Phoenix AZ", dest: "Dallas TX", progress: 34, deadline: "Tomorrow 07:42" }, speed: 67, fuel: 71, onTime: 96, cpm: 2.61, alerts: [] },
  { id: "D-002", name: "Sandra Kim", truck: "TRK-089", location: "Tempe AZ — Truck Stop", status: "On Break", hos: 7.2, load: { id: "LD-4798", origin: "LA CA", dest: "Albuquerque NM", progress: 0, deadline: "Pending" }, speed: 0, fuel: 52, onTime: 98, cpm: 2.68, alerts: ["Break ends in 22 min"] },
  { id: "D-003", name: "James Okafor", truck: "TRK-201", location: "US-60 W, Globe AZ", status: "En Route", hos: 2.1, load: { id: "LD-4809", origin: "Albuquerque NM", dest: "Phoenix AZ", progress: 71, deadline: "Today 18:30" }, speed: 58, fuel: 29, onTime: 88, cpm: 2.74, alerts: ["HOS critical — 2.1h remaining", "Fuel below 30%"] },
  { id: "D-004", name: "Tanya Reyes", truck: "TRK-177", location: "Tucson AZ — Delivered", status: "Available", hos: 10.0, load: null, speed: 0, fuel: 91, onTime: 93, cpm: 2.79, alerts: [] },
  { id: "D-005", name: "Devon Carter", truck: "TRK-033", location: "I-40 W, Gallup NM", status: "En Route", hos: 5.5, load: { id: "LD-4815", origin: "Albuquerque NM", dest: "Flagstaff AZ", progress: 55, deadline: "Today 21:15" }, speed: 62, fuel: 48, onTime: 81, cpm: 2.74, alerts: ["Running 47 min behind schedule", "Wind advisory on I-40"] },
  { id: "D-006", name: "Priya Nair", truck: "TRK-158", location: "Phoenix AZ — Yard", status: "Off Duty", hos: 0, load: null, speed: 0, fuel: 64, onTime: 95, cpm: 2.65, alerts: ["34h reset — available tomorrow 09:00"] },
  { id: "D-007", name: "Luis Mendoza", truck: "TRK-092", location: "I-17 N, Camp Verde AZ", status: "En Route", hos: 6.8, load: { id: "LD-4822", origin: "Phoenix AZ", dest: "Flagstaff AZ", progress: 62, deadline: "Today 16:50" }, speed: 71, fuel: 83, onTime: 92, cpm: 2.68, alerts: [] },
  { id: "D-008", name: "Rachel Stone", truck: "TRK-245", location: "US-93 N, Wikieup AZ", status: "En Route", hos: 8.3, load: { id: "LD-4817", origin: "Phoenix AZ", dest: "Las Vegas NV", progress: 28, deadline: "Today 20:10" }, speed: 65, fuel: 77, onTime: 94, cpm: 2.71, alerts: [] },
];

const SUGGESTED = [
  "Which drivers will miss their delivery windows today?",
  "Who can take a new load from Phoenix to El Paso right now?",
  "Give me a summary of all active alerts",
  "Which driver has the best cost per mile available?",
  "What's James Okafor's current status?",
  "How many drivers are available for dispatch?",
  "Who's running low on fuel and still en route?",
  "Rank available drivers for a load from Tucson to LA",
];

// ─── UTILITIES ────────────────────────────────────────────────────────────
function timeStr() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function parseAIResponse(raw) {
  try {
    const clean = raw.replace(/```json|```/g, "").trim();
    const start = clean.indexOf("{");
    const end = clean.lastIndexOf("}");
    if (start === -1 || end === -1) throw new Error("no json");
    return JSON.parse(clean.slice(start, end + 1));
  } catch {
    return {
      headline: "Response received",
      summary: raw.slice(0, 400),
      type: "info",
      drivers: [],
      tableRows: [],
      actions: [],
      severity: "normal",
    };
  }
}

// ─── SUB-COMPONENTS ───────────────────────────────────────────────────────

const TAG_COLORS = {
  green: { bg: "rgba(52,211,153,.12)", border: "rgba(52,211,153,.3)", text: "#34d399" },
  amber: { bg: "rgba(251,191,36,.12)", border: "rgba(251,191,36,.3)", text: "#fbbf24" },
  red: { bg: "rgba(248,113,113,.12)", border: "rgba(248,113,113,.3)", text: "#f87171" },
  blue: { bg: "rgba(96,165,250,.12)", border: "rgba(96,165,250,.3)", text: "#60a5fa" },
  gray: { bg: "rgba(107,114,128,.12)", border: "rgba(107,114,128,.3)", text: "#9ca3af" },
};

function DriverChip({ driver }) {
  const tc = TAG_COLORS[driver.tagColor] || TAG_COLORS.gray;
  const fleetDriver = FLEET.find(d => d.id === driver.id);
  return (
    <div style={{ background: "rgba(255,255,255,.03)", border: "0.5px solid rgba(255,255,255,.1)", borderRadius: 8, padding: "8px 10px", marginBottom: 6 }}>
      <div style={{ display: "flex", alignItems: "center", justifyItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {driver.rank && (
            <span style={{ fontSize: 9, fontWeight: 700, color: "rgba(255,255,255,.3)", minWidth: 14 }}>#{driver.rank}</span>
          )}
          <div style={{ width: 26, height: 26, borderRadius: 6, background: "rgba(255,255,255,.07)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 700, color: "rgba(255,255,255,.55)" }}>
            {driver.name.split(" ").map(n => n[0]).join("")}
          </div>
          <span style={{ fontSize: 12, fontWeight: 600, color: "#f1f5f9" }}>{driver.name}</span>
          {fleetDriver && <span style={{ fontSize: 9, color: "rgba(255,255,255,.3)" }}>{fleetDriver.truck}</span>}
        </div>
        <span style={{ fontSize: 9, fontWeight: 600, padding: "2px 7px", borderRadius: 4, background: tc.bg, border: `0.5px solid ${tc.border}`, color: tc.text }}>{driver.tag}</span>
      </div>
      {fleetDriver && (
        <div style={{ display: "flex", gap: 10, marginBottom: driver.note ? 6 : 0 }}>
          {[
            ["HOS", fleetDriver.hos + "h", fleetDriver.hos <= 2 ? "#f87171" : fleetDriver.hos <= 4 ? "#fbbf24" : "#34d399"],
            ["Fuel", fleetDriver.fuel + "%", fleetDriver.fuel < 30 ? "#f87171" : fleetDriver.fuel < 50 ? "#fbbf24" : "#34d399"],
            ["On-time", fleetDriver.onTime + "%", "#94a3b8"],
            ["CPM", "$" + fleetDriver.cpm, "#94a3b8"],
          ].map(([label, val, color]) => (
            <div key={label} style={{ display: "flex", flexDirection: "column", alignItems: "center", background: "rgba(255,255,255,.04)", borderRadius: 5, padding: "3px 7px" }}>
              <span style={{ fontSize: 11, fontWeight: 700, color }}>{val}</span>
              <span style={{ fontSize: 8, color: "rgba(255,255,255,.3)", marginTop: 1 }}>{label}</span>
            </div>
          ))}
        </div>
      )}
      {driver.note && (
        <p style={{ fontSize: 10, color: "rgba(255,255,255,.5)", lineHeight: 1.5, margin: 0, paddingTop: 4, borderTop: "0.5px solid rgba(255,255,255,.06)" }}>{driver.note}</p>
      )}
    </div>
  );
}

function AIMessageCard({ msg, onAction }) {
  const data = msg.parsed;
  if (!data) return null;

  const severityBorder = data.severity === "critical" ? "rgba(248,113,113,.35)" : data.severity === "warning" ? "rgba(251,191,36,.25)" : "rgba(29,158,117,.2)";
  const severityBg = data.severity === "critical" ? "rgba(248,113,113,.05)" : data.severity === "warning" ? "rgba(251,191,36,.04)" : "rgba(29,158,117,.04)";
  const typeIcon = { info: "◈", alert: "⚠", recommendation: "◆", ranking: "▲", status: "●" }[data.type] || "◈";
  const typeColor = { info: "#60a5fa", alert: "#f87171", recommendation: "#34d399", ranking: "#a78bfa", status: "#fbbf24" }[data.type] || "#60a5fa";

  const BTN_STYLES = {
    primary: { bg: "#1d9e75", color: "#000", border: "none" },
    secondary: { bg: "rgba(255,255,255,.07)", color: "rgba(255,255,255,.7)", border: "0.5px solid rgba(255,255,255,.12)" },
    danger: { bg: "rgba(248,113,113,.12)", color: "#f87171", border: "0.5px solid rgba(248,113,113,.25)" },
  };

  return (
    <div style={{ border: `0.5px solid ${severityBorder}`, background: severityBg, borderRadius: 10, padding: "12px 14px", marginBottom: 2 }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: 11, color: typeColor, marginTop: 1, flexShrink: 0 }}>{typeIcon}</span>
        <h3 style={{ fontSize: 13, fontWeight: 700, color: "#f1f5f9", margin: 0, lineHeight: 1.3 }}>{data.headline}</h3>
      </div>

      {data.summary && (
        <p style={{ fontSize: 11, color: "rgba(255,255,255,.6)", lineHeight: 1.65, margin: "0 0 10px 0", paddingLeft: 19 }}>{data.summary}</p>
      )}

      {data.drivers?.length > 0 && (
        <div style={{ paddingLeft: 19, marginBottom: 8 }}>
          {data.drivers.map((d, i) => <DriverChip key={i} driver={d} />)}
        </div>
      )}

      {data.tableRows?.length > 0 && (
        <div style={{ paddingLeft: 19, marginBottom: 8 }}>
          <div style={{ border: "0.5px solid rgba(255,255,255,.08)", borderRadius: 7, overflow: "hidden" }}>
            {data.tableRows.map((row, i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "6px 10px", background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,.02)", borderBottom: i < data.tableRows.length - 1 ? "0.5px solid rgba(255,255,255,.05)" : "none" }}>
                <span style={{ fontSize: 10, color: "rgba(255,255,255,.4)" }}>{row.label}</span>
                <span style={{ fontSize: 10, fontWeight: 600, color: "rgba(255,255,255,.8)" }}>{row.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.actions?.length > 0 && (
        <div style={{ paddingLeft: 19, display: "flex", gap: 6, flexWrap: "wrap" }}>
          {data.actions.map((action, i) => {
            const s = BTN_STYLES[action.type] || BTN_STYLES.secondary;
            return (
              <button
                key={i}
                className="action-btn"
                onClick={() => {
                  console.log("Action button clicked:", action.label);
                  if (onAction) onAction(action.label);
                }}
                style={{ fontSize: 10, fontWeight: 600, padding: "5px 12px", borderRadius: 6, cursor: "pointer", background: s.bg, color: s.color, border: s.border, transition: "opacity .15s" }}
                onMouseEnter={e => e.target.style.opacity = ".8"}
                onMouseLeave={e => e.target.style.opacity = "1"}
              >
                {action.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 0" }}>
      <div style={{ width: 24, height: 24, borderRadius: 6, background: "rgba(29,158,117,.15)", border: "0.5px solid rgba(29,158,117,.3)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <span style={{ fontSize: 10, color: "#34d399" }}>AI</span>
      </div>
      <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
        {[0, 1, 2].map(i => (
          <div key={i} style={{
            width: 5, height: 5, borderRadius: "50%", background: "#34d399",
            animation: `bounce 1s ease-in-out ${i * 0.15}s infinite`,
          }} />
        ))}
        <span style={{ fontSize: 10, color: "rgba(255,255,255,.3)", marginLeft: 6 }}>Analyzing fleet data…</span>
      </div>
    </div>
  );
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────
export default function AIChatAssistant() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSuggested, setShowSuggested] = useState(true);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [isAudioLoading, setIsAudioLoading] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ─── AUDIO UTILITY ──────────────────────────────────────────────────────
  const playAudioFromText = async (text, id = 'manual') => {
    if (!text) return;
    setIsAudioLoading(id);
    try {
      const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:5001";
      const resp = await fetch(`${AI_URL}/api/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      if (!resp.ok) throw new Error("TTS failed");
      const data = await resp.json();
      if (!data.audio_b64) throw new Error(data.error || "No audio returned");
      const binary = atob(data.audio_b64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      const blob = new Blob([bytes], { type: "audio/mpeg" });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => setIsAudioLoading(null);
      await audio.play();
    } catch (err) {
      console.error("Audio Playback Error:", err);
      setIsAudioLoading(null);
    }
  };

  const handleBriefing = async (type) => {
    const prompt = type === 'fleet'
      ? "Give me a very concise 2-sentence fleet status overview for an operational voice briefing."
      : "Summarize the top 2 most urgent critical alerts in 2 short sentences for a voice briefing.";

    setIsAudioLoading(type);
    try {
      const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:5001";
      const resp = await fetch(`${AI_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: prompt, history: [] })
      });
      const data = await resp.json();
      if (data.answer) {
        await playAudioFromText(data.answer, type);
      }
    } catch (err) {
      console.error("Briefing Error:", err);
      setIsAudioLoading(null);
    }
  };

  // Welcome message on mount
  useEffect(() => {
    setMessages([{
      id: "welcome",
      role: "ai",
      text: "",
      time: timeStr(),
      parsed: {
        headline: "Fleet operations center ready",
        summary: `Monitoring ${FLEET.length} drivers. ${FLEET.filter(d => d.status === "En Route").length} en route, ${FLEET.filter(d => d.status === "Available").length} available. ${FLEET.flatMap(d => d.alerts).filter(Boolean).length > 0 ? `⚠ Active alerts detected — ask me for a summary.` : "No active alerts."}`,
        type: "status",
        drivers: [],
        tableRows: [],
        actions: [{ label: "Show active alerts", type: "primary" }, { label: "Fleet summary", type: "secondary" }],
        severity: "normal",
      },
    }]);
  }, []);

  const sendMessage = useCallback(async (text) => {
    const userText = text || input.trim();
    console.log("sendMessage called with:", userText);
    if (!userText || loading) {
      console.log("sendMessage blocked:", { userText, loading });
      return;
    }
    setInput("");
    setShowSuggested(false);

    const userMsg = { id: Date.now(), role: "user", text: userText, time: timeStr() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    const newHistory = [...conversationHistory, { role: "user", content: userText }];

    try {
      const data = await chatService.sendMessage(userText, newHistory);

      const rawAnswer = data.answer || "I'm having trouble retrieving that information.";
      const intentHeadline = data.intent ? data.intent.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : "Chat Response";

      const parsed = {
        headline: intentHeadline,
        summary: rawAnswer,
        type: (data.intent || "").includes('alert') ? 'alert' : 'info',
        severity: "normal",
        drivers: (data.data?.drivers || []).map((d, i) => ({
          id: d.id,
          name: d.name,
          rank: i + 1,
          tag: d.status || "Available",
          tagColor: d.status === "At Risk" ? "amber" : "green",
          note: d.reason || ""
        })),
        tableRows: [],
        actions: (data.suggested_followups || []).map(f => ({ label: f, type: "secondary" }))
      };

      const aiMsg = { id: Date.now() + 1, role: "ai", text: rawAnswer, time: timeStr(), parsed };
      setMessages(prev => [...prev, aiMsg]);
      setConversationHistory([...newHistory, { role: "assistant", content: rawAnswer }]);
    } catch (err) {
      console.error(err);

      const errorMsg = err.message || "Cannot connect to the AI backend. Please ensure the Flask server is running on port 5001.";
      const isConnectionError = errorMsg.includes("Failed to fetch") || errorMsg.includes("Cannot connect");

      const parsed = {
        headline: isConnectionError ? "Backend Offline" : "API Integration Error",
        summary: errorMsg,
        type: "alert",
        severity: isConnectionError ? "warning" : "critical",
        drivers: [],
        tableRows: [],
        actions: []
      };
      setMessages(prev => [...prev, { id: Date.now() + 1, role: "ai", text: "", time: timeStr(), parsed }]);
      setConversationHistory([...newHistory, { role: "assistant", content: JSON.stringify(parsed) }]);
    }
    setLoading(false);
    inputRef.current?.focus();
  }, [input, loading, conversationHistory]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const criticalCount = FLEET.flatMap(d => d.alerts).filter(a => typeof a === "string" && (a.includes("critical") || a.includes("behind"))).length;

  return (
    <div className="flex flex-col h-full gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold tracking-tight">AI Chat Assistant</h2>
        <div className="flex items-center gap-2 text-[11px] text-brand-muted">
          <div className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-pulse" />
          Neural Link: Active
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0 bg-white/[0.02] border border-white/[0.05] rounded-2xl p-6 overflow-hidden relative">

        {/* Voice Dashboard */}
        <div style={{ background: "rgba(29,158,117,.03)", border: "0.5px solid rgba(29,158,117,.15)", borderRadius: 12, padding: "14px", marginBottom: 20, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 28, height: 28, borderRadius: "50%", background: "#1d9e75", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>🎙️</div>
            <div>
              <h4 style={{ margin: 0, fontSize: 12, color: "#f1f5f9" }}>Voice Copilot</h4>
              <p style={{ margin: 0, fontSize: 9, color: "rgba(255,255,255,.3)" }}>Hands-busy briefings</p>
            </div>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <button
              onClick={() => handleBriefing('fleet')}
              disabled={isAudioLoading !== null}
              style={{ background: "rgba(255,255,255,.05)", border: "0.5px solid rgba(255,255,255,.1)", borderRadius: 6, color: "#f1f5f9", fontSize: 9, fontWeight: 600, padding: "5px 10px", cursor: "pointer", transition: "all 0.2s", display: "flex", alignItems: "center", gap: 6 }}
              onMouseEnter={e => e.target.style.background = "rgba(255,255,255,.1)"}
              onMouseLeave={e => e.target.style.background = "rgba(255,255,255,.05)"}
            >
              {isAudioLoading === 'fleet' ? "⌛" : "▶"} Play Fleet Briefing
            </button>
            <button
              onClick={() => handleBriefing('alerts')}
              disabled={isAudioLoading !== null}
              style={{ background: "rgba(248,113,113,.08)", border: "0.5px solid rgba(248,113,113,.15)", borderRadius: 6, color: "#f87171", fontSize: 9, fontWeight: 600, padding: "5px 10px", cursor: "pointer", transition: "all 0.2s", display: "flex", alignItems: "center", gap: 6 }}
              onMouseEnter={e => e.target.style.background = "rgba(248,113,113,.12)"}
              onMouseLeave={e => e.target.style.background = "rgba(248,113,113,.08)"}
            >
              {isAudioLoading === 'alerts' ? "⌛" : "⚠"} Play Critical Alerts
            </button>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "10px 0", display: "flex", flexDirection: "column", gap: 12 }}>

          {messages.map((msg) => (
            <div key={msg.id} className="msg-in" style={{ display: "flex", flexDirection: "column", alignItems: msg.role === "user" ? "flex-end" : "flex-start", gap: 4 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                {msg.role === "ai" && (
                  <div style={{ width: 22, height: 22, borderRadius: 5, background: "rgba(29,158,117,.15)", border: "0.5px solid rgba(29,158,117,.3)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 8, fontWeight: 700, color: "#34d399", letterSpacing: "0.05em" }}>AI</div>
                )}
                <span style={{ fontSize: 9, color: "rgba(255,255,255,.25)" }}>{msg.role === "ai" ? "DispatchIQ" : "You"} · {msg.time}</span>
                {msg.role === "ai" && (
                  <button
                    onClick={() => playAudioFromText(msg.text || (msg.parsed && msg.parsed.summary), msg.id)}
                    disabled={isAudioLoading !== null}
                    style={{ background: "none", border: "none", cursor: "pointer", color: isAudioLoading === msg.id ? "#34d399" : "rgba(255,255,255,.15)", fontSize: 11, padding: 0, marginLeft: 2, display: "flex", alignItems: "center", transition: "color 0.2s" }}
                    title="Speak response"
                  >
                    {isAudioLoading === msg.id ? "⌛" : "🔊"}
                  </button>
                )}
                {msg.role === "user" && (
                  <div style={{ width: 22, height: 22, borderRadius: 5, background: "rgba(255,255,255,.07)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 8, fontWeight: 700, color: "rgba(255,255,255,.5)" }}>ME</div>
                )}
              </div>

              {msg.role === "user" ? (
                <div style={{ maxWidth: "72%", background: "rgba(29,158,117,.12)", border: "0.5px solid rgba(29,158,117,.25)", borderRadius: "10px 10px 2px 10px", padding: "9px 13px", fontSize: 13, color: "rgba(255,255,255,.85)", lineHeight: 1.5 }}>
                  {msg.text}
                </div>
              ) : (
                <div style={{ width: "100%", maxWidth: 680 }}>
                  {msg.parsed ? <AIMessageCard msg={msg} onAction={sendMessage} /> : (
                    <div style={{ fontSize: 12, color: "rgba(255,255,255,.6)", padding: "9px 13px", background: "rgba(255,255,255,.03)", border: "0.5px solid rgba(255,255,255,.08)", borderRadius: 10 }}>{msg.text}</div>
                  )}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="msg-in" style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 4 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 22, height: 22, borderRadius: 5, background: "rgba(29,158,117,.15)", border: "0.5px solid rgba(29,158,117,.3)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 8, fontWeight: 700, color: "#34d399" }}>AI</div>
                <span style={{ fontSize: 9, color: "rgba(255,255,255,.25)" }}>DispatchIQ · {timeStr()}</span>
              </div>
              <TypingIndicator />
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Suggestions */}
        {showSuggested && (
          <div style={{ padding: "0 0 12px 0", flexShrink: 0 }}>
            <div style={{ fontSize: 9, color: "rgba(255,255,255,.25)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 7 }}>Suggested queries</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {SUGGESTED.map((s, i) => (
                <button key={i} className="suggestion-btn" onClick={() => sendMessage(s)}
                  style={{ fontSize: 10, padding: "5px 10px", borderRadius: 6, background: "rgba(255,255,255,.03)", border: "0.5px solid rgba(255,255,255,.1)", color: "rgba(255,255,255,.5)", cursor: "pointer", transition: "all .15s", textAlign: "left" }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div style={{ borderTop: "0.5px solid rgba(255,255,255,.07)", padding: "12px 0", flexShrink: 0, background: "transparent" }}>
          <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
            <div style={{ flex: 1, background: "rgba(255,255,255,.05)", border: `0.5px solid ${loading ? "rgba(29,158,117,.2)" : "rgba(255,255,255,.1)"}`, borderRadius: 10, padding: "10px 14px", transition: "border-color .2s" }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Ask about drivers, loads, delays, HOS, or dispatch recommendations…"
                rows={1}
                disabled={loading}
                style={{ width: "100%", background: "transparent", border: "none", color: "#f1f5f9", fontSize: 13, resize: "none", lineHeight: 1.5, maxHeight: 100, overflowY: "auto", fontFamily: "inherit" }}
                onInput={e => { e.target.style.height = "auto"; e.target.style.height = Math.min(e.target.scrollHeight, 100) + "px"; }}
              />
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 6 }}>
                <span style={{ fontSize: 9, color: "rgba(255,255,255,.2)" }}>Enter to send · Shift+Enter for new line</span>
                <span style={{ fontSize: 9, color: input.length > 400 ? "#f87171" : "rgba(255,255,255,.2)" }}>{input.length}/500</span>
              </div>
            </div>
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              style={{
                width: 42, height: 42, borderRadius: 10, flexShrink: 0,
                background: loading || !input.trim() ? "rgba(255,255,255,.05)" : "#1d9e75",
                border: "none", cursor: loading || !input.trim() ? "not-allowed" : "pointer",
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "all .15s", boxShadow: !loading && input.trim() ? "0 2px 12px rgba(29,158,117,.3)" : "none",
              }}
            >
              {loading ? (
                <div style={{ width: 14, height: 14, border: "1.5px solid rgba(255,255,255,.2)", borderTopColor: "#34d399", borderRadius: "50%", animation: "spin .7s linear infinite" }} />
              ) : (
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M13 8L3 3l2.5 5L3 13l10-5z" fill={input.trim() ? "#000" : "rgba(255,255,255,.25)"} />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}