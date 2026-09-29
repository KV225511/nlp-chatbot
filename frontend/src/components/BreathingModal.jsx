import React, { useState, useEffect, useRef } from 'react';

export default function BreathingModal({ isOpen, onClose }) {
    const [isRunning, setIsRunning] = useState(false);
    const [phase, setPhase] = useState('ready'); // 'ready', 'in', 'hold', 'out', 'done'
    const [timer, setTimer] = useState(4);
    const timeouts = useRef([]);

    const clearAllTimers = () => {
        timeouts.current.forEach((id) => clearTimeout(id));
        timeouts.current = [];
    };

    useEffect(() => {
        return () => clearAllTimers();
    }, []);

    const startBreathing = (cycles = 3) => {
        clearAllTimers();
        setIsRunning(true);
        let cycleCount = 0;

        const executeCycle = () => {
            if (cycleCount >= cycles) {
                setPhase('done');
                setIsRunning(false);
                return;
            }
            cycleCount++;

            // Phase 1: Inhale (4s)
            setPhase('in');
            setTimer(4);

            const tIn = setTimeout(() => {
                // Phase 2: Hold (7s)
                setPhase('hold');
                setTimer(7);

                const tHold = setTimeout(() => {
                    // Phase 3: Exhale (8s)
                    setPhase('out');
                    setTimer(8);

                    const tOut = setTimeout(() => {
                        executeCycle();
                    }, 8000);
                    timeouts.current.push(tOut);
                }, 7000);
                timeouts.current.push(tHold);
            }, 4000);
            timeouts.current.push(tIn);
        };

        executeCycle();
    };

    // Countdown interval effect
    useEffect(() => {
        if (!isRunning || phase === 'ready' || phase === 'done') return;

        const interval = setInterval(() => {
            setTimer((prev) => (prev > 1 ? prev - 1 : 1));
        }, 1000);

        return () => clearInterval(interval);
    }, [isRunning, phase]);

    const handleStop = () => {
        clearAllTimers();
        setIsRunning(false);
        setPhase('ready');
    };

    const handleClose = () => {
        handleStop();
        onClose();
    };

    if (!isOpen) return null;

    let instruction = 'Ready to align your cosmic breath?';
    let circleClass = '';
    if (phase === 'in') {
        instruction = 'Inhale deeply as stardust expands... (4s)';
        circleClass = 'breathe-in';
    } else if (phase === 'hold') {
        instruction = 'Hold your breath gently in zero gravity... (7s)';
        circleClass = 'breathe-hold';
    } else if (phase === 'out') {
        instruction = 'Exhale slowly into the infinite cosmos... (8s)';
        circleClass = 'breathe-out';
    } else if (phase === 'done') {
        instruction = 'Wonderful! You are centered with the universe. 🌟';
    }

    return (
        <div className="modal-backdrop" onClick={handleClose} role="dialog" aria-modal="true">
            <div className="modal-card breathing-modal glass-panel" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <div className="modal-title-row">
                        <span className="modal-icon">🧘</span>
                        <h2>Cosmic Breathing (4-7-8)</h2>
                    </div>
                    <button className="modal-close-btn" onClick={handleClose} aria-label="Close modal">×</button>
                </div>

                <div className="breathing-content">
                    <p className="breathing-instruction">{instruction}</p>

                    <div className="breathing-stage">
                        <div className={`breathing-circle-outer ${circleClass}`}>
                            <div className="breathing-circle-inner">
                                <span className="breathing-timer-number">
                                    {isRunning && phase !== 'done' ? timer : '✨'}
                                </span>
                                <span className="breathing-phase-text">
                                    {phase === 'in' && 'Breathe In'}
                                    {phase === 'hold' && 'Hold'}
                                    {phase === 'out' && 'Breathe Out'}
                                    {phase === 'ready' && '4-7-8'}
                                    {phase === 'done' && 'Peace'}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="breathing-actions">
                        {!isRunning ? (
                            <button className="action-button-primary" onClick={() => startBreathing(3)}>
                                {phase === 'done' ? 'Repeat Exercise' : 'Start Cosmic Breathing'}
                            </button>
                        ) : (
                            <button className="action-button-secondary" onClick={handleStop}>
                                Stop Exercise
                            </button>
                        )}
                    </div>
                    <p className="breathing-subtext">Clinically proven relaxation technique combined with deep space visualization.</p>
                </div>
            </div>
        </div>
    );
}
