import React from 'react';

export default function MessageItem({ message, onSpeak }) {
    const isBot = message.sender === 'bot';
    const confidence = message.confidence;
    const confidencePercent = confidence !== undefined ? Math.round(confidence * 100) : null;

    let confidenceClass = 'confidence-high';
    if (confidence !== undefined) {
        if (confidence < 0.5) confidenceClass = 'confidence-low';
        else if (confidence < 0.75) confidenceClass = 'confidence-medium';
    }

    return (
        <div className={`message-row ${isBot ? 'bot-row' : 'user-row'}`}>
            <div className="message-avatar">
                {isBot ? '🤖' : '👨‍🚀'}
            </div>

            <div className="message-bubble-wrapper">
                <div className={`message-bubble ${isBot ? 'bot-bubble' : 'user-bubble'}`}>
                    <p className="message-text">{message.text}</p>
                </div>

                <div className="message-footer">
                    <span className="message-time">{message.timestamp}</span>

                    {/* Bot Voice Replay Button */}
                    {isBot && onSpeak && (
                        <button
                            className="speak-btn"
                            onClick={() => onSpeak(message.text)}
                            title="Listen to this response"
                            aria-label="Speak response"
                        >
                            🔊
                        </button>
                    )}

                    {/* User Sentiment Badge */}
                    {!isBot && message.sentiment && (
                        <span className="user-sentiment-pill" title={`Mood: ${message.sentiment.label}`}>
                            {message.sentiment.emoji} {message.sentiment.label}
                        </span>
                    )}
                </div>

                {/* Bot Confidence Score Bar */}
                {isBot && confidencePercent !== null && (
                    <div className="confidence-container" title={`Neural confidence: ${confidencePercent}% for intent [${message.intent || 'general'}]`}>
                        <div className="confidence-label">
                            <span>Intent: <strong>{message.intent || 'response'}</strong></span>
                            <span className="confidence-value">{confidencePercent}% confidence</span>
                        </div>
                        <div className="confidence-bar-bg">
                            <div
                                className={`confidence-bar-fill ${confidenceClass}`}
                                style={{ width: `${confidencePercent}%` }}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
