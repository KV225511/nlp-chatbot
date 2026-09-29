import React, { useEffect, useState } from 'react';

export default function TypingIndicator() {
    const [isSlow, setIsSlow] = useState(false);

    // Web searches take longer than dataset answers, so tell the user after a moment
    useEffect(() => {
        const timer = setTimeout(() => setIsSlow(true), 1500);
        return () => clearTimeout(timer);
    }, []);

    return (
        <div className="message-row bot-row typing-row" role="status">
            <div className="message-avatar">🤖</div>
            <div className="typing-bubble">
                <span className="dot dot-1"></span>
                <span className="dot dot-2"></span>
                <span className="dot dot-3"></span>
                <span className="typing-text">
                    {isSlow ? 'Searching the web for an answer...' : 'CosmosBot is thinking...'}
                </span>
            </div>
        </div>
    );
}
