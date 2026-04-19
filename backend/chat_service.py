from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv, find_dotenv

# Load environment variables from the root .env file
load_dotenv(find_dotenv())


# Add the current directory to sys.path so we can import 'ai'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai.service import process_dispatch_query

app = Flask(__name__)
# Enable CORS for all routes (to allow frontend on port 5173 to reach backend on port 5000)
CORS(app)

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

if __name__ == '__main__':
    # Run the server on port 5001
    app.run(port=5001, debug=True)

