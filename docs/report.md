# Lab Assessment Report: CosmosBot 🚀
## Voice-Enabled Space & Astronomy Chatbot Using Speech Recognition and Deep Learning

**Course:** Natural Language Processing / Deep Learning Lab Assessment  
**Project Title:** CosmosBot — Voice-Enabled Space & Astronomy Conversational Assistant  
**Domain:** Space Exploration, Astrophysics, Planetary Science, and Observational Astronomy  
**Submission Artifacts:** Full Source Code + Live Deployment Pipeline + Experimental Report  

---

## 1. Executive Summary

CosmosBot is an end-to-end voice-enabled conversational AI system specialized in the domain of astronomy and space exploration. Unlike standard generic chatbots that rely on superficial keyword matching or rule-based heuristics, CosmosBot incorporates a hybrid deep learning architecture—combining **1D Convolutional Neural Networks (CNN)** for local n-gram extraction, **Bidirectional Gated Recurrent Units (BiGRU)** for contextual sequential modeling, and a **Multi-Head Self-Attention** mechanism inspired by modern Transformer architectures.

The system features real-time bidirectional voice communication:
1. **Speech-to-Text (STT):** Captures user voice inputs via the Web Speech Recognition API with low-latency streaming text transcription.
2. **Deep Learning Intent Classifier:** Tokenizes, cleans, pads, and classifies natural language utterances across 38 space exploration intents.
3. **Context & Sentiment Pipeline:** Tracks user emotional state across conversational turns using VADER sentiment analysis, manages dialogue context, and computes contextual follow-up recommendations.
4. **Text-to-Speech (TTS):** Synthesizes neural responses back to audible speech in the user's selected language.
5. **Interactive Glassmorphic React 18 UI:** Built with React 18 and Vite, featuring componentized architecture, real-time confidence scores, mood tracking analytics via Chart.js, a 4-7-8 cosmic breathing relaxation exercise, procedural sound synthesis via Web Audio API, dynamic suggestion chips, and conversation export to PDF.

---

## 2. Dataset Description

### 2.1 Domain Specialization: Space Exploration
Rather than using generic conversational corpora (e.g. small talk or greeting sets), CosmosBot is anchored in **Space Exploration and Astrophysics**. The dataset comprises 38 distinct intents covering:
- **Planetary Science:** Solar system structure, Mars missions (Perseverance/Curiosity), Europa's subsurface ocean, Saturn's rings, Venus' runaway greenhouse effect, exoplanets.
- **Astrophysics & Cosmology:** Black holes and event horizons, neutron stars & pulsars, dark matter & dark energy, cosmic microwave background, stellar evolution & supernovae.
- **Space Flight & Missions:** Rocket propulsion principles, James Webb Space Telescope (JWST), Hubble Space Telescope, Apollo program, Artemis Moon return, International Space Station (ISS).
- **Interactive & Utility Intents:** Greetings, acknowledgments, multi-language query prompts, cosmic breathing guidance, conversational reset, and calibrated fallbacks.

### 2.2 Dataset Statistics
- **Total Intents:** 38 classes
- **Total Training Utterances:** 320+ curated query variations incorporating diverse syntactic structures, idioms, colloquial phrasing, and domain terminology.
- **Responses:** Rich, scientifically accurate explanations paired with follow-up topic suggestions and contextual links.
- **Data Format:** JSON structure with `tag`, `patterns`, `responses`, `suggestions`, and `related_intents`.

---

## 3. Preprocessing Pipeline

The text preprocessing pipeline (`model/preprocessing.py`) prepares raw user speech or typed text for neural inference:

1. **Text Normalization:**
   - Lowercasing of all characters.
   - Punctuation stripping with regex preservation of apostrophes (e.g., preserving contractions like *"what's"*).
   - Redundant whitespace collapsing.

2. **Morphological Lemmatization:**
   - Word tokenization and lemmatization using NLTK's `WordNetLemmatizer` with fallback to token split. Words like *"telescopes"*, *"telescopic"*, and *"telescope"* are mapped to their canonical lemma form.

