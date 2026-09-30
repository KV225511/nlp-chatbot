/**
 * SpeechService — Handles Web Speech API (Speech Recognition & Speech Synthesis).
 */
class SpeechService {
    constructor() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognitionSupported = !!SpeechRecognition;
        this.currentRecognition = null;
        this.synthesisSupported = 'speechSynthesis' in window;
        this.ttsEnabled = localStorage.getItem('cosmos_tts') !== 'false';
    }

    getLangCode(langCode) {
        const map = {
            'en': 'en-US',
            'hi': 'hi-IN',
            'ta': 'ta-IN',
            'te': 'te-IN',
            'es': 'es-ES',
            'fr': 'fr-FR',
            'de': 'de-DE',
            'ja': 'ja-JP',
            'ko': 'ko-KR',
            'zh-cn': 'zh-CN',
            'bn': 'bn-IN',
            'mr': 'mr-IN'
        };
        return map[langCode] || 'en-US';
    }

    startListening(langCode, callbacks) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            callbacks?.onError?.('not-supported');
            return false;
        }

        // Clean up previous instance if still active
        this.stopListening();

        try {
            const recognition = new SpeechRecognition();
            this.currentRecognition = recognition;
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.maxAlternatives = 1;
            recognition.lang = this.getLangCode(langCode);

            let hasResult = false;

            recognition.onresult = (event) => {
                let interim = '';
                let final = '';

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const text = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        final += text;
                    } else {
                        interim += text;
                    }
                }

                if (final) {
                    hasResult = true;
                    callbacks?.onFinal?.(final.trim());
                } else if (interim) {
                    callbacks?.onInterim?.(interim.trim());
                }
            };

            recognition.onerror = (event) => {
                console.warn('SpeechRecognition error:', event.error);
                // 'no-speech' is non-fatal if user just paused
                callbacks?.onError?.(event.error);
            };

            recognition.onend = () => {
                callbacks?.onEnd?.();
                this.currentRecognition = null;
            };

            recognition.start();
            return true;
        } catch (err) {
            console.error('Failed to start speech recognition:', err);
            callbacks?.onError?.(err.name || err.message || 'start-failed');
            return false;
        }
    }

    stopListening() {
        if (this.currentRecognition) {
            try {
                this.currentRecognition.stop();
            } catch {
                try {
                    this.currentRecognition.abort();
                } catch {
                    // Ignore abort errors
                }
            }
            this.currentRecognition = null;
        }
    }

    speak(text, langCode = 'en') {
        if (!this.synthesisSupported || !this.ttsEnabled) return;

        try {
            window.speechSynthesis.cancel();

            // Strip markdown and emojis for clean voice synthesis
            const clean = text
                .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
                .replace(/\*\*/g, '')
                .trim();

            if (!clean) return;

            const utterance = new SpeechSynthesisUtterance(clean);
            const locale = this.getLangCode(langCode);
            utterance.lang = locale;
            utterance.rate = 1.0;
            utterance.pitch = 1.0;

            const voices = window.speechSynthesis.getVoices();
            const preferred = voices.find(v => v.lang.startsWith(locale.split('-')[0]) && (v.name.includes('Natural') || v.name.includes('Google')));
            if (preferred) {
                utterance.voice = preferred;
            }

            window.speechSynthesis.speak(utterance);
        } catch (err) {
            console.warn('Speech synthesis error:', err);
        }
    }

    toggleTTS() {
        this.ttsEnabled = !this.ttsEnabled;
        localStorage.setItem('cosmos_tts', this.ttsEnabled);
        if (!this.ttsEnabled && this.synthesisSupported) {
            window.speechSynthesis.cancel();
        }
        return this.ttsEnabled;
    }

    isTTSEnabled() {
        return this.ttsEnabled;
    }
}

export const speechService = new SpeechService();
