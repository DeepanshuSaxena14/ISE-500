import sys
import unittest
import json

try:
    from ai.config import config
    from ai.intents import detect_intent
    from ai.service import process_dispatch_query
    from ai.providers.mock_provider import MockFleetProvider
    from ai.tools.llm import generate_text
    from ai.tools.tts import synthesize_speech
    IMPORTS_OK = True
except ImportError as e:
    IMPORTS_OK = False
    IMPORT_ERROR = str(e)

QUESTIONS = [
    "Give me a summary of all active alerts",
    "What’s James Okafor’s current status?",
    "How many drivers are available for dispatch?",
    "Who’s running low on fuel and still en route?",
    "Which driver has the best cost per mile available?",
    "Rank available drivers for a load from Tucson to LA",
    "Who can take a new load from Phoenix to El Paso right now?",
    "Give me a fleet summary"
]

def test_imports():
    print("--- A. Import and Startup Test ---")
    if IMPORTS_OK:
        print("[PASS] All modules imported.")
        print(f"Config default Groq Model: {config.GROQ_MODEL}")
        print(f"Config default ElevenLabs Voice: {config.ELEVENLABS_VOICE_ID}")
    else:
        print(f"[FAIL] Import failed: {IMPORT_ERROR}")

def test_routing():
    print("\n--- B. Intent Routing Test ---")
    if not IMPORTS_OK: return
    for q in QUESTIONS:
        intent = detect_intent(q)
        print(f"Q: {q}")
        print(f"-> Intent: {intent}")

def test_service():
    print("\n--- C. Main Service Test ---")
    if not IMPORTS_OK: return
    for q in QUESTIONS:
        res = process_dispatch_query(q)
        print(f"Q: {q}")
        print(f"Intent: {res.get('intent')}")
        print(f"Answer: {res.get('answer')}")
        print("-" * 20)

def test_provider():
    print("\n--- D. Mock Provider Test ---")
    if not IMPORTS_OK: return
    p = MockFleetProvider()
    print(f"Total Drivers: {len(p.drivers)}")
    js = p.get_driver_status("James Okafor")
    print(f"Status for James Okafor: {bool(js)}")

def test_tools():
    print("\n--- F/G. Tools Test ---")
    if not IMPORTS_OK: return
    print(f"Generate text fallback check: {generate_text('hello')}")
    print(f"TTS fallback check: {synthesize_speech('hello')}")

if __name__ == '__main__':
    test_imports()
    test_routing()
    test_service()
    test_provider()
    test_tools()
