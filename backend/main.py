"""
DispatchIQ — FastAPI Backend
Run: uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import AsyncGenerator

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

load_dotenv()

app = FastAPI(title="DispatchIQ API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Supabase client ──────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

# ── LLM clients ─────────────────────────────────────────────────────────────
GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ELEVENLABS_KEY    = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE  = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # default: Bella

# ── Pydantic models ──────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str          # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    fleet_context: dict | None = None  # optional override; backend pulls live data if absent

class DispatchRecommendRequest(BaseModel):
    load_id: str
    candidate_driver_ids: list[str] | None = None  # if None, consider all available

class BriefingRequest(BaseModel):
    date: str | None = None   # ISO date string, defaults to today

# ── Helpers ──────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fleet_snapshot() -> dict:
    """Pull live fleet state from Supabase (falls back to mock data if DB unavailable)."""
    if supabase:
        try:
            drivers = supabase.table("drivers").select("*, loads(*)").execute().data
            alerts  = supabase.table("alerts").select("*").eq("is_resolved", False).execute().data
            return {"drivers": drivers, "alerts": alerts, "generated_at": _now_iso()}
        except Exception:
            pass
    # Fallback — mock snapshot (mirrors the 8-driver dataset)
    from mock_data import MOCK_FLEET_SNAPSHOT
    return MOCK_FLEET_SNAPSHOT


async def _groq_chat(messages: list[dict], system: str) -> str:
    """Call Groq llama-3.3-70b for real-time chat."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system}, *messages],
                "temperature": 0.3,
                "max_tokens": 1024,
                "response_format": {"type": "json_object"},
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _claude_complete(prompt: str) -> str:
    """Call Claude claude-sonnet-4 for high-quality structured output (briefings)."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


async def _elevenlabs_tts(text: str) -> bytes:
    """Convert text to speech via ElevenLabs. Returns raw MP3 bytes."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE}",
            headers={"xi-api-key": ELEVENLABS_KEY},
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
        )
        resp.raise_for_status()
        return resp.content


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": _now_iso()}


# ── /fleet ───────────────────────────────────────────────────────────────────

@app.get("/fleet")
async def get_fleet():
    """Return current fleet snapshot (drivers + active loads + open alerts)."""
    return _fleet_snapshot()


@app.get("/fleet/drivers/{driver_id}")
async def get_driver(driver_id: str):
    if supabase:
        row = supabase.table("drivers").select("*, loads(*)").eq("id", driver_id).single().execute()
        if row.data:
            return row.data
    raise HTTPException(status_code=404, detail="Driver not found")


# ── /alerts ──────────────────────────────────────────────────────────────────

@app.get("/alerts")
async def get_alerts(resolved: bool = False):
    """Return all open (or resolved) alerts sorted by severity then time."""
    if supabase:
        q = supabase.table("alerts").select("*").eq("is_resolved", resolved)
        return q.order("created_at", desc=True).execute().data
    # fallback
    from mock_data import MOCK_ALERTS
    return MOCK_ALERTS


@app.patch("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int):
    if supabase:
        supabase.table("alerts").update(
            {"is_resolved": True, "resolved_at": _now_iso()}
        ).eq("id", alert_id).execute()
    return {"status": "resolved", "alert_id": alert_id}


# ── /dispatch/recommend ──────────────────────────────────────────────────────

@app.post("/dispatch/recommend")
async def dispatch_recommend(req: DispatchRecommendRequest):
    """
    Uses Groq to rank available drivers for a given load.
    Returns a JSON array of {driver_id, score, reasoning}.
    """
    fleet = _fleet_snapshot()

    # Filter candidates
    drivers = [
        d for d in fleet["drivers"]
        if d["status"] in ("available", "on_break")
        and (req.candidate_driver_ids is None or d["id"] in req.candidate_driver_ids)
    ]

    if not drivers:
        raise HTTPException(status_code=404, detail="No available drivers found")

    # Find the load
    load_info = {}
    if supabase:
        row = supabase.table("loads").select("*").eq("id", req.load_id).single().execute()
        load_info = row.data or {}

    system_prompt = """You are DispatchIQ, an AI dispatch assistant for a trucking fleet.
You must respond ONLY with valid JSON — no markdown, no prose.
Format: {"ranked_drivers": [{"driver_id": "...", "score": 0-100, "reasoning": "..."}]}
Score based on: HOS hours remaining (most important), fuel level, CPM cost, on-time rate, proximity."""

    user_content = f"""
Load to dispatch: {json.dumps(load_info)}

Available drivers:
{json.dumps(drivers, indent=2)}

Rank these drivers for this load. Return top results sorted by score descending.
"""
    raw = await _groq_chat(
        messages=[{"role": "user", "content": user_content}],
        system=system_prompt,
    )
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"ranked_drivers": [], "error": "Failed to parse AI response", "raw": raw}

    return result


