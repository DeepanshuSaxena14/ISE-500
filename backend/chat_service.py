from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv, find_dotenv

# Load environment variables from the root .env file
load_dotenv(find_dotenv())

# Add the current directory to sys.path so we can import 'ai'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai.service import process_dispatch_query
from ai.tools.tts import synthesize_speech

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    question = data.get('question', '')
    history = data.get('history', [])
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    try:
        # Resolve the query using the LLM-driven dispatch service
        response = process_dispatch_query(question, context={"history": history})
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/voice/tts', methods=['POST'])
def tts():
    data = request.get_json() or {}
    text = data.get('text', '')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
        
    try:
        audio_content = synthesize_speech(text)
        if not audio_content:
            return jsonify({"error": "Failed to synthesize speech"}), 500
            
        return Response(audio_content, mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run the server on port 5001 to avoid conflicts with app.py on port 8000
    app.run(host="0.0.0.0", port=5001, debug=True)
