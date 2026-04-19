# DispatchIQ — AI-Powered Fleet Operations Platform

> **GlobeHack @ ASU · ISE-500 Team**

DispatchIQ is a real-time fleet management platform that helps trucking dispatchers make faster, smarter decisions using AI. It combines live driver data, AI-powered chat, voice briefings, and smart load dispatch recommendations in a single operations dashboard.

**Live Demo:** https://dispatchiq-steel.vercel.app

---

## What It Does

- **Fleet Dashboard** — Real-time driver cards showing location, HOS, fuel, load progress, and performance alerts
- **AI Chat Assistant** — Ask natural language questions about your fleet ("Who can take a load from Phoenix to Dallas right now?") and get structured, ranked answers
- **Voice Copilot** — Hands-free audio briefings powered by ElevenLabs TTS — play a fleet status summary or critical alerts while on the move
- **Smart Dispatch** — AI-ranked driver recommendations for any new load based on HOS, location, fuel, and cost-per-mile
- **Alerts** — Automated flagging of HOS violations, out-of-route ratios, fuel warnings, and schedule delays

---

## Architecture

```
┌─────────────────────────────────────┐
│         Vercel (Frontend)           │
│      React + TypeScript + Vite      │
│      dispatchiq-steel.vercel.app    │
└────────────┬────────────┬───────────┘
             │            │
             ▼            ▼
┌────────────────┐  ┌─────────────────────┐
│  Fleet API     │  │   AI Chat Service   │
│  Flask/Python  │  │   Flask/Python      │
│  Port 8000     │  │   Port 5001         │
│  Railway       │  │   Railway           │
└────────┬───────┘  └──────────┬──────────┘
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌────────────────────┐
│    Supabase     │   │   Groq (LLM)       │
│  PostgreSQL DB  │   │   ElevenLabs (TTS) │
│   50 drivers    │   │   LangChain        │
└─────────────────┘   └────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, JavaScript, Tailwind CSS, Vite |
| Ops Backend | Flask (Python), Supabase, PostgreSQL |
| AI Backend | Flask (Python), Groq (llama-3.1-8b-instant), LangChain |
| Voice | ElevenLabs TTS API |
| Database | Supabase (PostgreSQL) — 50 seeded drivers |
| Frontend Deploy | Vercel |
| Backend Deploy | Railway (2 services) |
| CI/CD | GitHub Actions |

---

## Project Structure

```
ISE-500/
├── frontend/                    # React app
│   ├── src/
│   │   ├── pages/
│   │   │   ├── FleetDashboard.jsx      # Live driver cards
│   │   │   ├── AIChatAssistant.jsx     # AI chat + voice copilot
│   │   │   ├── SmartDispatch.jsx       # AI dispatch recommendations
│   │   │   ├── Alerts.jsx              # Fleet alerts
│   │   │   └── Briefings.jsx           # Ops briefing page
│   │   ├── api/
│   │   │   └── index.js                # API calls to both backends
│   │   └── components/                 # Shared UI components
│   ├── .env.example                    # Environment variable template
│   └── vite.config.js
│
├── backend/                     # Python backends
│   ├── app.py                          # Fleet ops API (port 8000)
│   ├── chat_service.py                 # AI chat + TTS API (port 5001)
│   ├── ai/
│   │   ├── service.py                  # LangChain dispatch query processor
│   │   ├── config.py                   # Environment config
│   │   ├── handlers/                   # Intent handlers (alerts, dispatch, etc.)
│   │   ├── providers/                  # Fleet data providers (API + mock)
│   │   └── tools/
│   │       ├── llm.py                  # Groq LLM wrapper
│   │       └── tts.py                  # ElevenLabs TTS
│   ├── data/
│   │   ├── seed_data.py                # Seeds 50 drivers into Supabase
│   │   └── schema.sql                  # Database schema
│   ├── requirements.txt
│   ├── Dockerfile                      # For Fleet API service
│   └── Dockerfile.chat                 # For AI Chat service
│
└── .github/workflows/
    ├── deploy-frontend.yml             # Vercel auto-deploy
    └── deploy-backend.yml             # Railway deploy (manual trigger)
