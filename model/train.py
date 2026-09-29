"""
Complete training pipeline for the CosmosBot chatbot model.

Steps:
1. Load intent patterns
2. Evaluation run: 80/20 split, augment the training part, train with
   EarlyStopping on val_loss and report validation accuracy
3. Final run: augment 100% of the patterns and train a fresh model on all of it
   (so every pattern in intents.json is learned), stopping when training loss plateaus
4. Save model, tokenizer, label encoder, config and training history
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import json
import pickle
from sklearn.model_selection import train_test_split

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.preprocessing import (
    load_patterns, build_training_texts, fit_tokenizer, encode_texts,
    fit_label_encoder, encode_labels
)
from model.model_architecture import build_model, get_model_summary

import tensorflow as tf

SEED = 42


def _train_eval_run(pairs, label_encoder, max_len, embed_dim, epochs, batch_size, test_size):
    """Train on 80% (augmented) and evaluate on the untouched 20%."""
    train_pairs, test_pairs = train_test_split(
        pairs, test_size=test_size, random_state=SEED,
        stratify=[tag for _, tag in pairs]
    )
    train_texts, train_tags = build_training_texts(train_pairs, augment=True, seed=SEED)
    test_texts, test_tags = build_training_texts(test_pairs, augment=False)

    tokenizer = fit_tokenizer(train_texts)
    X_train = encode_texts(train_texts, tokenizer, max_len)
    X_test = encode_texts(test_texts, tokenizer, max_len)
    y_train = encode_labels(train_tags, label_encoder)
    y_test = encode_labels(test_tags, label_encoder)

    tf.keras.utils.set_random_seed(SEED)
    model = build_model(len(tokenizer.word_index) + 1, max_len, len(label_encoder.classes_), embed_dim)
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=30, restore_best_weights=True),
            tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-6)
        ],
        verbose=0
    )
    val_loss, val_acc = model.evaluate(X_test, y_test, verbose=0)
    return history, float(val_acc), float(val_loss), len(train_texts), len(test_texts)


def train_model(
    intents_path=None,
    model_dir=None,
    max_len=25,
    embed_dim=128,
    epochs=300,
    final_max_epochs=60,
    batch_size=16,
    test_size=0.2
):
    """Complete training pipeline (evaluation run + final full-data run)."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if intents_path is None:
        intents_path = os.path.join(base_dir, 'data', 'intents.json')
    if model_dir is None:
        model_dir = os.path.join(base_dir, 'model')

    print("=" * 60)
    print("🚀 CosmosBot Training Pipeline")
    print("=" * 60)

    # Step 1: Load patterns
    print("\n📦 Step 1: Loading intent patterns...")
    pairs = load_patterns(intents_path)
    label_encoder = fit_label_encoder([tag for _, tag in pairs])
    classes = list(label_encoder.classes_)
    num_classes = len(classes)
    print(f"Patterns: {len(pairs)} | Intents: {num_classes}")

    # Step 2: Evaluation run (held-out 20%)
    print("\n📊 Step 2: Evaluation run (80% train + augmentation / 20% held out)...")
    eval_history, val_acc, val_loss, n_train, n_test = _train_eval_run(
        pairs, label_encoder, max_len, embed_dim, epochs, batch_size, test_size
    )
    print(f"Augmented training texts: {n_train} | Held-out texts: {n_test}")
    print(f"Validation Accuracy: {val_acc:.4f} ({val_acc*100:.2f}%)")
    print(f"Validation Loss:     {val_loss:.4f}")

    # Step 3: Final run on 100% of the patterns
    print("\n🎯 Step 3: Final training on all patterns (with augmentation)...")
    texts, tags = build_training_texts(pairs, augment=True, seed=SEED)
    tokenizer = fit_tokenizer(texts)
    X = encode_texts(texts, tokenizer, max_len)
    y = encode_labels(tags, label_encoder)
    vocab_size = len(tokenizer.word_index) + 1

    tf.keras.utils.set_random_seed(SEED)
    model = build_model(vocab_size=vocab_size, max_len=max_len, num_classes=num_classes, embed_dim=embed_dim)
    total_params = get_model_summary(model)
    history = model.fit(
        X, y,
        epochs=final_max_epochs,
        batch_size=batch_size,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(monitor='loss', patience=8, min_delta=0.005, restore_best_weights=True)
        ],
        verbose=1
    )
    train_loss, train_acc = model.evaluate(X, y, verbose=0)
    print(f"Final Training Accuracy: {train_acc:.4f} ({train_acc*100:.2f}%)")

    # Step 4: Save all artifacts
    print("\n💾 Step 4: Saving model artifacts...")
    model_path = os.path.join(model_dir, 'chatbot_model.keras')
    model.save(model_path)
    print(f"✅ Model saved: {model_path}")

    with open(os.path.join(model_dir, 'tokenizer.pickle'), 'wb') as f:
        pickle.dump(tokenizer, f)
    with open(os.path.join(model_dir, 'label_encoder.pickle'), 'wb') as f:
        pickle.dump(label_encoder, f)
    print("✅ Tokenizer and label encoder saved")

    history_data = {
        'accuracy': [float(v) for v in history.history['accuracy']],
        'loss': [float(v) for v in history.history['loss']],
        'eval_accuracy': [float(v) for v in eval_history.history['accuracy']],
        'eval_val_accuracy': [float(v) for v in eval_history.history['val_accuracy']],
        'eval_loss': [float(v) for v in eval_history.history['loss']],
        'eval_val_loss': [float(v) for v in eval_history.history['val_loss']],
        'epochs_trained': len(history.history['accuracy']),
        'final_train_accuracy': float(train_acc),
        'final_train_loss': float(train_loss),
        'final_val_accuracy': val_acc,
        'final_val_loss': val_loss,
        'original_patterns': len(pairs),
        'augmented_samples': len(texts),
        'total_params': int(total_params),
        'vocab_size': int(vocab_size),
        'num_classes': int(num_classes),
        'max_len': int(max_len),
        'embed_dim': int(embed_dim),
        'classes': classes
    }
    with open(os.path.join(model_dir, 'training_history.json'), 'w') as f:
        json.dump(history_data, f, indent=2)
    print("✅ Training history saved")

    with open(os.path.join(model_dir, 'model_config.json'), 'w') as f:
        json.dump({
            'max_len': max_len,
            'vocab_size': vocab_size,
            'num_classes': num_classes,
            'embed_dim': embed_dim,
            'classes': classes
        }, f, indent=2)
    print("✅ Model config saved")

    print("\n" + "=" * 60)
    print("🎉 Training complete!")
    print(f"Held-out Validation Accuracy: {val_acc*100:.2f}%")
    print(f"Final Training Accuracy:      {train_acc*100:.2f}%")
    print(f"Final epochs trained:         {len(history.history['accuracy'])}")
    print("=" * 60)

    return model, history, tokenizer, label_encoder


if __name__ == '__main__':
    train_model()