@app.post("/dispatch/confirm/{load_id}/{driver_id}")
async def dispatch_confirm(load_id: str, driver_id: str):
    """Assign a driver to a load — updates both tables."""
    if supabase:
        supabase.table("loads").update(
            {"driver_id": driver_id, "status": "assigned"}
        ).eq("id", load_id).execute()
        supabase.table("drivers").update(
            {"current_load_id": load_id, "status": "en_route"}
        ).eq("id", driver_id).execute()
    return {"status": "dispatched", "load_id": load_id, "driver_id": driver_id, "timestamp": _now_iso()}


# ── /chat ────────────────────────────────────────────────────────────────────

@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Multi-turn NL chat with Groq. Fleet context is injected as system prompt.
    Expects messages in [{role, content}] format.
    Returns structured JSON parsed into UI components by the frontend.
    """
    fleet = req.fleet_context or _fleet_snapshot()

    system_prompt = f"""You are DispatchIQ, an AI assistant for fleet dispatchers.
You have real-time access to the fleet. Always respond ONLY with valid JSON.
Format:
{{
  "headline": "short summary",
  "summary": "one paragraph",
  "severity": "normal|warning|critical",
  "drivers": [
    {{"id": "...", "name": "...", "status": "...", "highlight": "why they matter"}}
  ],
  "table": {{"headers": [...], "rows": [[...]]}},  // optional
  "actions": [{{"label": "...", "action": "...", "payload": {{}}}}]  // optional
}}

Current fleet snapshot:
{json.dumps(fleet, indent=2)}

Today: {_now_iso()}
"""
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    raw = await _groq_chat(messages=messages, system=system_prompt)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"headline": "Response error", "summary": raw, "severity": "warning", "drivers": [], "actions": []}


# ── /briefing/generate ───────────────────────────────────────────────────────

@app.post("/briefing/generate")
async def briefing_generate(req: BriefingRequest):
    """
    Generates a daily fleet briefing using Claude.
    Optionally synthesizes audio via ElevenLabs.
    """
    fleet = _fleet_snapshot()
    date_str = req.date or datetime.now(timezone.utc).strftime("%A, %B %-d, %Y")

    prompt = f"""You are DispatchIQ's briefing narrator. Generate a concise morning briefing for a fleet dispatcher.
Cover: active loads & ETAs, HOS warnings, fuel alerts, cost highlights.
Keep it under 250 words. Use natural spoken language (no bullet points — this will be read aloud).
End with 1–2 recommended priority actions.

Date: {date_str}
Fleet data:
{json.dumps(fleet, indent=2)}
"""
    briefing_text = await _claude_complete(prompt)

    # Optionally generate TTS
    audio_url = None
    if ELEVENLABS_KEY:
        try:
            audio_bytes = await _elevenlabs_tts(briefing_text)
            # In production: upload audio_bytes to Supabase Storage and return the URL.
            # For hackathon: return base64 so frontend can play inline.
            import base64
            audio_url = f"data:audio/mpeg;base64,{base64.b64encode(audio_bytes).decode()}"
        except Exception as e:
            audio_url = None

    # Persist briefing
    if supabase:
        supabase.table("briefings").insert({
            "fleet_snapshot": fleet,
            "summary_text": briefing_text,
            "voice_audio_url": audio_url,
            "generated_at": _now_iso(),
        }).execute()

    return {
        "text": briefing_text,
        "audio_url": audio_url,
        "generated_at": _now_iso(),
    }


# ── WebSocket — live fleet updates ───────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)


manager = ConnectionManager()


@app.websocket("/ws/fleet")
async def ws_fleet(websocket: WebSocket):
    """
    Streams fleet state updates every 5 seconds.
    In production this would listen to Trucker Path NavPro webhook events.
    For the hackathon it uses the mock data generator.
    """
    await manager.connect(websocket)
    try:
        from mock_data import fleet_event_generator
        async for event in fleet_event_generator():
            await websocket.send_json(event)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)