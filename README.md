# CosmosBot 🚀 — Voice-Enabled Space & Astronomy Chatbot

A deep learning-powered, voice-enabled chatbot for space and astronomy education. Built with a **CNN + BiGRU + Multi-Head Self-Attention** model for intent classification.

## Features

- 🎤 **Voice Input** — Speak to the bot using Web Speech API
- 🔊 **Voice Output** — Bot reads responses aloud
- 🧠 **Deep Learning** — CNN + BiGRU + Self-Attention architecture
- 📊 **Match Scores** — See how closely a question matched the knowledge base
- 🌍 **Space-only Web Search** — Space questions outside the dataset are answered from Wikipedia, with a source link; non-space questions are politely refused
- 😊 **Sentiment Analysis** — Real-time mood detection
- 📈 **Mood Dashboard** — Track sentiment over conversation
- 💬 **Quick Reply Chips** — Contextual suggestion buttons
- 🧘 **Breathing Exercise** — Space-themed guided breathing
- 🌙 **Dark/Light Mode** — Theme toggle
- 🌐 **Multi-Language** — 10+ language support
- 📄 **PDF Export** — Download conversation history
- 🔔 **Sound Effects** — Synthesized audio feedback
- 📱 **Responsive** — Works on all devices

## Tech Stack

- **Frontend**: React 19, Vite, Vanilla CSS (Glassmorphism), Chart.js, jsPDF
- **Web Search**: Wikipedia REST API + DuckDuckGo Instant Answer API (no API key needed)
- **Backend**: Python Flask, Gunicorn
- **ML/DL**: TensorFlow/Keras (CNN + BiGRU + Multi-Head Self-Attention)
- **NLP**: NLTK, VADER Sentiment, Googletrans
- **Speech**: Web Speech API (STT & TTS browser-native)
- **Audio**: Web Audio API procedural synthesis

## Setup & Running

### 1. Backend Setup
```bash
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
python model/train.py
python backend/app.py
```

### 2. Frontend Development (React)
```bash
cd frontend
npm install
npm run dev      # Runs Vite dev server with proxy to backend at localhost:5173
npm run build    # Builds production React bundle to frontend/dist
```
When running `python backend/app.py`, Flask automatically serves the production React build from `frontend/dist` on `http://localhost:5000`!

### 3. Smoke Test
```bash
python tests/smoke_test.py   # needs internet for the web search checks
```

### Configuration
| Variable | Default | Meaning |
|---|---|---|
| `WEB_SEARCH_ENABLED` | `true` | Set to `false` to disable the web search fallback |
| `WEB_SEARCH_TIMEOUT` | `6` | Seconds per web request |

## Architecture

```
Input → Embedding → [Conv1D(k=2) || Conv1D(k=3) || Conv1D(k=4)] → Concat
→ BiGRU (masked) → MultiHeadAttention (4 heads, masked) → Masked GlobalAvgPool → Dense → Softmax
```

**Answer routing:** the network's intent must agree with a TF-IDF nearest-pattern match
(similarity ≥ 0.65) for a knowledge-base answer. Otherwise CosmosBot searches Wikipedia
(then DuckDuckGo). The result is used only if it is about space or astronomy (keyword check); then it answers with a
source link. Non-space topics get an "outside my orbit" reply.

## License

MIT
