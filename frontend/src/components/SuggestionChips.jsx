import React from 'react';

const EMOJI_MAP = {
    'black hole': '🕳️',
    'solar': '🪐',
    'rocket': '🚀',
    'mars': '🔴',
    'moon': '🌙',
    'star': '⭐',
    'light': '⚡',
    'telescope': '🔭',
    'alien': '👽',
    'gravity': '🌌',
    'breathing': '🧘',
    'saturn': '🪐',
    'supernova': '💥',
    'galaxy': '🌌',
    'facts': '✨',
    'speed': '⚡'
};

function getEmojiForSuggestion(text) {
    const lower = text.toLowerCase();
    for (const [key, icon] of Object.entries(EMOJI_MAP)) {
        if (lower.includes(key)) return icon;
    }
    return '💫';
}

export default function SuggestionChips({ suggestions, onSelectSuggestion, disabled }) {
    if (!suggestions || suggestions.length === 0) return null;

    return (
        <div className="suggestion-chips-container">
            <div className="chips-scroll-area">
                {suggestions.slice(0, 5).map((suggestion, idx) => (
                    <button
                        key={`${suggestion}-${idx}`}
                        className="suggestion-chip"
                        onClick={() => onSelectSuggestion(suggestion)}
                        disabled={disabled}
                        title={`Ask: "${suggestion}"`}
                    >
                        <span className="chip-icon">{getEmojiForSuggestion(suggestion)}</span>
                        <span className="chip-text">{suggestion}</span>
                    </button>
                ))}
            </div>
        </div>
    );
}
