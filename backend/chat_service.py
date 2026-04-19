from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import sys
import base64
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai.service import process_dispatch_query
from ai.tools.tts import synthesize_speech

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "dispatchiq-chat"}), 200


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    question = data.get('question', '')
    history = data.get('history', [])
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    try:
        response = process_dispatch_query(question, context={"history": history})
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def handle_tts():
    """Shared TTS logic used by both routes."""
    data = request.get_json() or {}
    text = data.get('text', '')
    if not text:
        return jsonify({"error": "No text provided"}), 400
    try:
        result = synthesize_speech(text)
        if result.get("error") and not result.get("audio_b64"):
            return jsonify({"error": result["error"]}), 503
        audio_bytes = base64.b64decode(result["audio_b64"])
        return Response(audio_bytes, mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tts', methods=['POST'])
def tts():
    """Convert a text briefing to speech via ElevenLabs — returns audio/mpeg stream."""
    return handle_tts()


@app.route('/api/voice/tts', methods=['POST'])
def voice_tts():
    """Alias for /api/tts — kept for backwards compatibility."""
    return handle_tts()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)