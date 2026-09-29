import React, { useState, useEffect, useRef } from 'react';
import './App.css';

import StarsBackground from './components/StarsBackground';
import Header from './components/Header';
import MessageItem from './components/MessageItem';
import TypingIndicator from './components/TypingIndicator';
import SuggestionChips from './components/SuggestionChips';
import InputArea from './components/InputArea';
import MoodModal from './components/MoodModal';
import BreathingModal from './components/BreathingModal';

import { soundService } from './services/soundService';
import { speechService } from './services/speechService';
import { exportChatToPDF } from './services/exportService';

const INITIAL_SUGGESTIONS = [
    'Tell me about black holes',
    'Solar system facts',
    'How do rockets work',
    'James Webb Telescope',
    'Fun space facts'
];

function generateSessionId() {
    return 'session-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9);
}

function getFormattedTime() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function App() {
    // Session ID
    const [sessionId] = useState(() => {
        const stored = sessionStorage.getItem('cosmos_session_id');
        if (stored) return stored;
        const newId = generateSessionId();
        sessionStorage.setItem('cosmos_session_id', newId);
        return newId;
    });

    // Theme state ('dark' | 'light')
    const [theme, setTheme] = useState(() => localStorage.getItem('cosmos_theme') || 'dark');

    // Audio state
    const [isMuted, setIsMuted] = useState(() => soundService.isMuted());
    const [isTTSEnabled, setIsTTSEnabled] = useState(() => speechService.isTTSEnabled());

    // Language state
    const [language, setLanguage] = useState(() => localStorage.getItem('cosmos_lang') || 'en');

    // Mood tracking state
    const [currentMood, setCurrentMood] = useState({ compound: 0, emoji: '😐', label: 'neutral' });
    const [moodHistory, setMoodHistory] = useState([]);

    // Modals
    const [isMoodModalOpen, setIsMoodModalOpen] = useState(false);
    const [isBreathingModalOpen, setIsBreathingModalOpen] = useState(false);

    // Chat state
    const [messages, setMessages] = useState([
        {
            id: 'welcome-msg',
            sender: 'bot',
            text: "Welcome, Space Explorer! 🌌 I am CosmosBot, your AI guide to the universe powered by Deep Learning (CNN + BiGRU + Self-Attention). Ask me about black holes, rockets, planets, or telescopes!",
            timestamp: getFormattedTime(),
            confidence: 1.0,
            intent: 'greeting'
        }
    ]);
    const [isTyping, setIsTyping] = useState(false);
    const [suggestions, setSuggestions] = useState(INITIAL_SUGGESTIONS);
    const [isListening, setIsListening] = useState(false);

    const messagesEndRef = useRef(null);

    // Apply theme attribute to html document
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('cosmos_theme', theme);
    }, [theme]);

    // Scroll to bottom when messages or typing changes
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isTyping]);

    const handleToggleTheme = () => {
        const nextTheme = theme === 'dark' ? 'light' : 'dark';
        setTheme(nextTheme);
        soundService.play('click');
    };

    const handleToggleSound = () => {
        const muted = soundService.toggleMute();
        setIsMuted(muted);
    };

    const handleToggleTTS = () => {
        const enabled = speechService.toggleTTS();
        setIsTTSEnabled(enabled);
        soundService.play('click');
    };

    const handleChangeLanguage = (newLang) => {
        setLanguage(newLang);
        localStorage.setItem('cosmos_lang', newLang);
        soundService.play('click');
    };

    const handleSendMessage = async (text) => {
        if (!text.trim() || isTyping) return;

        soundService.play('send');

        // Optimistically add user message
        const userMsg = {
            id: 'msg-' + Date.now(),
            sender: 'user',
            text,
            timestamp: getFormattedTime(),
            sentiment: null
        };

        setMessages((prev) => [...prev, userMsg]);
        setIsTyping(true);

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    session_id: sessionId,
                    language
                })
            });

            if (!res.ok) {
                throw new Error(`API returned ${res.status}`);
            }

            const data = await res.json();

            // Simulate realistic neural typing delay
            await new Promise((r) => setTimeout(r, Math.min(500 + data.response.length * 4, 1300)));

            // Update user message sentiment in place
            if (data.sentiment) {
                setCurrentMood(data.sentiment);
                setMoodHistory((prev) => [...prev, { ...data.sentiment, time: getFormattedTime() }]);
                setMessages((prev) =>
                    prev.map((m) => (m.id === userMsg.id ? { ...m, sentiment: data.sentiment } : m))
                );
            }

            // Create bot message
            const botMsg = {
                id: 'msg-' + (Date.now() + 1),
                sender: 'bot',
                text: data.response,
                timestamp: getFormattedTime(),
                confidence: data.confidence,
                intent: data.intent
            };

            setMessages((prev) => [...prev, botMsg]);
            soundService.play('receive');

            // Update dynamic suggestions (regular + context-aware)
            const combinedSuggestions = [
                ...(data.suggestions || []),
                ...(data.context_suggestions || [])
            ];
            if (combinedSuggestions.length > 0) {
                setSuggestions(combinedSuggestions);
            }

            // Read aloud if TTS is enabled
            if (isTTSEnabled) {
                speechService.speak(data.response, language);
            }

            // Trigger cosmic breathing modal if bot recommends breathing
            if (data.trigger_breathing) {
                setTimeout(() => setIsBreathingModalOpen(true), 1200);
            }
        } catch (err) {
            console.error('Chat error:', err);
            soundService.play('error');
            const errorMsg = {
                id: 'err-' + Date.now(),
                sender: 'bot',
                text: "Mission control warning: Could not communicate with server. Please ensure the backend is running and try again! 🛸",
                timestamp: getFormattedTime(),
                confidence: 0,
                intent: 'error'
            };
            setMessages((prev) => [...prev, errorMsg]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleToggleListen = () => {
        if (isListening) {
            speechService.stopListening();
            setIsListening(false);
            soundService.play('mic-stop');
        } else {
            const started = speechService.startListening(language, {
                onFinal: (transcription) => {
                    setIsListening(false);
                    soundService.play('mic-stop');
                    handleSendMessage(transcription);
                },
                onInterim: () => {},
                onError: (error) => {
                    setIsListening(false);
                    if (error === 'not-supported') {
                        alert('Speech recognition is supported in Chrome, Edge, and Chromium browsers.');
                    }
                },
                onEnd: () => {
                    setIsListening(false);
                }
            });

            if (started) {
                setIsListening(true);
                soundService.play('mic-start');
            }
        }
    };

    const handleSpeakMessage = (text) => {
        speechService.speak(text, language);
    };

    const handleExportPDF = () => {
        soundService.play('click');
        exportChatToPDF(messages, moodHistory);
    };

    return (
        <div className="app-container">
            <StarsBackground />

            <div className="chat-window glass-panel">
                <Header
                    theme={theme}
                    onToggleTheme={handleToggleTheme}
                    isMuted={isMuted}
                    onToggleSound={handleToggleSound}
                    onOpenMood={() => {
                        soundService.play('click');
                        setIsMoodModalOpen(true);
                    }}
                    onExportPDF={handleExportPDF}
                    language={language}
                    onChangeLanguage={handleChangeLanguage}
                    currentMood={currentMood}
                />

                <main className="messages-scroll-container">
                    {messages.map((msg) => (
                        <MessageItem
                            key={msg.id}
                            message={msg}
                            onSpeak={msg.sender === 'bot' ? handleSpeakMessage : null}
                        />
                    ))}

                    {isTyping && <TypingIndicator />}
                    <div ref={messagesEndRef} />
                </main>

                <SuggestionChips
                    suggestions={suggestions}
                    onSelectSuggestion={handleSendMessage}
                    disabled={isTyping}
                />

                <InputArea
                    onSendMessage={handleSendMessage}
                    isListening={isListening}
                    onToggleListen={handleToggleListen}
                    isTTSEnabled={isTTSEnabled}
                    onToggleTTS={handleToggleTTS}
                    language={language}
                    disabled={isTyping}
                />
            </div>

            <MoodModal
                isOpen={isMoodModalOpen}
                onClose={() => setIsMoodModalOpen(false)}
                moodHistory={moodHistory}
                theme={theme}
            />

            <BreathingModal
                isOpen={isBreathingModalOpen}
                onClose={() => setIsBreathingModalOpen(false)}
            />
        </div>
    );
}