```

---

## Running Locally

### Prerequisites

- Node.js 18+
- Python 3.12+
- A Supabase account
- A Groq API key (free at console.groq.com)
- An ElevenLabs API key (free tier available)

### 1. Clone the repo

```bash
git clone https://github.com/DeepanshuSaxena14/ISE-500.git
cd ISE-500
```

### 2. Set up the backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
BACKEND_BASE_URL=http://localhost:8000
```

Seed the database (first time only):

```bash
python data/seed_data.py
```

Start the Fleet API:

```bash
python app.py
# Runs on http://localhost:8000
```

In a separate terminal, start the AI Chat service:

```bash
python chat_service.py
# Runs on http://localhost:5001
```

### 3. Set up the frontend

```bash
cd frontend
npm install
```

Create a `.env.local` file in the `frontend/` directory:

```env
VITE_API_URL=http://localhost:8000
VITE_AI_URL=http://localhost:5001
```

Start the frontend:

```bash
npm run dev
# Opens at http://localhost:5173
```

---

## API Reference

### Fleet API (port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/health/db` | GET | Database connection check |
| `/driver-cards` | GET | All driver cards with alerts and performance |
| `/loads` | GET | All loads |
| `/loads/<id>/recommendations` | GET | AI dispatch recommendations for a load |

### AI Chat API (port 5001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/chat` | POST | Send a fleet question, get structured AI response |
| `/api/tts` | POST | Convert text to speech (returns audio/mpeg) |
| `/api/voice/tts` | POST | Alias for `/api/tts` |

**Example chat request:**
```bash
curl -X POST https://dynamic-analysis-production-9e03.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Which drivers are available for dispatch?", "history": []}'
```

---

## Deployment

### Live URLs

| Service | URL |
|---------|-----|
| Frontend | https://dispatchiq-steel.vercel.app |
| Fleet API | https://ise-500-production.up.railway.app |
| AI Chat | https://dynamic-analysis-production-9e03.up.railway.app |

### Environment Variables Required

**Railway — Fleet API (ISE-500):**
```
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
GROQ_API_KEY
GROQ_MODEL
ELEVENLABS_API_KEY
ELEVENLABS_VOICE_ID
PORT=8000
```

**Railway — AI Chat (dynamic-analysis):**
```
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
GROQ_API_KEY
GROQ_MODEL
ELEVENLABS_API_KEY
ELEVENLABS_VOICE_ID
PORT=5001
BACKEND_BASE_URL=https://ise-500-production.up.railway.app
```

**Vercel — Frontend:**
```
VITE_API_URL=https://ise-500-production.up.railway.app
VITE_AI_URL=https://dynamic-analysis-production-9e03.up.railway.app
```

### Auto-Deploy

- **Frontend** — pushes to `main` auto-deploy via Vercel Git integration
- **Backend** — pushes to `main` auto-deploy via Railway Git integration

---

## AI Features

### 1. Intent-Based Dispatch Query
The AI chat system uses LangChain to classify questions into intents (fleet summary, driver status, alerts, dispatch ranking) and routes them to specialized handlers that pull live data from Supabase.

### 2. Provider-Agnostic Fleet Data
The `FleetProvider` abstraction (`api_provider.py` / `mock_provider.py`) allows the AI layer to work with real Supabase data in production and mock data in development — zero code changes needed to switch.

### 3. Voice Copilot
The Voice Copilot first calls `/api/chat` to generate a concise 2-sentence briefing using Groq, then pipes that text to ElevenLabs TTS via `/api/tts`, and streams the audio directly to the browser.

---

### Screenshots
![alt text](/images/image.png)

![alt text](/images/image-1.png)

![alt text](/images/image-2.png)

![alt text](/images/image-3.png)

![alt text](/images/image-4.png)

![alt text](/images/image-5.png)