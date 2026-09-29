import React from 'react';

export default function TypingIndicator() {
    return (
        <div className="message-row bot-row typing-row">
            <div className="message-avatar">🤖</div>
            <div className="typing-bubble">
                <span className="dot dot-1"></span>
                <span className="dot dot-2"></span>
                <span className="dot dot-3"></span>
                <span className="typing-text">CosmosBot is computing...</span>
            </div>
        </div>
    );
}
