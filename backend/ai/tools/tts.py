import base64
import io
import requests

from ..config import config

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

def synthesize_speech(text: str) -> dict:
    """
    Converts text to speech via ElevenLabs API.
    Returns dict with 'audio_b64' (base64 MP3) and 'content_type'.
    Falls back gracefully if API key missing or call fails.
    """
    if not config.ELEVENLABS_API_KEY:
        print("[tts] No ELEVENLABS_API_KEY configured — skipping TTS")
        return {"audio_b64": None, "content_type": None, "error": "No API key"}

    voice_id = getattr(config, "ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    url = ELEVENLABS_TTS_URL.format(voice_id=voice_id)

    headers = {
        "xi-api-key": config.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text[:2500],  # stay well under 10k char/month limit
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        audio_b64 = base64.b64encode(resp.content).decode("utf-8")
        return {"audio_b64": audio_b64, "content_type": "audio/mpeg", "error": None}
    except requests.exceptions.HTTPError as e:
        print(f"[tts] ElevenLabs HTTP error: {e.response.status_code} — {e.response.text[:200]}")
        return {"audio_b64": None, "content_type": None, "error": str(e)}
    except Exception as e:
        print(f"[tts] ElevenLabs unexpected error: {e}")
        return {"audio_b64": None, "content_type": None, "error": str(e)}