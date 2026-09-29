"""
Complete training pipeline for the CosmosBot chatbot model.

Steps:
1. Load and preprocess intents data
2. Split into train/test sets
3. Build CNN + BiGRU + Attention model
4. Train with callbacks (EarlyStopping, ReduceLROnPlateau)
5. Save model, tokenizer, label encoder, and training history
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import json
import pickle
import numpy as np
from sklearn.model_selection import train_test_split

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.preprocessing import prepare_training_data
from model.model_architecture import build_model, get_model_summary

import tensorflow as tf


def train_model(
    intents_path=None,
    model_dir=None,
    max_len=25,
    embed_dim=128,
    epochs=300,
    batch_size=8,
    test_size=0.2,
    patience_early_stop=30,
    patience_reduce_lr=10
):
    """
    Complete training pipeline.
    
    Args:
        intents_path: Path to intents.json
        model_dir: Directory to save model artifacts
        max_len: Maximum sequence length
        embed_dim: Embedding dimension
        epochs: Maximum training epochs
        batch_size: Training batch size
        test_size: Fraction of data for validation
        patience_early_stop: Early stopping patience
        patience_reduce_lr: ReduceLR patience
    """
    # Set default paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if intents_path is None:
        intents_path = os.path.join(base_dir, 'data', 'intents.json')
    if model_dir is None:
        model_dir = os.path.join(base_dir, 'model')
    
    print("=" * 60)
    print("🚀 CosmosBot Training Pipeline")
    print("=" * 60)
    
    # ============================================
    # Step 1: Prepare training data
    # ============================================
    print("\n📦 Step 1: Preparing training data...")
    X, y, tokenizer, label_encoder, max_len, classes = prepare_training_data(
        intents_path, max_len=max_len
    )
    
    vocab_size = len(tokenizer.word_index) + 1
    num_classes = len(classes)
    
    # ============================================
    # Step 2: Train/Test split
    # ============================================
    print("\n✂️ Step 2: Splitting data (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y.argmax(axis=1)
    )
    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")
    
    # ============================================
    # Step 3: Build model
    # ============================================
    print("\n🏗️ Step 3: Building CNN + BiGRU + Attention model...")
    model = build_model(
        vocab_size=vocab_size,
        max_len=max_len,
        num_classes=num_classes,
        embed_dim=embed_dim
    )
    total_params = get_model_summary(model)
    
    # ============================================
    # Step 4: Define callbacks
    # ============================================
    print("\n⚙️ Step 4: Configuring training callbacks...")
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=patience_early_stop,
            restore_best_weights=True,
            verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=patience_reduce_lr,
            min_lr=1e-6,
            verbose=1
        )
    ]
    
    # ============================================
    # Step 5: Train the model
    # ============================================
    print("\n🎯 Step 5: Training model...")
    print(f"Epochs: {epochs} (max), Batch size: {batch_size}")
    print(f"Early stopping patience: {patience_early_stop}")
    print("-" * 40)
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=1
    )
    
    # ============================================
    # Step 6: Evaluate model
    # ============================================
    print("\n📊 Step 6: Evaluating model...")
    train_loss, train_acc = model.evaluate(X_train, y_train, verbose=0)
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    
    print(f"Training Accuracy:   {train_acc:.4f} ({train_acc*100:.2f}%)")
    print(f"Validation Accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)")
    print(f"Training Loss:       {train_loss:.4f}")
    print(f"Validation Loss:     {test_loss:.4f}")
    
    # ============================================
    # Step 7: Save all artifacts
    # ============================================
    print("\n💾 Step 7: Saving model artifacts...")
    
    # Save model
    model_path = os.path.join(model_dir, 'chatbot_model.keras')
    model.save(model_path)
    print(f"✅ Model saved: {model_path}")
    
    # Save tokenizer
    tokenizer_path = os.path.join(model_dir, 'tokenizer.pickle')
    with open(tokenizer_path, 'wb') as f:
        pickle.dump(tokenizer, f)
    print(f"✅ Tokenizer saved: {tokenizer_path}")
    
    # Save label encoder
    encoder_path = os.path.join(model_dir, 'label_encoder.pickle')
    with open(encoder_path, 'wb') as f:
        pickle.dump(label_encoder, f)
    print(f"✅ Label encoder saved: {encoder_path}")
    
    # Save training history
    history_data = {
        'accuracy': [float(v) for v in history.history['accuracy']],
        'val_accuracy': [float(v) for v in history.history['val_accuracy']],
        'loss': [float(v) for v in history.history['loss']],
        'val_loss': [float(v) for v in history.history['val_loss']],
        'epochs_trained': len(history.history['accuracy']),
        'final_train_accuracy': float(train_acc),
        'final_val_accuracy': float(test_acc),
        'final_train_loss': float(train_loss),
        'final_val_loss': float(test_loss),
        'total_params': int(total_params),
        'vocab_size': int(vocab_size),
        'num_classes': int(num_classes),
        'max_len': int(max_len),
        'embed_dim': int(embed_dim),
        'classes': classes
    }
    
    history_path = os.path.join(model_dir, 'training_history.json')
    with open(history_path, 'w') as f:
        json.dump(history_data, f, indent=2)
    print(f"✅ Training history saved: {history_path}")
    
    # Save max_len config
    config_path = os.path.join(model_dir, 'model_config.json')
    with open(config_path, 'w') as f:
        json.dump({
            'max_len': max_len,
            'vocab_size': vocab_size,
            'num_classes': num_classes,
            'embed_dim': embed_dim,
            'classes': classes
        }, f, indent=2)
    print(f"✅ Model config saved: {config_path}")
    
    # ============================================
    # Done!
    # ============================================
    print("\n" + "=" * 60)
    print("🎉 Training complete!")
    print(f"Final Validation Accuracy: {test_acc*100:.2f}%")
    print(f"Epochs trained: {len(history.history['accuracy'])}")
    print("=" * 60)
    
    return model, history, tokenizer, label_encoder


if __name__ == '__main__':
    model, history, tokenizer, label_encoder = train_model()
