import requests
from ..config import config

def synthesize_speech(text: str) -> bytes:
    """
    Converts text to speech via ElevenLabs. Returns binary audio data.
    """
    if not config.ELEVENLABS_API_KEY:
        print("ElevenLabs Error: API Key missing.")
        return None
    
    voice_id = config.ELEVENLABS_VOICE_ID or "21m00Tcm4TlvDq8ikWAM" # Default to Rachel
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": config.ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=15)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"ElevenLabs API Error: {e}")
        return None
