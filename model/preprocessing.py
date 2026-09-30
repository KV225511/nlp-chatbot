"""
Text preprocessing utilities for the CosmosBot chatbot.
Handles cleaning, lemmatization, data augmentation, vocabulary building and padding.
"""

import os
import json
import random
import re
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.utils import to_categorical

# Try NLTK imports only if explicitly needed for training
try:
    import nltk
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

_NLTK_READY = False
_LEMMATIZER = None

# Load precomputed lemma dictionary for zero-RAM fast inference
_LEMMA_DICT = {}
_lemma_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', 'lemma_dict.json')
if os.path.exists(_lemma_path):
    try:
        with open(_lemma_path, 'r', encoding='utf-8') as _f:
            _LEMMA_DICT = json.load(_f)
    except Exception:
        pass

# Intents that are small talk, not topics: they are never augmented with topic prefixes
CONVERSATIONAL_TAGS = {'greeting', 'goodbye', 'thanks', 'about_bot', 'breathing_exercise'}

# Phrases users put around a topic ("tell me about X please")
AUGMENT_PREFIXES = [
    "tell me about", "what is", "what are", "explain", "can you explain",
    "i want to know about", "give me info on", "do you know about", "describe"
]
AUGMENT_SUFFIXES = ["", "please", "in simple words"]
QUESTION_STARTS = (
    "what", "how", "why", "who", "when", "where", "is ", "are ", "can ",
    "do ", "does ", "tell", "explain"
)


def ensure_nltk_data():
    """Optional: Download required NLTK data for offline model training."""
    global _NLTK_READY, _LEMMATIZER
    if _NLTK_READY or not NLTK_AVAILABLE:
        return
    for resource in ['punkt', 'punkt_tab', 'wordnet', 'omw-1.4']:
        try:
            nltk.data.find(f'tokenizers/{resource}' if 'punkt' in resource else f'corpora/{resource}')
        except LookupError:
            nltk.download(resource, quiet=True)
    _LEMMATIZER = WordNetLemmatizer()
    _NLTK_READY = True


def tokenize_fast(text):
    """
    Fast regex-based tokenizer that matches Penn Treebank contractions
    without loading NLTK into memory.
    """
    text = text.lower().strip()
    text = re.sub(r"[^a-zA-Z0-9\s']", '', text)
    # Penn Treebank contractions
    text = re.sub(r"\bcan't\b", "ca n't", text)
    text = re.sub(r"\bwon't\b", "wo n't", text)
    text = re.sub(r"\bgotta\b", "got ta", text)
    text = re.sub(r"\bgonna\b", "gon na", text)
    text = re.sub(r"n't\b", " n't", text)
    text = re.sub(r"'s\b", " 's", text)
    text = re.sub(r"'re\b", " 're", text)
    text = re.sub(r"'d\b", " 'd", text)
    text = re.sub(r"'ll\b", " 'll", text)
    text = re.sub(r"'m\b", " 'm", text)
    text = re.sub(r"'ve\b", " 've", text)
    return text.split()


def lemmatize_token(token):
    """Lemmatize a single token using lemma dict with rule fallback."""
    if token in _LEMMA_DICT:
        return _LEMMA_DICT[token]
    if len(token) > 4 and token.endswith('ies'):
        return token[:-3] + 'y'
    if len(token) > 3 and token.endswith('es') and not token.endswith(('ses', 'xes', 'ches', 'shes')):
        return token[:-2]
    if len(token) > 3 and token.endswith('s') and not token.endswith(('ss', 'us', 'is')):
        return token[:-1]
    return token


def clean_text(text):
    """
    Clean and normalize text input without heavy NLTK overhead.
    - Lowercase
    - Remove special characters (keep contractions)
    - Tokenize with Penn Treebank contraction handling
    - Lemmatize words
    """
    if not text:
        return ""
    tokens = tokenize_fast(text)
    lemmatized = [lemmatize_token(t) for t in tokens]
    return ' '.join(lemmatized)


def load_intents(intents_path):
    """Load intents from JSON file."""
    with open(intents_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def load_patterns(intents_path):
    """Return a list of (pattern, tag) pairs for every intent that has patterns."""
    data = load_intents(intents_path)
    return [
        (pattern, intent['tag'])
        for intent in data['intents']
        for pattern in intent['patterns']
    ]


def augment_pattern(pattern, tag, rng, copies=4):
    """
    Create extra phrasings of a topic pattern so the model learns that
    words like "tell me about" or "please" do not change the intent.
    Small-talk intents and patterns that are already full questions get
    at most one extra variant.
    """
    variants = [pattern]
    if tag in CONVERSATIONAL_TAGS:
        return variants

    lowered = pattern.lower()
    if lowered.startswith(QUESTION_STARTS):
        variants.append(f"{pattern} {rng.choice(AUGMENT_SUFFIXES[1:])}")
    else:
        for _ in range(copies):
            prefix = rng.choice(AUGMENT_PREFIXES)
            suffix = rng.choice(AUGMENT_SUFFIXES)
            variants.append(f"{prefix} {pattern} {suffix}".strip())

    return list(dict.fromkeys(variants))


def build_training_texts(pairs, augment=True, seed=42):
    """
    Turn (pattern, tag) pairs into cleaned training texts and labels.

    Returns:
        texts: list of cleaned strings
        tags: list of intent tags (same length as texts)
    """
    rng = random.Random(seed)
    texts, tags = [], []
    for pattern, tag in pairs:
        variants = augment_pattern(pattern, tag, rng) if augment else [pattern]
        for variant in variants:
            cleaned = clean_text(variant)
            if cleaned:
                texts.append(cleaned)
                tags.append(tag)
    return texts, tags


def fit_tokenizer(texts):
    """Fit a Keras tokenizer (with an <OOV> token) on cleaned texts."""
    tokenizer = Tokenizer(oov_token='<OOV>')
    tokenizer.fit_on_texts(texts)
    return tokenizer


def encode_texts(texts, tokenizer, max_len=25):
    """Convert cleaned texts to padded integer sequences."""
    sequences = tokenizer.texts_to_sequences(texts)
    return pad_sequences(sequences, maxlen=max_len, padding='post', truncating='post')


def fit_label_encoder(tags):
    """Fit a LabelEncoder on intent tags."""
    label_encoder = LabelEncoder()
    label_encoder.fit(tags)
    return label_encoder


def encode_labels(tags, label_encoder):
    """One-hot encode intent tags."""
    num_classes = len(label_encoder.classes_)
    return to_categorical(label_encoder.transform(tags), num_classes=num_classes)


def text_to_sequence(text, tokenizer, max_len=25):
    """
    Convert a single text input to a padded sequence.
    Used during inference.
    """
    return encode_texts([clean_text(text)], tokenizer, max_len)


if __name__ == '__main__':
    import os
    intents_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'intents.json')
    pairs = load_patterns(intents_path)
    texts, tags = build_training_texts(pairs)
    print(f"Original patterns: {len(pairs)}")
    print(f"Augmented training texts: {len(texts)}")
    print(f"Sample: {texts[:5]}")
