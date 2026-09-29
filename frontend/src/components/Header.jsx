import React from 'react';

export default function Header({
    theme,
    onToggleTheme,
    isMuted,
    onToggleSound,
    onOpenMood,
    onExportPDF,
    onClearChat,
    language,
    onChangeLanguage,
    currentMood
}) {
    return (
        <header className="chat-header glass-panel">
            <div className="header-left">
                <div className="bot-avatar-header">
                    <span role="img" aria-label="rocket">🚀</span>
                </div>
                <div className="bot-info">
                    <div className="title-row">
                        <h1 className="bot-name">CosmosBot</h1>
                        <span className="ai-badge">Deep Learning</span>
                    </div>
                    <span className="bot-status">
                        <span className="status-dot"></span>
                        Online — Space Explorer AI
                    </span>
                </div>
            </div>

            <div className="header-actions">
                {/* Live Mood Badge */}
                <button
                    className="header-action-btn mood-indicator-btn"
                    onClick={onOpenMood}
                    title="View Mood Dashboard"
                    aria-label="Mood Dashboard"
                >
                    <span className="mood-emoji">{currentMood?.emoji || '😐'}</span>
                    <span className="mood-text-label">Mood</span>
                </button>

                {/* Language Selector */}
                <select
                    className="language-selector"
                    value={language}
                    onChange={(e) => onChangeLanguage(e.target.value)}
                    title="Select Language"
                    aria-label="Select Language"
                >
                    <option value="en">🇬🇧 EN</option>
                    <option value="hi">🇮🇳 HI</option>
                    <option value="ta">🇮🇳 TA</option>
                    <option value="te">🇮🇳 TE</option>
                    <option value="es">🇪🇸 ES</option>
                    <option value="fr">🇫🇷 FR</option>
                    <option value="de">🇩🇪 DE</option>
                    <option value="ja">🇯🇵 JA</option>
                    <option value="ko">🇰🇷 KO</option>
                    <option value="zh-cn">🇨🇳 ZH</option>
                    <option value="bn">🇮🇳 BN</option>
                    <option value="mr">🇮🇳 MR</option>
                </select>

                {/* Sound Effects Toggle */}
                <button
                    className={`header-action-btn ${isMuted ? 'muted' : ''}`}
                    onClick={onToggleSound}
                    title={isMuted ? 'Unmute sound effects' : 'Mute sound effects'}
                    aria-label="Toggle Sound Effects"
                >
                    {isMuted ? '🔇' : '🔊'}
                </button>

                {/* Clear Conversation */}
                <button
                    className="header-action-btn"
                    onClick={onClearChat}
                    title="Start a new conversation"
                    aria-label="Start a new conversation"
                >
                    🗑️
                </button>

                {/* Export PDF Button */}
                <button
                    className="header-action-btn"
                    onClick={onExportPDF}
                    title="Export Conversation as PDF"
                    aria-label="Export Conversation as PDF"
                >
                    📄
                </button>

                {/* Theme Toggle (Dark/Light) */}
                <button
                    className="header-action-btn theme-toggle-btn"
                    onClick={onToggleTheme}
                    title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
                    aria-label="Toggle Theme"
                >
                    {theme === 'dark' ? '☀️' : '🌙'}
                </button>
            </div>
        </header>
    );
}
