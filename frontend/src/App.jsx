import React, { useState, useEffect, useRef, lazy, Suspense } from 'react';
import './App.css';

import StarsBackground from './components/StarsBackground';
import Header from './components/Header';
import MessageItem from './components/MessageItem';
import TypingIndicator from './components/TypingIndicator';
import SuggestionChips from './components/SuggestionChips';
import InputArea from './components/InputArea';
import BreathingModal from './components/BreathingModal';

import { soundService } from './services/soundService';
import { speechService } from './services/speechService';
import { exportChatToPDF } from './services/exportService';

// Chart.js is only needed when the mood dashboard is opened
const MoodModal = lazy(() => import('./components/MoodModal'));

const INITIAL_SUGGESTIONS = [
    'Tell me about black holes',
    'Solar system facts',
    'How do rockets work',
    'What is ISRO?',
    'Fun space facts'
];

function generateSessionId() {
    return 'session-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9);
}

function getFormattedTime() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function createWelcomeMessage() {
    return {
        id: 'welcome-msg',
        sender: 'bot',
        text: "Welcome, Space Explorer! 🌌 I am CosmosBot, your AI guide to the universe powered by Deep Learning (CNN + BiGRU + Self-Attention). Ask me about black holes, rockets, planets, or telescopes — and if something isn't in my database, I'll search the web for you!",
        timestamp: getFormattedTime(),
        source: 'welcome'
    };
}

// In production (e.g. Vercel), VITE_API_URL points to the Render backend service.
// In local development, leaving it empty uses the Vite dev proxy or same-origin fallback.
const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

export default function App() {
    // Session ID
    const [sessionId, setSessionId] = useState(() => {
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
    const [messages, setMessages] = useState(() => [createWelcomeMessage()]);
    const [isTyping, setIsTyping] = useState(false);
    const [suggestions, setSuggestions] = useState(INITIAL_SUGGESTIONS);
    const [isListening, setIsListening] = useState(false);
    const [interimSpeech, setInterimSpeech] = useState('');

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

    const handleClearChat = () => {
        if (isTyping) return;
        soundService.play('click');
        speechService.stopListening();
        window.speechSynthesis?.cancel();

        const newId = generateSessionId();
        sessionStorage.setItem('cosmos_session_id', newId);
        setSessionId(newId);
        setMessages([createWelcomeMessage()]);
        setSuggestions(INITIAL_SUGGESTIONS);
        setMoodHistory([]);
        setCurrentMood({ compound: 0, emoji: '😐', label: 'neutral' });
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
            const res = await fetch(`${API_BASE_URL}/api/chat`, {
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

            // Short "thinking" pause for instant dataset answers (web answers are already slow)
            if (data.source !== 'web') {
                await new Promise((r) => setTimeout(r, Math.min(400 + data.response.length * 2, 900)));
            }

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
                intent: data.intent,
                source: data.source,
                sources: data.sources || []
            };

            setMessages((prev) => [...prev, botMsg]);
            soundService.play('receive');

            // Update dynamic suggestions (regular + context-aware), without duplicates
            const combinedSuggestions = [
                ...new Set([...(data.suggestions || []), ...(data.context_suggestions || [])])
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
                text: "Mission control warning: Could not communicate with server. (Note: If your Render backend was dormant, it can take ~45 seconds to spin up on first call). Please click retry below! 🛸",
                timestamp: getFormattedTime(),
                source: 'error',
                isError: true,
                retryText: text,
                failedMessageId: userMsg.id
            };
            setMessages((prev) => [...prev, errorMsg]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleRetry = (errorMsg) => {
        // Remove the failed question and the error, then ask again
        setMessages((prev) => prev.filter((m) => m.id !== errorMsg.id && m.id !== errorMsg.failedMessageId));
        handleSendMessage(errorMsg.retryText);
    };

    const handleToggleListen = () => {
        if (isListening) {
            speechService.stopListening();
            setIsListening(false);
            setInterimSpeech('');
            soundService.play('mic-stop');
        } else {
            setInterimSpeech('');
            const started = speechService.startListening(language, {
                onFinal: (transcription) => {
                    setIsListening(false);
                    setInterimSpeech('');
                    soundService.play('mic-stop');
                    if (transcription && transcription.trim()) {
                        handleSendMessage(transcription.trim());
                    }
                },
                onInterim: (text) => {
                    setInterimSpeech(text);
                },
                onError: (error) => {
                    setIsListening(false);
                    setInterimSpeech('');
                    soundService.play('error');
                    if (error === 'not-supported') {
                        alert('Speech recognition requires Chrome, Edge, or a Chromium browser.');
                    } else if (error === 'not-allowed' || error === 'permission-denied') {
                        alert('Microphone access is blocked! Please click the lock or camera icon in your browser address bar and allow microphone permissions for this site.');
                    } else if (error === 'no-speech') {
                        // User paused or no sound was captured
                        console.log('No speech detected during listening interval.');
                    } else if (error === 'network') {
                        console.warn('Speech recognition network error — Google speech servers unreachable.');
                        alert('Voice recognition could not connect to the speech service. If you are using Brave or an ad-blocker/firewall, please allow speech services in browser settings, or type your query in the box below!');
                    } else if (error !== 'aborted') {
                        console.warn('Voice transcription error:', error);
                    }
                },
                onEnd: () => {
                    setIsListening(false);
                    setInterimSpeech('');
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
                    onClearChat={handleClearChat}
                    language={language}
                    onChangeLanguage={handleChangeLanguage}
                    currentMood={currentMood}
                />

                <main className="messages-scroll-container" role="log" aria-live="polite" aria-label="Conversation">
                    {messages.map((msg) => (
                        <MessageItem
                            key={msg.id}
                            message={msg}
                            onSpeak={msg.sender === 'bot' ? handleSpeakMessage : null}
                            onRetry={handleRetry}
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
                    interimSpeech={interimSpeech}
                    onToggleListen={handleToggleListen}
                    isTTSEnabled={isTTSEnabled}
                    onToggleTTS={handleToggleTTS}
                    language={language}
                    disabled={isTyping}
                />
            </div>

            {isMoodModalOpen && (
                <Suspense fallback={null}>
                    <MoodModal
                        isOpen={isMoodModalOpen}
                        onClose={() => setIsMoodModalOpen(false)}
                        moodHistory={moodHistory}
                        theme={theme}
                    />
                </Suspense>
            )}

            <BreathingModal
                isOpen={isBreathingModalOpen}
                onClose={() => setIsBreathingModalOpen(false)}
            />
        </div>
    );
}
