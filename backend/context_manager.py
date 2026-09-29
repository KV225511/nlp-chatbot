"""
Context manager for session-based conversation tracking.
Enables context-aware follow-up suggestions and mood history.
"""

from datetime import datetime
from collections import defaultdict


class ContextManager:
    """
    Manages conversation context per session.
    Tracks message history, intents, and sentiment for:
    - Context-aware follow-up suggestions
    - Mood tracking dashboard data
    - Conversation export
    """
    
    # Intent relationship map for contextual follow-ups
    RELATED_INTENTS = {
        'black_holes': ['gravity', 'star_formation', 'supernova', 'milky_way'],
        'solar_system': ['mars_missions', 'jupiter_facts', 'saturn_rings', 'venus_mercury', 'uranus_neptune', 'dwarf_planets'],
        'mars_missions': ['solar_system', 'space_travel', 'alien_life', 'rocket_science'],
        'star_formation': ['supernova', 'nebulae', 'sun_facts', 'milky_way'],
        'moon_facts': ['eclipses', 'space_exploration_history', 'gravity'],
        'exoplanets': ['alien_life', 'telescopes', 'light_speed', 'star_formation'],
        'rocket_science': ['space_travel', 'iss_info', 'space_exploration_history', 'space_suits'],
        'iss_info': ['space_food', 'space_suits', 'space_careers', 'rocket_science'],
        'eclipses': ['moon_facts', 'sun_facts', 'constellations'],
        'gravity': ['black_holes', 'light_speed', 'big_bang', 'rocket_science'],
        'big_bang': ['dark_matter_energy', 'milky_way', 'light_speed', 'telescopes'],
        'dark_matter_energy': ['big_bang', 'milky_way', 'gravity', 'telescopes'],
        'supernova': ['star_formation', 'nebulae', 'black_holes', 'milky_way'],
        'nebulae': ['star_formation', 'supernova', 'milky_way', 'telescopes'],
        'milky_way': ['big_bang', 'dark_matter_energy', 'constellations', 'black_holes'],
        'saturn_rings': ['jupiter_facts', 'solar_system', 'alien_life'],
        'space_travel': ['rocket_science', 'light_speed', 'mars_missions', 'space_suits'],
        'asteroids_comets': ['solar_system', 'dwarf_planets', 'space_exploration_history'],
        'space_suits': ['iss_info', 'space_food', 'space_travel'],
        'alien_life': ['exoplanets', 'mars_missions', 'telescopes', 'dark_matter_energy'],
        'telescopes': ['exoplanets', 'nebulae', 'big_bang', 'constellations'],
        'space_exploration_history': ['rocket_science', 'moon_facts', 'mars_missions', 'iss_info'],
        'sun_facts': ['star_formation', 'space_weather', 'eclipses', 'solar_system'],
        'constellations': ['milky_way', 'telescopes', 'star_formation'],
        'space_food': ['iss_info', 'space_suits', 'mars_missions'],
        'jupiter_facts': ['saturn_rings', 'solar_system', 'alien_life', 'exoplanets'],
        'light_speed': ['gravity', 'big_bang', 'space_travel', 'dark_matter_energy'],
        'venus_mercury': ['solar_system', 'mars_missions', 'space_travel'],
        'uranus_neptune': ['solar_system', 'dwarf_planets', 'saturn_rings'],
        'dwarf_planets': ['solar_system', 'asteroids_comets', 'uranus_neptune'],
        'space_weather': ['sun_facts', 'iss_info', 'constellations'],
        'space_careers': ['rocket_science', 'space_exploration_history', 'iss_info'],
        'fun_space_facts': ['black_holes', 'solar_system', 'light_speed', 'alien_life'],
    }
    
    # Human-readable intent names for suggestions
    INTENT_LABELS = {
        'black_holes': 'Tell me about black holes',
        'solar_system': 'Solar system facts',
        'mars_missions': 'Mars missions',
        'star_formation': 'How are stars born?',
        'moon_facts': 'Moon facts',
        'exoplanets': 'Planets outside our solar system',
        'rocket_science': 'How do rockets work?',
        'iss_info': 'About the International Space Station',
        'eclipses': 'How do eclipses work?',
        'gravity': 'Explain gravity',
        'big_bang': 'How did the universe begin?',
        'dark_matter_energy': 'What is dark matter?',
        'supernova': 'What is a supernova?',
        'nebulae': 'Tell me about nebulae',
        'milky_way': 'Our Milky Way galaxy',
        'saturn_rings': 'Saturn and its rings',
        'space_travel': 'How long to travel in space?',
        'asteroids_comets': 'Asteroids and comets',
        'space_suits': 'How do space suits work?',
        'alien_life': 'Is there alien life?',
        'telescopes': 'About telescopes and JWST',
        'space_exploration_history': 'History of space exploration',
        'sun_facts': 'Facts about our Sun',
        'constellations': 'What are constellations?',
        'space_food': 'What do astronauts eat?',
        'jupiter_facts': 'Jupiter facts',
        'light_speed': 'Speed of light explained',
        'venus_mercury': 'Venus and Mercury',
        'uranus_neptune': 'Uranus and Neptune',
        'dwarf_planets': 'Pluto and dwarf planets',
        'space_weather': 'Space weather and auroras',
        'space_careers': 'Space careers',
        'fun_space_facts': 'Fun space facts',
        'breathing_exercise': 'Help me relax',
    }
    
    def __init__(self, max_history=10):
        """Initialize context manager with max history per session."""
        self.sessions = defaultdict(list)
        self.max_history = max_history
    
    def add_message(self, session_id, role, text, intent=None, sentiment=None):
        """
        Add a message to the session history.
        
        Args:
            session_id: Unique session identifier
            role: 'user' or 'bot'
            text: Message text
            intent: Predicted intent (for bot messages)
            sentiment: Sentiment analysis result (for user messages)
        """
        message = {
            'role': role,
            'text': text,
            'intent': intent,
            'sentiment': sentiment,
            'timestamp': datetime.now().isoformat()
        }
        
        self.sessions[session_id].append(message)
        
        # Keep only last max_history * 2 messages (user + bot pairs)
        if len(self.sessions[session_id]) > self.max_history * 2:
            self.sessions[session_id] = self.sessions[session_id][-(self.max_history * 2):]
    
    def get_context(self, session_id):
        """Get full conversation history for a session."""
        return self.sessions.get(session_id, [])
    
    def get_recent_intents(self, session_id, n=3):
        """Get the last n intents discussed."""
        history = self.sessions.get(session_id, [])
        intents = [
            msg['intent'] for msg in history 
            if msg.get('intent') and msg['intent'] not in ('greeting', 'goodbye', 'thanks', 'about_bot', 'fallback', 'breathing_exercise', 'web_search')
        ]
        return intents[-n:]
    
    def get_context_suggestions(self, session_id, current_intent, max_suggestions=3):
        """
        Generate context-aware follow-up suggestions based on conversation flow.
        
        Args:
            session_id: Session identifier
            current_intent: The intent just predicted
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of suggestion strings
        """
        recent_intents = self.get_recent_intents(session_id)
        discussed = set(recent_intents + [current_intent])
        
        # Get related intents for the current topic
        related = self.RELATED_INTENTS.get(current_intent, [])
        
        # Filter out already-discussed intents
        suggestions = []
        for intent in related:
            if intent not in discussed and intent in self.INTENT_LABELS:
                suggestions.append(self.INTENT_LABELS[intent])
                if len(suggestions) >= max_suggestions:
                    break
        
        return suggestions
    
    def get_mood_history(self, session_id):
        """
        Get sentiment scores over the conversation for the mood chart.
        
        Returns:
            List of dicts with timestamp and compound score
        """
        history = self.sessions.get(session_id, [])
        mood_data = []
        
        for msg in history:
            if msg['role'] == 'user' and msg.get('sentiment'):
                mood_data.append({
                    'timestamp': msg['timestamp'],
                    'compound': msg['sentiment'].get('compound', 0),
                    'label': msg['sentiment'].get('label', 'neutral'),
                    'emoji': msg['sentiment'].get('emoji', '😐')
                })
        
        return mood_data
    
    def clear_session(self, session_id):
        """Clear a session's history."""
        if session_id in self.sessions:
            del self.sessions[session_id]


if __name__ == '__main__':
    # Test context manager
    cm = ContextManager()
    
    cm.add_message('test', 'user', 'Tell me about black holes', sentiment={'compound': 0.2, 'label': 'positive', 'emoji': '😊'})
    cm.add_message('test', 'bot', 'Black holes are...', intent='black_holes')
    
    suggestions = cm.get_context_suggestions('test', 'black_holes')
    print(f"Follow-up suggestions after 'black_holes': {suggestions}")
    
    mood = cm.get_mood_history('test')
    print(f"Mood history: {mood}")
