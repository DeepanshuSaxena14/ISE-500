from ..config import config

def synthesize_speech(text: str) -> str:
    """
    Converts text to speech via ElevenLabs. Returns a URL or binary data.
    """
    if not config.ELEVENLABS_API_KEY:
        return ""
    
    # In a real implementation we would call elevenlabs api
    return "http://mock-tts-url-for-audio.mp3"
