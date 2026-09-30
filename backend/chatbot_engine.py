"""
Core chatbot engine for CosmosBot.
Loads the trained model and decides whether a question is covered by the
dataset, using two signals:
  1. the neural network's predicted intent (CNN + BiGRU + Attention)
  2. TF-IDF similarity to the closest pattern in intents.json
Only when both agree and the similarity is high enough is the dataset answer used.
"""

import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import json
import pickle
import random
import numpy as np
import tensorflow as tf

# Limit TensorFlow to 1 thread to conserve RAM on Render Free Tier (512MB limit)
try:
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(1)
except Exception:
    pass

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Import preprocessing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.preprocessing import clean_text, CONVERSATIONAL_TAGS
import model.model_architecture  # noqa: F401  registers the custom mask layers for load_model
from backend.intent_matcher import IntentMatcher

# Similarity to the closest dataset pattern needed to answer from the dataset
KNOWN_SIMILARITY = 0.65
# Small talk ("hey buddy", "thank you so much") is short, so it gets a lower bar
CONVERSATIONAL_SIMILARITY = 0.45
# If web search is unavailable, a weaker dataset match is still better than nothing
WEAK_SIMILARITY = 0.45


class ChatbotEngine:
    """
    Main chatbot engine that handles:
    - Model loading
    - Text preprocessing
    - Intent prediction
    - Deciding whether the dataset covers the question
    """

    def __init__(self, model_dir=None, intents_path=None):
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
        with open(os.path.join(model_dir, 'tokenizer.pickle'), 'rb') as f:
            self.tokenizer = pickle.load(f)

        # Load label encoder
        with open(os.path.join(model_dir, 'label_encoder.pickle'), 'rb') as f:
            self.label_encoder = pickle.load(f)

        # Load model config
        with open(os.path.join(model_dir, 'model_config.json'), 'r') as f:
            self.config = json.load(f)

        self.max_len = self.config['max_len']

        # Load intents data
        with open(intents_path, 'r', encoding='utf-8') as f:
            self.intents_data = json.load(f)

        self.intent_map = {intent['tag']: intent for intent in self.intents_data['intents']}
        self.matcher = IntentMatcher(self.intents_data)

        print("✅ ChatbotEngine loaded successfully!")
        print(f"   Model: {self.config.get('num_classes', '?')} intents, vocab_size={self.config.get('vocab_size', '?')}")

    def predict_intent(self, text):
        """
        Predict the intent of a given text input.

        Returns:
            dict with keys:
                intent, response, confidence, suggestions, top_predictions,
                is_fallback, is_known, is_weak_match, nn_confidence, match_similarity
        """
        cleaned = clean_text(text)
        seq = self.tokenizer.texts_to_sequences([cleaned])
        if not cleaned.strip() or not seq[0]:
            return self._fallback_response()

        padded = pad_sequences(seq, maxlen=self.max_len, padding='post', truncating='post')
        pred = self.model.predict(padded, verbose=0)[0]

        intent_idx = int(np.argmax(pred))
        nn_confidence = float(pred[intent_idx])
        intent_tag = self.label_encoder.inverse_transform([intent_idx])[0]

        top3_idx = np.argsort(pred)[-3:][::-1]
        top3 = [
            {
                'intent': str(self.label_encoder.inverse_transform([idx])[0]),
                'confidence': round(float(pred[idx]), 4)
            }
            for idx in top3_idx
        ]

        match_tag, similarity = self.matcher.best_match(cleaned)
        agree = match_tag == intent_tag
        threshold = CONVERSATIONAL_SIMILARITY if intent_tag in CONVERSATIONAL_TAGS else KNOWN_SIMILARITY
        is_known = agree and similarity >= threshold
        is_weak_match = agree and similarity >= WEAK_SIMILARITY

        intent_data = self.intent_map.get(intent_tag)
        if intent_data is None or not is_weak_match:
            result = self._fallback_response()
            result.update({
                'top_predictions': top3,
                'nn_confidence': round(nn_confidence, 4),
                'match_similarity': round(similarity, 4)
            })
            return result

        return {
            'intent': str(intent_tag),
            'response': random.choice(intent_data['responses']),
            # Both signals must be high for a high score, so this number is stable
            'confidence': round(min(nn_confidence, similarity), 4),
            'suggestions': intent_data.get('suggestions', []),
            'top_predictions': top3,
            'is_fallback': False,
            'is_known': is_known,
            'is_weak_match': True,
            'nn_confidence': round(nn_confidence, 4),
            'match_similarity': round(similarity, 4)
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
            'is_fallback': True,
            'is_known': False,
            'is_weak_match': False,
            'nn_confidence': 0.0,
            'match_similarity': 0.0
        }

    def off_topic_response(self):
        """Reply for questions that are not about space or astronomy."""
        result = self._fallback_response()
        result['response'] = (
            "That's outside my orbit! 🛰️ I only answer questions about space and astronomy — "
            "planets, stars, black holes, rockets, missions like ISRO's Chandrayaan, and more. "
            "Try asking me something cosmic!"
        )
        return result

    def get_intent_list(self):
        """Return list of all available intents."""
        return [intent['tag'] for intent in self.intents_data['intents']]


if __name__ == '__main__':
    engine = ChatbotEngine()

    test_inputs = [
        "Tell me about black holes",
        "How do rockets work",
        "What is the speed of light",
        "Hello",
        "Thanks for the info",
        "What is ISRO",
        "asdkjhfaskjdfh"
    ]

    for text in test_inputs:
        result = engine.predict_intent(text)
        print(f"\nInput: '{text}'")
        print(f"Intent: {result['intent']} (confidence: {result['confidence']:.2%}, known: {result['is_known']})")
        print(f"Response: {result['response'][:100]}...")
