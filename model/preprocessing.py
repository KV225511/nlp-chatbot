"""
Text preprocessing utilities for the CosmosBot chatbot.
Handles tokenization, lemmatization, vocabulary building, and sequence padding.
"""

import json
import re
import string
import pickle
import numpy as np
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.utils import to_categorical

# Try NLTK imports with fallback
try:
    import nltk
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


def ensure_nltk_data():
    """Download required NLTK data if not present."""
    if NLTK_AVAILABLE:
        for resource in ['punkt', 'punkt_tab', 'wordnet', 'omw-1.4']:
            try:
                nltk.data.find(f'tokenizers/{resource}' if 'punkt' in resource else f'corpora/{resource}')
            except LookupError:
                nltk.download(resource, quiet=True)


def clean_text(text):
    """
    Clean and normalize text input.
    - Lowercase
    - Remove special characters (keep alphanumeric and spaces)
    - Remove extra whitespace
    - Lemmatize words
    """
    text = text.lower().strip()
    # Remove special characters but keep apostrophes for contractions
    text = re.sub(r"[^a-zA-Z0-9\s']", '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    if NLTK_AVAILABLE:
        ensure_nltk_data()
        lemmatizer = WordNetLemmatizer()
        try:
            tokens = word_tokenize(text)
        except Exception:
            tokens = text.split()
        tokens = [lemmatizer.lemmatize(word) for word in tokens]
        text = ' '.join(tokens)

    return text


def load_intents(intents_path):
    """Load intents from JSON file."""
    with open(intents_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def prepare_training_data(intents_path, max_len=25):
    """
    Prepare training data from intents.json.
    
    Returns:
        X_padded: Padded token sequences (numpy array)
        y_encoded: One-hot encoded labels (numpy array)
        tokenizer: Fitted Keras Tokenizer
        label_encoder: Fitted LabelEncoder
        max_len: Maximum sequence length used
        classes: List of intent classes
    """
    data = load_intents(intents_path)
    
    texts = []
    labels = []
    
    for intent in data['intents']:
        tag = intent['tag']
        for pattern in intent['patterns']:
            cleaned = clean_text(pattern)
            if cleaned:  # Skip empty patterns
                texts.append(cleaned)
                labels.append(tag)
    
    print(f"Total training samples: {len(texts)}")
    print(f"Number of intents: {len(set(labels))}")
    
    # Tokenize texts
    tokenizer = Tokenizer(oov_token='<OOV>')
    tokenizer.fit_on_texts(texts)
    sequences = tokenizer.texts_to_sequences(texts)
    
    vocab_size = len(tokenizer.word_index) + 1
    print(f"Vocabulary size: {vocab_size}")
    
    # Pad sequences
    X_padded = pad_sequences(sequences, maxlen=max_len, padding='post', truncating='post')
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_int = label_encoder.fit_transform(labels)
    
    num_classes = len(label_encoder.classes_)
    y_encoded = to_categorical(y_int, num_classes=num_classes)
    
    print(f"Classes: {list(label_encoder.classes_)}")
    print(f"Input shape: {X_padded.shape}")
    print(f"Output shape: {y_encoded.shape}")
    
    return X_padded, y_encoded, tokenizer, label_encoder, max_len, list(label_encoder.classes_)


def text_to_sequence(text, tokenizer, max_len=25):
    """
    Convert a single text input to a padded sequence.
    Used during inference.
    """
    cleaned = clean_text(text)
    seq = tokenizer.texts_to_sequences([cleaned])
    padded = pad_sequences(seq, maxlen=max_len, padding='post', truncating='post')
    return padded


if __name__ == '__main__':
    # Test preprocessing
    import os
    intents_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'intents.json')
    X, y, tok, le, ml, classes = prepare_training_data(intents_path)
    print("\nPreprocessing test successful!")
    print(f"Sample input (first pattern): {X[0]}")
    print(f"Sample label (first pattern): {y[0]}")
