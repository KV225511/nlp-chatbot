import React from 'react';

// Generated once when the module loads, so re-renders never move the stars
const STARS = Array.from({ length: 70 }, (_, i) => ({
    id: i,
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
    size: `${Math.random() * 2.5 + 1}px`,
    duration: `${Math.random() * 3 + 2}s`,
    delay: `${Math.random() * 3}s`
}));

/**
 * Animated twinkling starfield background with randomized stars
 */
export default function StarsBackground() {
    return (
        <div className="stars-container" aria-hidden="true">
            {STARS.map((star) => (
                <div
                    key={star.id}
                    className="star"
                    style={{
                        left: star.left,
                        top: star.top,
                        width: star.size,
                        height: star.size,
                        animationDuration: star.duration,
                        animationDelay: star.delay
                    }}
                />
            ))}
            <div className="nebula-glow nebula-1" />
            <div className="nebula-glow nebula-2" />
        </div>
    );
}