3. **Subword & Word Tokenization:**
   - Keras `Tokenizer` maps the vocabulary with an explicit `<OOV>` (Out-of-Vocabulary) token to handle unexpected astronomical queries gracefully.
   - Sequences are padded/truncated to a fixed window length $T_{max} = 25$ using `post` padding.

4. **Categorical Label Encoding:**
   - Target intent tags are mapped to one-hot vectors using Scikit-Learn `LabelEncoder` and Keras `to_categorical`.

5. **Data Augmentation:**
   - Every topic pattern gets up to four extra phrasings built from carrier phrases (e.g. *"tell me about … please"*), teaching the model that such words do not change the intent. Small-talk intents are not augmented.

6. **Padding Masks:**
   - A boolean mask (token id ≠ 0) is passed to the BiGRU, the Multi-Head Attention layer and the Global Average Pooling layer, so padding never influences the prediction and short and long questions are scored consistently.

---

## 4. Model Architecture & Deep Learning Methodology

### 4.1 Motivation: Bridging Traditional RNNs and Transformers
While Large Language Models (LLMs) and standard 12-layer Transformer models (BERT, GPT) achieve state-of-the-art results, they require billions of parameters, heavy GPU memory, and significant inference latency unsuitable for lightweight, cost-effective lab deployments. Conversely, shallow bag-of-words or simple Vanilla RNNs fail to capture long-distance syntactic dependencies and multi-word phrases (e.g., *"event horizon"*, *"James Webb"*).

CosmosBot adopts an **asymmetric hybrid architecture**:
$$\text{Input} \longrightarrow \text{Embedding} \longrightarrow \text{Parallel 1D CNNs} \longrightarrow \text{BiGRU} \longrightarrow \text{Multi-Head Attention} \longrightarrow \text{Global Pooling} \longrightarrow \text{Dense MLP}$$

```
                +------------------------------------+
                |       Input Tokens (L = 25)        |
                +------------------------------------+
                                   │
                                   ▼
                +------------------------------------+
                |    Embedding Layer (dim = 128)     |
                +------------------------------------+
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
+─────────────────+       +─────────────────+       +─────────────────+
| Conv1D (k=2, 64)|       | Conv1D (k=3, 64)|       | Conv1D (k=4, 64)|
|   (Bigrams)     |       |   (Trigrams)    |       |   (4-Grams)     |
+─────────────────+       +─────────────────+       +─────────────────+
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   ▼
                +------------------------------------+
                | Concatenate + SpatialDropout (192) |
                +------------------------------------+
                                   │
                                   ▼
                +------------------------------------+
                |  Bidirectional GRU (2 × 64 = 128)  |
                +------------------------------------+
                                   │
                                   ▼
                +------------------------------------+
                | Multi-Head Self-Attention (4 heads)|
                +------------------------------------+
                                   │
                                   ▼
                +------------------------------------+
                |   Residual Connection + LayerNorm  |
                +------------------------------------+
                                   │
                                   ▼
                +------------------------------------+
                |     Global Average Pooling 1D      |
                +------------------------------------+
                                   │
                                   ▼
                +------------------------------------+
                |     Dense(128, ReLU) + Dropout     |
                +------------------------------------+
                                   │
                                   ▼
                +------------------------------------+
                |     Dense(64, ReLU) + Dropout      |
                +------------------------------------+
                                   │
                                   ▼
                +------------------------------------+
                |      Dense(38, Softmax Output)     |
                +------------------------------------+
```

### 4.2 Mathematical Components

1. **Parallel Multi-Scale 1D CNNs:**
   Extracts local n-gram patterns simultaneously across 3 kernel sizes ($k \in \{2, 3, 4\}$):
   $$c_i^{(k)} = \text{ReLU}\left(\text{BatchNorm}\left(\mathbf{W}^{(k)} * \mathbf{x}_{i:i+k-1} + b^{(k)}\right)\right)$$
   This ensures specialized compound phrases like *"black hole"* ($k=2$) and *"speed of light"* ($k=3$) are explicitly detected.

