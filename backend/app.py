"""
Flask application for CosmosBot — Voice-Enabled Space & Astronomy Chatbot.

Serves the frontend and provides REST API endpoints for:
- Chat (intent prediction + response)
- Sentiment analysis
- Mood tracking history
- Translation
- Health checks
"""

import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import uuid

# Add project root to sys.path so 'backend' package is resolvable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Import backend modules
from backend.chatbot_engine import ChatbotEngine
from backend.sentiment_analyzer import SentimentAnalyzer
from backend.context_manager import ContextManager
from backend.translation_service import TranslationService
from backend.web_search import WebSearchService


# ============================================
# Initialize Flask App
# ============================================
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dist_folder = os.path.join(base_dir, 'frontend', 'dist')
static_folder = dist_folder if os.path.exists(dist_folder) else os.path.join(base_dir, 'frontend')

app = Flask(
    __name__,
    static_folder=static_folder,
    static_url_path=''
)
# ============================================
# CORS Configuration
# ============================================
# Support specific frontend URLs (e.g. Vercel deployment) or allow all by default
allowed_origins_raw = os.environ.get('CORS_ORIGINS', os.environ.get('FRONTEND_URL', '*'))
if allowed_origins_raw.strip() == '*':
    cors_origins = '*'
else:
    cors_origins = [o.strip() for o in allowed_origins_raw.split(',') if o.strip()]

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Accept", "X-Requested-With"]
        }
    }
)


@app.after_request
def apply_cors_headers(response):
    """Ensure CORS headers are always attached to API responses, including errors."""
    if request.path.startswith('/api/'):
        origin = request.headers.get('Origin')
        if cors_origins == '*':
            response.headers['Access-Control-Allow-Origin'] = '*'
        elif origin and (origin in cors_origins or '*' in cors_origins):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Vary'] = 'Origin'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept, X-Requested-With'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

# ============================================
# Initialize Backend Services
# ============================================
print("🚀 Initializing CosmosBot services...")

chatbot = ChatbotEngine()
sentiment = SentimentAnalyzer()
context = ContextManager()
translator = TranslationService()
web_search = WebSearchService()

print("✅ All services initialized!")


def build_web_prediction(web_result):
    """Turn a web search result into the same shape as a model prediction."""
    return {
        'intent': 'web_search',
        'response': (
            f"I didn't have that in my space database, so I searched {web_result['provider']}: "
            f"{web_result['answer']}"
        ),
        'confidence': None,
        'suggestions': [f"More about {web_result['title']}", 'Fun space facts', 'Solar system facts'],
        'top_predictions': [],
        'is_fallback': False,
        'sources': [{'title': web_result['title'], 'url': web_result['url'], 'provider': web_result['provider']}]
    }


# ============================================
# Frontend Routes (React SPA Serving)
# ============================================

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve React frontend and assets with SPA fallback."""
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')



# ============================================
# API Routes
# ============================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint.
    
    Request Body:
        {
            "message": "Tell me about black holes",
            "session_id": "uuid-string" (optional),
            "language": "en" (optional, default "en")
        }
    
    Response:
        {
            "intent": "black_holes",
            "response": "Black holes are...",
            "confidence": 0.94,
            "sentiment": { "compound": 0.2, "label": "positive", "emoji": "😊" },
            "suggestions": [...],
            "context_suggestions": [...],
            "mood_history": [...],
            "is_fallback": false,
            "trigger_breathing": false,
            "source": "knowledge_base" | "web" | "off_topic" | "fallback",
            "sources": [{ "title": "...", "url": "...", "provider": "Wikipedia" }]
        }
    """
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Missing "message" field'}), 400
    
    message = data['message'].strip()
    session_id = data.get('session_id', str(uuid.uuid4()))
    language = data.get('language', 'en')
    
    if not message:
        return jsonify({'error': 'Empty message'}), 400
    
    # Step 1: Translate to English if needed
    original_message = message
    if language != 'en':
        translation_result = translator.translate_to_english(message, source_lang=language)
        message = translation_result['translated_text']
    
    # Step 2: Analyze sentiment of original message
    sentiment_result = sentiment.analyze(original_message)
    
    # Step 3: Predict intent and get response
    prediction = chatbot.predict_intent(message)
    source = 'knowledge_base'

    # Step 3b: Not covered by the dataset -> search the web
    if not prediction['is_known']:
        web_result = web_search.search(message)
        if web_result and web_result.get('off_topic'):
            # Something was found online, but it is not about space: stay on topic
            if prediction['is_fallback'] or not prediction['is_weak_match']:
                prediction = chatbot.off_topic_response()
                source = 'off_topic'
        elif web_result:
            prediction = build_web_prediction(web_result)
            source = 'web'
        elif prediction['is_fallback']:
            source = 'fallback'
    
    # Step 4: Track context
    context.add_message(session_id, 'user', original_message, 
                       intent=None, sentiment=sentiment_result)
    context.add_message(session_id, 'bot', prediction['response'],
                       intent=prediction['intent'])
    
    # Step 5: Get context-aware follow-up suggestions
    context_suggestions = context.get_context_suggestions(
        session_id, prediction['intent']
    )
    
    # Step 6: Get mood history
    mood_history = context.get_mood_history(session_id)
    
    # Step 7: Translate response back if needed
    response_text = prediction['response']
    if language != 'en':
        response_text = translator.translate_from_english(response_text, language)
    
    # Step 8: Check if breathing exercise should be triggered
    trigger_breathing = prediction['intent'] == 'breathing_exercise'
    
    return jsonify({
        'intent': prediction['intent'],
        'response': response_text,
        'confidence': prediction['confidence'],
        'sentiment': sentiment_result,
        'suggestions': prediction['suggestions'],
        'context_suggestions': context_suggestions,
        'mood_history': mood_history,
        'top_predictions': prediction.get('top_predictions', []),
        'is_fallback': prediction['is_fallback'],
        'trigger_breathing': trigger_breathing,
        'session_id': session_id,
        'source': source,
        'sources': prediction.get('sources', [])
    })


@app.route('/api/mood-history', methods=['GET'])
def mood_history():
    """Get mood tracking data for a session."""
    session_id = request.args.get('session_id', '')
    
    if not session_id:
        return jsonify({'mood_history': []})
    
    history = context.get_mood_history(session_id)
    return jsonify({'mood_history': history})


@app.route('/api/languages', methods=['GET'])
def supported_languages():
    """Get list of supported languages."""
    return jsonify({
        'languages': translator.get_supported_languages()
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment monitoring."""
    return jsonify({
        'status': 'healthy',
        'service': 'CosmosBot',
        'version': '1.0.0',
        'model_loaded': chatbot.model is not None,
        'web_search_enabled': web_search.enabled
    })


@app.route('/api/intents', methods=['GET'])
def list_intents():
    """List all available intents (for debugging)."""
    return jsonify({
        'intents': chatbot.get_intent_list(),
        'count': len(chatbot.get_intent_list())
    })


# ============================================
# Error Handlers
# ============================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================
# Run Server
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"\n🌌 CosmosBot is launching on port {port}...")
    print(f"🔗 Open http://localhost:{port} in your browser")
    print(f"🎤 Use Chrome or Edge for voice input support\n")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
