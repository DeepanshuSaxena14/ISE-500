# DispatchIQ (ISE-500)

DispatchIQ is an AI-powered fleet operations assistant designed specifically for small trucking fleets. It acts as a copilot, combining a React frontend with a LangChain + LLM (Llama 3.1) backend to dynamically manage drivers, calculate route risks, and handle conversational analytics.

---

## Prerequisites
Before you start, make sure you have the following installed on your machine:
- **Node.js** (v16 or higher)
- **Python** (v3.9 or higher)

## 1. Project Setup
Clone this repository to your local machine, then follow these steps carefully to set up both environments.

### Setting up the Environment Variables
Before running the server, you need API keys to power the AI logic.

1. Create a file named exactly **`.env`** in the ROOT directory of this project (`ISE-500/.env`).
2. Copy the contents of the `.env.example` file (or paste the following) into your new `.env` file:
```env
# ─── GROQ SETTINGS (LLM) ───
GROQ_API_KEY="your_groq_api_key_here"
GROQ_MODEL="llama-3.1-8b-instant"

# ─── BACKEND SETTINGS ───
BACKEND_BASE_URL="http://localhost:5001/api"
```
3. Replace `"your_groq_api_key_here"` with a valid Groq API Key.

---

## 2. Installation & Running

The project runs on two separate servers: a Python backend and a React/Vite frontend. You will need **two terminal windows** open.

### Terminal 1: Run the AI Backend
This terminal runs the Flask server on port `5001`.
```bash
# Enter the backend directory
cd backend

# Create a virtual environment (only needed the very first time)
python -m venv venv

# Activate the virtual environment
# Mac/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Install the required Python packages
pip install -r requirements.txt

# Start the Flask web server
python app.py
```

### Terminal 2: Run the Web Frontend
This terminal builds the User Interface on port `5173`. Open a new tab in your terminal and run:
```bash
# Enter the frontend directory
cd frontend

# Install the Node dependencies
npm install

# Start the Vite development server
npm run dev
```

---

## 3. Usage
Once both servers are running:
1. Open your browser and navigate to `http://localhost:5173`.
2. Open the Chat Assistant interface.
3. Test the Natural Language Understanding (NLU) by typing conversational or complex questions about the fleet, such as:
   - *"Are any drivers running dangerously low on fuel?"*
   - *"Find me the cheapest driver to take my load."*
   - *"What is James's current ETA?"*

The AI will dynamically map your unstructured question to the underlying operational data endpoints!