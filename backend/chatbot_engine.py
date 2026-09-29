"""
Core chatbot engine for CosmosBot.
Loads the trained model and handles predictions with confidence scoring.
"""

import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import pickle
import random
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Import preprocessing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.preprocessing import clean_text


class ChatbotEngine:
    """
    Main chatbot engine that handles:
    - Model loading
    - Text preprocessing
    - Intent prediction
    - Response selection
    - Confidence thresholding
    """
    
    def __init__(self, model_dir=None, intents_path=None):
        """
        Initialize the chatbot engine by loading all artifacts.
        
        Args:
            model_dir: Path to directory containing model artifacts
            intents_path: Path to intents.json
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if model_dir is None:
            model_dir = os.path.join(base_dir, 'model')
        if intents_path is None:
            intents_path = os.path.join(base_dir, 'data', 'intents.json')
        
        # Load model
        model_path = os.path.join(model_dir, 'chatbot_model.keras')
        print(f"Loading model from: {model_path}")
        self.model = load_model(model_path)
        
        # Load tokenizer
        tokenizer_path = os.path.join(model_dir, 'tokenizer.pickle')
        with open(tokenizer_path, 'rb') as f:
            self.tokenizer = pickle.load(f)
        
        # Load label encoder
        encoder_path = os.path.join(model_dir, 'label_encoder.pickle')
        with open(encoder_path, 'rb') as f:
            self.label_encoder = pickle.load(f)
        
        # Load model config
        config_path = os.path.join(model_dir, 'model_config.json')
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.max_len = self.config['max_len']
        
        # Load intents data
        with open(intents_path, 'r', encoding='utf-8') as f:
            self.intents_data = json.load(f)
        
        # Build intent lookup dict
        self.intent_map = {}
        for intent in self.intents_data['intents']:
            self.intent_map[intent['tag']] = intent
        
        # Confidence threshold
        self.confidence_threshold = 0.30
        
        print(f"✅ ChatbotEngine loaded successfully!")
        print(f"   Model: {self.config.get('num_classes', '?')} intents, vocab_size={self.config.get('vocab_size', '?')}")
    
    def predict_intent(self, text):
        """
        Predict the intent of a given text input.
        
        Args:
            text: User's input text
            
        Returns:
            dict with keys: intent, response, confidence, suggestions, all_probs
        """
        # Preprocess text
        cleaned = clean_text(text)
        
        if not cleaned.strip():
            return self._fallback_response()
        
        # Convert to sequence
        seq = self.tokenizer.texts_to_sequences([cleaned])
        padded = pad_sequences(seq, maxlen=self.max_len, padding='post', truncating='post')
        
        # Predict
        pred = self.model.predict(padded, verbose=0)[0]
        
        # Get top prediction
        intent_idx = np.argmax(pred)
        confidence = float(pred[intent_idx])
        
        # Get top 3 predictions for debugging/display
        top3_idx = np.argsort(pred)[-3:][::-1]
        top3 = [
            {
                'intent': self.label_encoder.inverse_transform([idx])[0],
                'confidence': float(pred[idx])
            }
            for idx in top3_idx
        ]
        
        # Check confidence threshold
        if confidence < self.confidence_threshold:
            result = self._fallback_response()
            result['top_predictions'] = top3
            return result
        
        # Get intent tag
        intent_tag = self.label_encoder.inverse_transform([intent_idx])[0]
        
        # Get intent data
        intent_data = self.intent_map.get(intent_tag, None)
        
        if intent_data is None:
            return self._fallback_response()
        
        # Select random response
        response = random.choice(intent_data['responses'])
        
        # Get suggestions
        suggestions = intent_data.get('suggestions', [])
        
        return {
            'intent': intent_tag,
            'response': response,
            'confidence': round(confidence, 4),
            'suggestions': suggestions,
            'top_predictions': top3,
            'is_fallback': False
        }
    
    def _fallback_response(self):
        """Return a fallback response when intent is unclear."""
        fallback_data = self.intent_map.get('fallback', {})
        responses = fallback_data.get('responses', [
            "I'm not sure about that. Try asking me about planets, stars, black holes, or space missions! 🚀"
        ])
        suggestions = fallback_data.get('suggestions', [
            "Solar system facts", "Black holes explained", "Fun space facts"
        ])
        
        return {
            'intent': 'fallback',
            'response': random.choice(responses),
            'confidence': 0.0,
            'suggestions': suggestions,
            'top_predictions': [],
            'is_fallback': True
        }
    
    def get_intent_list(self):
        """Return list of all available intents."""
        return [intent['tag'] for intent in self.intents_data['intents']]


if __name__ == '__main__':
    # Test the engine
    engine = ChatbotEngine()
    
    test_inputs = [
        "Tell me about black holes",
        "How do rockets work",
        "What is the speed of light",
        "Hello",
        "Thanks for the info",
        "asdkjhfaskjdfh"
    ]
    
    for text in test_inputs:
        result = engine.predict_intent(text)
        print(f"\nInput: '{text}'")
        print(f"Intent: {result['intent']} (confidence: {result['confidence']:.2%})")
        print(f"Response: {result['response'][:100]}...")
