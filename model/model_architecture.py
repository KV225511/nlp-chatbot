"""
CNN + BiGRU + Multi-Head Self-Attention model architecture for intent classification.

This architecture combines:
- 1D CNN for local n-gram feature extraction (bigrams, trigrams, 4-grams)
- Bidirectional GRU for sequential context in both directions
- Multi-Head Self-Attention for focusing on intent-bearing words
- Dense classification head with dropout regularization

This is a transformer-inspired architecture that is lightweight enough to train
on CPU with small datasets while still leveraging modern attention mechanisms.
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model


def build_model(vocab_size, max_len, num_classes, embed_dim=128):
    """
    Build the CNN + BiGRU + Multi-Head Self-Attention model.
    
    Architecture:
        Input → Embedding → [Conv1D(k=2) || Conv1D(k=3) || Conv1D(k=4)] → Concat
        → BiGRU → MultiHeadAttention → GlobalAvgPool → Dense → Dense → Softmax
    
    Args:
        vocab_size: Size of the vocabulary (number of unique tokens + 1)
        max_len: Maximum sequence length (padding length)
        num_classes: Number of intent classes
        embed_dim: Embedding dimension (default 128)
    
    Returns:
        Compiled Keras Model
    """
    # Input layer
    inputs = layers.Input(shape=(max_len,), name='text_input')
    
    # ============================================
    # Layer 1: Embedding
    # Learns dense vector representations for each token
    # ============================================
    x = layers.Embedding(
        input_dim=vocab_size,
        output_dim=embed_dim,
        name='embedding'
    )(inputs)
    
    # ============================================
    # Layer 2: Parallel 1D CNN Feature Extraction
    # Three branches capture different n-gram patterns
    # ============================================
    
    # Branch A: Bigram features (kernel_size=2)
    # Captures 2-word patterns like "black hole", "feels like"
    conv2 = layers.Conv1D(
        filters=64, kernel_size=2, padding='same',
        activation=None, name='conv1d_bigram'
    )(x)
    conv2 = layers.BatchNormalization(name='bn_bigram')(conv2)
    conv2 = layers.Activation('relu', name='relu_bigram')(conv2)
    
    # Branch B: Trigram features (kernel_size=3)
    # Captures 3-word patterns like "speed of light", "how do rockets"
    conv3 = layers.Conv1D(
        filters=64, kernel_size=3, padding='same',
        activation=None, name='conv1d_trigram'
    )(x)
    conv3 = layers.BatchNormalization(name='bn_trigram')(conv3)
    conv3 = layers.Activation('relu', name='relu_trigram')(conv3)
    
    # Branch C: 4-gram features (kernel_size=4)
    # Captures 4-word patterns like "what is a black"
    conv4 = layers.Conv1D(
        filters=64, kernel_size=4, padding='same',
        activation=None, name='conv1d_fourgram'
    )(x)
    conv4 = layers.BatchNormalization(name='bn_fourgram')(conv4)
    conv4 = layers.Activation('relu', name='relu_fourgram')(conv4)
    
    # Concatenate all CNN branches
    # Output shape: (batch, max_len, 192)
    cnn_out = layers.Concatenate(name='cnn_concat')([conv2, conv3, conv4])
    cnn_out = layers.SpatialDropout1D(0.2, name='cnn_dropout')(cnn_out)
    
    # ============================================
    # Layer 3: Bidirectional GRU
    # Captures sequential dependencies from both directions
    # GRU is lighter than LSTM (fewer gates, fewer parameters)
    # ============================================
    gru_out = layers.Bidirectional(
        layers.GRU(
            64,
            return_sequences=True,  # Return full sequence for attention
            dropout=0.2,
            recurrent_dropout=0.0,  # Set to 0 for CuDNN compatibility
            name='gru'
        ),
        name='bidirectional_gru'
    )(cnn_out)
    # Output shape: (batch, max_len, 128) — 64 forward + 64 backward
    
    # ============================================
    # Layer 4: Multi-Head Self-Attention
    # THE KEY INNOVATION — same mechanism as in Transformers!
    # Allows model to focus on "intent-bearing" words
    # 4 heads × 32 dim each = 128 total
    # ============================================
    attention_out = layers.MultiHeadAttention(
        num_heads=4,
        key_dim=32,
        dropout=0.1,
        name='multi_head_attention'
    )(gru_out, gru_out)  # Self-attention: query=key=value=gru_out
    
    # Residual connection + Layer normalization (like a Transformer!)
    attention_out = layers.Add(name='residual_connection')([gru_out, attention_out])
    attention_out = layers.LayerNormalization(name='layer_norm')(attention_out)
    # Output shape: (batch, max_len, 128)
    
    # ============================================
    # Layer 5: Global Average Pooling
    # Reduces variable-length sequence to fixed-size vector
    # ============================================
    pooled = layers.GlobalAveragePooling1D(name='global_avg_pool')(attention_out)
    # Output shape: (batch, 128)
    
    # ============================================
    # Layer 6-7: Classification Head
    # Two Dense layers with dropout for regularization
    # ============================================
    x = layers.Dense(128, activation='relu', name='dense_1')(pooled)
    x = layers.Dropout(0.4, name='dropout_1')(x)
    
    x = layers.Dense(64, activation='relu', name='dense_2')(x)
    x = layers.Dropout(0.3, name='dropout_2')(x)
    
    # ============================================
    # Output Layer: Softmax classification
    # ============================================
    outputs = layers.Dense(
        num_classes,
        activation='softmax',
        name='intent_output'
    )(x)
    
    # Build and compile model
    model = Model(inputs=inputs, outputs=outputs, name='CosmosBot_CNN_BiGRU_Attention')
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model


def get_model_summary(model):
    """Print and return model summary."""
    model.summary()
    total_params = model.count_params()
    print(f"\nTotal parameters: {total_params:,}")
    print(f"Approximate model size: {total_params * 4 / 1024 / 1024:.2f} MB (float32)")
    return total_params


if __name__ == '__main__':
    # Test model building with sample dimensions
    test_model = build_model(
        vocab_size=500,
        max_len=25,
        num_classes=30,
        embed_dim=128
    )
    get_model_summary(test_model)
    print("\nModel architecture test successful!")
