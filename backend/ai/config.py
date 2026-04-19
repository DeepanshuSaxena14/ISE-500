import os

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "dummy_groq_key")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:5000/api")

config = Config()