2. **Bidirectional GRU (BiGRU):**
   Captures bi-directional sequence context with lower computational overhead than LSTM:
   $$\overrightarrow{h}_t = \text{GRU}(\mathbf{c}_t, \overrightarrow{h}_{t-1}), \quad \overleftarrow{h}_t = \text{GRU}(\mathbf{c}_t, \overleftarrow{h}_{t+1})$$
   $$H_t = [\overrightarrow{h}_t \,\|\, \overleftarrow{h}_t] \in \mathbb{R}^{128}$$

3. **Multi-Head Self-Attention:**
   Computes scaled dot-product attention across $H = 4$ representation subspaces:
   $$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$
   $$\text{MultiHead}(H) = \text{Concat}(\text{head}_1, \dots, \text{head}_4)\mathbf{W}^O$$
   Allows the network to focus heavily on discriminative tokens (e.g. *"propulsion"*, *"singularity"*, *"exoplanet"*) regardless of sentence length.

4. **Residual Connection & Layer Normalization:**
   Preserves gradient flow and stabilizes hidden state variance:
   $$Z = \text{LayerNorm}(H + \text{MultiHead}(H))$$

---

## 5. System Features & Implementation Details

| Feature ID | Feature Name | Technical Description |
|---|---|---|
| **A1** | **Voice Output (TTS)** | Implemented via Web Speech API `SpeechSynthesis`. Dynamic speech queue with customizable pitch, speed, and auto-voice selection matching target language. |
| **A2** | **Match Scoring** | The displayed score is `min(softmax probability, TF-IDF similarity to the closest dataset pattern)`, shown as a colour-coded bar with a label (≥ 85% strong, ≥ 65% good, otherwise partial). |
| **A3** | **Quick Reply Chips** | Dynamically rendered button chips offering contextual follow-up questions linked to the predicted space topic. |
| **A4** | **Dark / Light Mode** | Modern CSS custom property theming persisted in `localStorage` with smooth transition interpolation. |
| **B1** | **Sentiment Analysis** | Real-time sentiment classification using VADER (Valence Aware Dictionary and sEntiment Reasoner), extracting valence scores and sentiment emojis. |
| **B2** | **Mood Dashboard** | Interactive modal powered by Chart.js displaying real-time temporal valence curves, emotional distribution, and aggregate sentiment metrics across the conversation. |
| **B3** | **Breathing Exercise** | Guided 4-7-8 cosmic relaxation module featuring an expanding/contracting glowing nebula circle with countdown cues. |
| **B4** | **PDF Export** | Client-side PDF generation using `jsPDF`, formatting transcript timestamps, user queries, bot replies, confidence levels, and sentiment summaries. |
| **B5** | **Context Follow-ups** | In-memory session tracking module (`ContextManager`) mapping semantic connections between topics (e.g., *Black Holes* $\rightarrow$ *Neutron Stars* or *General Relativity*). |
| **B6** | **Multi-Language** | Translation pipeline supporting 12 international and regional languages (English, Hindi, Tamil, Telugu, Spanish, French, German, Japanese, Korean, Chinese, etc.). |
| **B7** | **Web Search Fallback** | Questions the dataset does not cover (network and TF-IDF disagree, or similarity < 0.65) are looked up in the Wikipedia search and summary APIs, with DuckDuckGo Instant Answers as a backup. A result is accepted only if it is about space or astronomy (keyword filter) and is shown with its source link. Non-space topics are refused, and small talk is never searched. |
| **C1** | **Typing Animation** | Realistic delayed character typing effect with pulsing ellipsis indicators. |
| **C2** | **Glassmorphism UI** | Multi-layer frosted glass effects using CSS `backdrop-filter: blur(16px)`, translucent radial gradients, and animated starfield backgrounds. |
| **C3** | **Responsive Design** | Mobile-first flexbox and grid layouts adaptable to smartphones, tablets, and widescreen desktop monitors. |
| **C4** | **Sound Effects** | Procedurally generated audio using the HTML5 Web Audio API (sine/triangle wave synthesis, gain envelopes, and cosmic chimes) without external MP3 dependencies. |

