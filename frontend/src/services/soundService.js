/**
 * SoundService — Generates rich audio cues using Web Audio API synthesis.
 * Completely client-side with zero external audio assets.
 */
class SoundService {
    constructor() {
        this.audioCtx = null;
        this.muted = localStorage.getItem('cosmos_sound_muted') === 'true';
        this.volume = 0.25;
    }

    _ensureContext() {
        if (!this.audioCtx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                this.audioCtx = new AudioContext();
            }
        }
        if (this.audioCtx && this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }
    }

    play(soundName) {
        if (this.muted) return;
        this._ensureContext();
        if (!this.audioCtx) return;

        switch (soundName) {
            case 'send':
                this._playTone(740, 0.08, 'sine', 0.2);
                setTimeout(() => this._playTone(980, 0.09, 'sine', 0.18), 60);
                break;
            case 'receive':
                this._playTone(523, 0.09, 'sine', 0.15);
                setTimeout(() => this._playTone(659, 0.09, 'sine', 0.16), 80);
                setTimeout(() => this._playTone(880, 0.12, 'sine', 0.2), 160);
                break;
            case 'mic-start':
                this._playTone(440, 0.08, 'triangle', 0.18);
                setTimeout(() => this._playTone(660, 0.08, 'triangle', 0.2), 70);
                break;
            case 'mic-stop':
                this._playTone(660, 0.08, 'triangle', 0.18);
                setTimeout(() => this._playTone(440, 0.08, 'triangle', 0.15), 70);
                break;
            case 'click':
                this._playTone(1050, 0.03, 'sine', 0.08);
                break;
            case 'error':
                this._playTone(280, 0.12, 'sawtooth', 0.15);
                setTimeout(() => this._playTone(220, 0.16, 'sawtooth', 0.15), 100);
                break;
            default:
                break;
        }
    }

    _playTone(frequency, duration, type = 'sine', volume = 0.2) {
        try {
            const osc = this.audioCtx.createOscillator();
            const gain = this.audioCtx.createGain();

            osc.type = type;
            osc.frequency.setValueAtTime(frequency, this.audioCtx.currentTime);

            gain.gain.setValueAtTime(volume * this.volume, this.audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, this.audioCtx.currentTime + duration);

            osc.connect(gain);
            gain.connect(this.audioCtx.destination);

            osc.start(this.audioCtx.currentTime);
            osc.stop(this.audioCtx.currentTime + duration);
        } catch (e) {
            // Audio context safely ignored
        }
    }

    toggleMute() {
        this.muted = !this.muted;
        localStorage.setItem('cosmos_sound_muted', this.muted);
        return this.muted;
    }

    isMuted() {
        return this.muted;
    }
}

export const soundService = new SoundService();
