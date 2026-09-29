/**
 * SpeechService — Handles Web Speech API (Speech Recognition & Speech Synthesis).
 */
class SpeechService {
    constructor() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognitionSupported = !!SpeechRecognition;
        this.recognition = null;

        if (this.recognitionSupported) {
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = true;
            this.recognition.maxAlternatives = 1;
        }

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
        if (!this.recognitionSupported || !this.recognition) {
            callbacks?.onError?.('not-supported');
            return false;
        }

        const locale = this.getLangCode(langCode);
        this.recognition.lang = locale;

        this.recognition.onresult = (event) => {
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
                callbacks?.onFinal?.(final.trim());
            } else if (interim) {
                callbacks?.onInterim?.(interim.trim());
            }
        };

        this.recognition.onerror = (event) => {
            callbacks?.onError?.(event.error);
        };

        this.recognition.onend = () => {
            callbacks?.onEnd?.();
        };

        try {
            this.recognition.start();
            return true;
        } catch (err) {
            callbacks?.onError?.(err.message);
            return false;
        }
    }

    stopListening() {
        if (this.recognitionSupported && this.recognition) {
            try {
                this.recognition.stop();
            } catch (e) {
                // Ignore stop error
            }
        }
    }

    speak(text, langCode = 'en') {
        if (!this.synthesisSupported || !this.ttsEnabled) return;

        window.speechSynthesis.cancel();

        // Strip markdown/emojis for clean voice synthesis
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
