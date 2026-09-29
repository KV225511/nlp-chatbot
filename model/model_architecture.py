"""
CNN + BiGRU + Multi-Head Self-Attention model architecture for intent classification.

This architecture combines:
- 1D CNN for local n-gram feature extraction (bigrams, trigrams, 4-grams)
- Bidirectional GRU for sequential context in both directions
- Multi-Head Self-Attention for focusing on intent-bearing words
- Dense classification head with dropout regularization

Padding tokens (id 0) are masked in the GRU, the attention layer and the
pooling layer, so short and long questions are scored consistently.
"""

import keras
from keras import layers, Model, ops


@keras.saving.register_keras_serializable(package="cosmosbot")
class PaddingMask(layers.Layer):
    """Boolean mask: True for real tokens, False for padding (token id 0)."""

    def call(self, inputs):
        return ops.not_equal(inputs, 0)


@keras.saving.register_keras_serializable(package="cosmosbot")
class AttentionPaddingMask(layers.Layer):
    """Turns a (batch, len) token mask into a (batch, len, len) attention mask."""

    def call(self, mask):
        return ops.logical_and(ops.expand_dims(mask, 1), ops.expand_dims(mask, 2))


def build_model(vocab_size, max_len, num_classes, embed_dim=128):
    """
    Build the CNN + BiGRU + Multi-Head Self-Attention model.

    Architecture:
        Input → Embedding → [Conv1D(k=2) || Conv1D(k=3) || Conv1D(k=4)] → Concat
        → BiGRU (masked) → MultiHeadAttention (masked) → Masked GlobalAvgPool
        → Dense → Dense → Softmax

    Args:
        vocab_size: Size of the vocabulary (number of unique tokens + 1)
        max_len: Maximum sequence length (padding length)
        num_classes: Number of intent classes
        embed_dim: Embedding dimension (default 128)

    Returns:
        Compiled Keras Model
    """
    inputs = layers.Input(shape=(max_len,), dtype='int32', name='text_input')
    token_mask = PaddingMask(name='padding_mask')(inputs)

    # Layer 1: Embedding
    x = layers.Embedding(input_dim=vocab_size, output_dim=embed_dim, name='embedding')(inputs)

    # Layer 2: Parallel 1D CNN branches (bigram, trigram, 4-gram)
    branches = []
    for kernel_size, name in [(2, 'bigram'), (3, 'trigram'), (4, 'fourgram')]:
        conv = layers.Conv1D(
            filters=64, kernel_size=kernel_size, padding='same',
            activation=None, name=f'conv1d_{name}'
        )(x)
        conv = layers.BatchNormalization(name=f'bn_{name}')(conv)
        conv = layers.Activation('relu', name=f'relu_{name}')(conv)
        branches.append(conv)

    cnn_out = layers.Concatenate(name='cnn_concat')(branches)
    cnn_out = layers.SpatialDropout1D(0.2, name='cnn_dropout')(cnn_out)

    # Layer 3: Bidirectional GRU (ignores padding via the mask)
    gru_out = layers.Bidirectional(
        layers.GRU(64, return_sequences=True, dropout=0.2, recurrent_dropout=0.0, name='gru'),
        name='bidirectional_gru'
    )(cnn_out, mask=token_mask)

    # Layer 4: Multi-Head Self-Attention (padding positions are not attended to)
    attention_mask = AttentionPaddingMask(name='attention_mask')(token_mask)
    attention_out = layers.MultiHeadAttention(
        num_heads=4, key_dim=32, dropout=0.1, name='multi_head_attention'
    )(gru_out, gru_out, attention_mask=attention_mask)

    # Residual connection + Layer normalization
    attention_out = layers.Add(name='residual_connection')([gru_out, attention_out])
    attention_out = layers.LayerNormalization(name='layer_norm')(attention_out)

    # Layer 5: Global Average Pooling over real tokens only
    pooled = layers.GlobalAveragePooling1D(name='global_avg_pool')(attention_out, mask=token_mask)

    # Layer 6-7: Classification head
    x = layers.Dense(128, activation='relu', name='dense_1')(pooled)
    x = layers.Dropout(0.4, name='dropout_1')(x)
    x = layers.Dense(64, activation='relu', name='dense_2')(x)
    x = layers.Dropout(0.3, name='dropout_2')(x)

    outputs = layers.Dense(num_classes, activation='softmax', name='intent_output')(x)

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
    test_model = build_model(vocab_size=500, max_len=25, num_classes=30, embed_dim=128)
    get_model_summary(test_model)
    print("\nModel architecture test successful!")
