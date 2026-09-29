import React, { useEffect, useRef } from 'react';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

export default function MoodModal({ isOpen, onClose, moodHistory, theme }) {
    const chartRef = useRef(null);
    const chartInstance = useRef(null);

    useEffect(() => {
        if (!isOpen || !chartRef.current || !moodHistory || moodHistory.length === 0) return;

        if (chartInstance.current) {
            chartInstance.current.destroy();
        }

        const isDark = theme === 'dark';
        const textColor = isDark ? '#c4b5fd' : '#4338ca';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)';

        const labels = moodHistory.map((_, idx) => `Msg ${idx + 1}`);
        const data = moodHistory.map((item) => item.compound || 0);

        const pointColors = moodHistory.map((item) => {
            const comp = item.compound || 0;
            if (comp > 0.05) return '#10b981'; // positive
            if (comp < -0.05) return '#ef4444'; // negative
            return '#f59e0b'; // neutral
        });

        const ctx = chartRef.current.getContext('2d');
        chartInstance.current = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Sentiment Valence',
                        data,
                        borderColor: '#7c6aef',
                        backgroundColor: 'rgba(124, 106, 239, 0.15)',
                        borderWidth: 2.5,
                        pointBackgroundColor: pointColors,
                        pointBorderColor: pointColors,
                        pointRadius: 6,
                        pointHoverRadius: 9,
                        fill: true,
                        tension: 0.35
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        min: -1,
                        max: 1,
                        ticks: {
                            color: textColor,
                            stepSize: 0.5,
                            callback: (val) => {
                                if (val === 1) return '😄 (+1.0)';
                                if (val === 0.5) return '😊 (+0.5)';
                                if (val === 0) return '😐 (0.0)';
                                if (val === -0.5) return '😟 (-0.5)';
                                if (val === -1) return '😢 (-1.0)';
                                return '';
                            }
                        },
                        grid: { color: gridColor }
                    },
                    x: {
                        ticks: { color: textColor },
                        grid: { color: gridColor }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const item = moodHistory[context.dataIndex];
                                return `${item.emoji || ''} ${item.label || 'neutral'} (${(item.compound || 0).toFixed(3)})`;
                            }
                        }
                    }
                }
            }
        });

        return () => {
            if (chartInstance.current) {
                chartInstance.current.destroy();
            }
        };
    }, [isOpen, moodHistory, theme]);

    if (!isOpen) return null;

    const count = moodHistory.length;
    const avgScore = count > 0 ? (moodHistory.reduce((a, b) => a + (b.compound || 0), 0) / count).toFixed(3) : '0.000';

    let moodSummaryText = 'Neutral 😐';
    if (avgScore > 0.2) moodSummaryText = 'Very Positive 😄';
    else if (avgScore > 0.05) moodSummaryText = 'Positive 😊';
    else if (avgScore < -0.2) moodSummaryText = 'Negative 😟';
    else if (avgScore < -0.05) moodSummaryText = 'Slightly Negative 😕';

    return (
        <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
            <div className="modal-card glass-panel" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <div className="modal-title-row">
                        <span className="modal-icon">📈</span>
                        <h2>Sentiment & Mood Dashboard</h2>
                    </div>
                    <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">×</button>
                </div>

                <div className="modal-body">
                    <div className="mood-kpi-grid">
                        <div className="kpi-card">
                            <span className="kpi-label">Analyzed Turns</span>
                            <span className="kpi-value">{count}</span>
                        </div>
                        <div className="kpi-card">
                            <span className="kpi-label">Avg Sentiment</span>
                            <span className="kpi-value">{avgScore}</span>
                        </div>
                        <div className="kpi-card">
                            <span className="kpi-label">Current Tone</span>
                            <span className="kpi-value">{moodSummaryText}</span>
                        </div>
                    </div>

                    <div className="chart-wrapper">
                        {count === 0 ? (
                            <div className="empty-chart-placeholder">
                                <p>🚀 Send messages to CosmosBot to generate live sentiment tracking!</p>
                            </div>
                        ) : (
                            <canvas ref={chartRef} />
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
