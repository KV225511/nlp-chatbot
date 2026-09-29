import React from 'react';

function getMatchLabel(confidence) {
    if (confidence >= 0.85) return { text: 'Strong match', className: 'confidence-high' };
    if (confidence >= 0.65) return { text: 'Good match', className: 'confidence-medium' };
    return { text: 'Partial match', className: 'confidence-low' };
}

export default function MessageItem({ message, onSpeak, onRetry }) {
    const isBot = message.sender === 'bot';
    const { source, confidence } = message;
    const showConfidence = isBot && source === 'knowledge_base' && typeof confidence === 'number';
    const confidencePercent = showConfidence ? Math.round(confidence * 100) : null;
    const match = showConfidence ? getMatchLabel(confidence) : null;
    const webSources = isBot && source === 'web' ? message.sources || [] : [];

    return (
        <div className={`message-row ${isBot ? 'bot-row' : 'user-row'}`}>
            <div className="message-avatar">
                {isBot ? '🤖' : '👨‍🚀'}
            </div>

            <div className="message-bubble-wrapper">
                <div className={`message-bubble ${isBot ? 'bot-bubble' : 'user-bubble'} ${message.isError ? 'error-bubble' : ''}`}>
                    <p className="message-text">{message.text}</p>
                </div>

                <div className="message-footer">
                    <span className="message-time">{message.timestamp}</span>

                    {/* Bot Voice Replay Button */}
                    {isBot && onSpeak && !message.isError && (
                        <button
                            className="speak-btn"
                            onClick={() => onSpeak(message.text)}
                            title="Listen to this response"
                            aria-label="Speak response"
                        >
                            🔊
                        </button>
                    )}

                    {/* Retry after a network error */}
                    {message.isError && onRetry && (
                        <button className="retry-btn" onClick={() => onRetry(message)}>
                            ↻ Retry
                        </button>
                    )}

                    {/* User Sentiment Badge */}
                    {!isBot && message.sentiment && (
                        <span className="user-sentiment-pill" title={`Mood: ${message.sentiment.label}`}>
                            {message.sentiment.emoji} {message.sentiment.label}
                        </span>
                    )}
                </div>

                {/* Knowledge base answer: match strength */}
                {showConfidence && (
                    <div
                        className="confidence-container"
                        title={`Match score ${confidencePercent}% for intent [${message.intent}]`}
                    >
                        <div className="confidence-label">
                            <span>📚 Knowledge base · <strong>{message.intent}</strong></span>
                            <span className="confidence-value">{match.text} · {confidencePercent}%</span>
                        </div>
                        <div className="confidence-bar-bg">
                            <div
                                className={`confidence-bar-fill ${match.className}`}
                                style={{ width: `${confidencePercent}%` }}
                            />
                        </div>
                    </div>
                )}

                {/* Web answer: where it came from */}
                {webSources.length > 0 && (
                    <div className="source-container">
                        <span className="source-badge source-web">🌐 Answered from the web</span>
                        {webSources.map((item) => (
                            <a
                                key={item.url}
                                className="source-link"
                                href={item.url}
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                {item.provider}: {item.title} ↗
                            </a>
                        ))}
                    </div>
                )}

                {/* Not a space question */}
                {isBot && source === 'off_topic' && (
                    <div className="source-container">
                        <span className="source-badge source-fallback">
                            🌌 I only answer space and astronomy questions
                        </span>
                    </div>
                )}

                {/* Nothing found anywhere */}
                {isBot && source === 'fallback' && (
                    <div className="source-container">
                        <span className="source-badge source-fallback">
                            🤔 Not in my database, and nothing found online
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
}