---

## 6. Deployment Architecture

CosmosBot is packaged for instant deployment to cloud platforms (such as Render, Railway, or Heroku):
- **Web Server:** Gunicorn WSGI server (`gunicorn backend.app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1`).
- **Memory Optimization:** Configured for single-worker execution with CPU-optimized TensorFlow wheels (`tensorflow-cpu`), staying comfortably under the 512MB RAM limit on free-tier containers.
- **Port Binding:** Dynamically binds to the cloud provider's `$PORT` environment variable.
- **Static Asset Serving:** Unified Flask application that simultaneously delivers the REST API and serves the client frontend with zero cross-origin issues.

---

## 7. Experimental Results & Evaluation

### 7.1 Quantitative Performance Metrics

Training runs in two phases. **Phase 1 (evaluation):** the 454 original patterns are split 80/20 (stratified); only the 80% part is augmented, and the model is trained with `ReduceLROnPlateau` and `EarlyStopping` (patience 30, best weights restored) and evaluated on the untouched 20%. **Phase 2 (final model):** a fresh model is trained on 100% of the augmented patterns, stopping when training loss plateaus, so every pattern in `intents.json` is learned.

| Metric | Measured Value |
|---|---|
| **Total Model Parameters** | 328,870 |
| **Target Intent Classes** | 38 categories |
| **Vocabulary Size** | 481 unique tokens |
| **Original / Augmented Training Samples** | 454 / 1447 |
| **Maximum Sequence Length** | 25 tokens |
| **Final-model Epochs** | 43 |
| **Initial Learning Rate** | 0.001 (Adam Optimizer) |
| **Held-out Validation Accuracy (Phase 1)** | **57.14%** (was 51.65% before padding masks and augmentation) |
| **Held-out Validation Loss (Phase 1)** | 2.2378 |
| **Final Training Accuracy (Phase 2)** | **99.45%** |
| **Final Training Loss (Phase 2)** | 0.0100 |

*Note: held-out accuracy measures phrasings the model has never seen, with only ~12 patterns per intent. At answer time, a TF-IDF similarity check decides whether a question is covered at all; uncovered questions go to web search instead of being forced into one of the 38 intents.*

### 7.2 Sample Inference Evaluations

| User Query | Route | Result Intent / Source | Match Score |
|---|---|---|---|
| *"Tell me about black holes"* | Knowledge base | `black_holes` | **100%** |
| *"Tell me about Apollo 11"* | Knowledge base | `space_exploration_history` | **81%** |
| *"What is the speed of light"* | Knowledge base | `light_speed` | **100%** |
| *"Hello"* | Knowledge base | `greeting` | **100%** |
| *"What is ISRO?"* | Web search | Wikipedia: ISRO | n/a (source link shown) |
| *"What is Chandrayaan 3"* | Web search | Wikipedia: Chandrayaan-3 | n/a (source link shown) |
| *"What is the capital of France"* | Refused (not space) | `fallback` ("outside my orbit") | 0% |
| *"asdkjhfaskjdfh"* (Gibberish) | Fallback | `fallback` ("I don't know") | 0% |

---

## 8. Conclusion & Future Work

CosmosBot successfully meets and exceeds all requirements of the Lab Assessment:
1. **Full Voice Pipeline:** End-to-end speech recognition (STT) and synthesized voice feedback (TTS).
2. **Modern Deep Learning:** Replaces primitive bag-of-words or heavy Transformer architectures with an efficient, novel CNN + BiGRU + Self-Attention network ($<330\text{k}$ parameters).
3. **Rich Multimodal Experience:** Sentiment analysis, mood tracking dashboard with Chart.js, cosmic breathing exercises, PDF transcripts, 12-language translation, sound effects, and glassmorphism styling.
4. **Production Readiness:** Lightweight, self-contained dependencies ready for instant cloud deployment.

