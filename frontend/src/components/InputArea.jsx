import React, { useEffect, useRef, useState } from 'react';

const PLACEHOLDERS = {
    'en': 'Ask me about black holes, rockets, planets, or the cosmos...',
    'hi': 'ब्लैक होल, रॉकेट, ग्रहों या ब्रह्मांड के बारे में पूछें...',
    'ta': 'கருந்துளைகள், ராக்கெட்டுகள், கிரகங்கள் பற்றி கேளுங்கள்...',
    'te': 'బ్లాక్ హోల్స్, రాకెట్లు, గ్రహాల గురించి అడగండి...',
    'es': 'Pregúntame sobre agujeros negros, cohetes, planetas...',
    'fr': 'Posez des questions sur les trous noirs, les fusées...',
    'de': 'Fragen Sie über Schwarze Löcher, Raketen, Planeten...',
    'ja': 'ブラックホール、ロケット、惑星について質問してください...',
    'ko': '블랙홀, 로켓, 행성에 대해 질문하세요...',
    'zh-cn': '问我关于黑洞、火箭、行星或宇宙的问题...',
    'bn': 'ব্ল্যাক হোল, রকেট বা গ্রহ সম্পর্কে জিজ্ঞাসা করুন...',
    'mr': 'कृष्णविवर, रॉकेट किंवा ग्रहांबद्दल विचारा...'
};

export default function InputArea({
    onSendMessage,
    isListening,
    onToggleListen,
    isTTSEnabled,
    onToggleTTS,
    language,
    disabled
}) {
    const [inputValue, setInputValue] = useState('');
    const inputRef = useRef(null);

    // Put the cursor back in the box as soon as the bot has answered
    useEffect(() => {
        if (!disabled) inputRef.current?.focus();
    }, [disabled]);

    const handleSubmit = (e) => {
        e.preventDefault();
        const trimmed = inputValue.trim();
        if (trimmed && !disabled) {
            onSendMessage(trimmed);
            setInputValue('');
        }
    };

    const placeholderText = PLACEHOLDERS[language] || PLACEHOLDERS['en'];

    return (
        <footer className="input-bar-container glass-panel">
            <form onSubmit={handleSubmit} className="input-form">
                {/* Voice Output Toggle */}
                <button
                    type="button"
                    className={`voice-tts-toggle ${isTTSEnabled ? 'active' : ''}`}
                    onClick={onToggleTTS}
                    title={isTTSEnabled ? 'Voice output (TTS) is ON' : 'Voice output (TTS) is OFF'}
                    aria-label="Toggle voice output"
                >
                    {isTTSEnabled ? '🔈' : '🔇'}
                </button>

                {/* Text input */}
                <input
                    ref={inputRef}
                    type="text"
                    className="chat-text-input"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder={isListening ? 'Listening to your voice...' : placeholderText}
                    maxLength={500}
                    autoComplete="off"
                    aria-label="Type your question"
                />

                {/* Speech Input (Microphone) */}
                <button
                    type="button"
                    className={`mic-button ${isListening ? 'recording' : ''}`}
                    onClick={onToggleListen}
                    title={isListening ? 'Stop listening' : 'Speak via microphone (Speech Recognition)'}
                    aria-label="Toggle microphone input"
                >
                    <span className="mic-icon">🎤</span>
                </button>

                {/* Send Button */}
                <button
                    type="submit"
                    className="send-button"
                    disabled={!inputValue.trim() || disabled}
                    title="Send message"
                    aria-label="Send message"
                >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>
            </form>

            {/* Listening Banner */}
            {isListening && (
                <div className="listening-banner">
                    <span className="pulsing-record-dot"></span>
                    <span>Transcribing speech in real-time... Speak now</span>
                </div>
            )}
        </footer>
    );
}
