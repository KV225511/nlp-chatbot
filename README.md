# CosmosBot 🚀 — Voice-Enabled Space & Astronomy Chatbot

A deep learning-powered, voice-enabled chatbot for space and astronomy education. Built with a **CNN + BiGRU + Multi-Head Self-Attention** model for intent classification.

## Features

- 🎤 **Voice Input** — Speak to the bot using Web Speech API
- 🔊 **Voice Output** — Bot reads responses aloud
- 🧠 **Deep Learning** — CNN + BiGRU + Self-Attention architecture
- 📊 **Confidence Scores** — See how confident the bot is
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

- **Frontend**: React 18, Vite, Vanilla CSS (Glassmorphism), Chart.js, jsPDF
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

## Architecture

```
Input → Embedding → [Conv1D(k=2) || Conv1D(k=3) || Conv1D(k=4)] → Concat
→ BiGRU → MultiHeadAttention (4 heads) → GlobalAvgPool → Dense → Softmax
```

## License

MIT
