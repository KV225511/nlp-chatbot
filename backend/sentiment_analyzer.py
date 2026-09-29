"""
Sentiment analysis module using VADER.
Analyzes the emotional tone of user messages.
"""

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False


class SentimentAnalyzer:
    """
    Analyzes sentiment of user input using VADER.
    VADER (Valence Aware Dictionary and sEntiment Reasoner) is specifically
    designed for short texts/social media, making it ideal for chat messages.
    """
    
    def __init__(self):
        if VADER_AVAILABLE:
            self.analyzer = SentimentIntensityAnalyzer()
        else:
            self.analyzer = None
            print("⚠️ VADER not available. Sentiment analysis disabled.")
    
    def analyze(self, text):
        """
        Analyze sentiment of text.
        
        Args:
            text: Input text string
            
        Returns:
            dict with: compound, label, emoji, scores
        """
        if not self.analyzer:
            return {
                'compound': 0.0,
                'label': 'neutral',
                'emoji': '😐',
                'scores': {'pos': 0, 'neg': 0, 'neu': 1, 'compound': 0}
            }
        
        scores = self.analyzer.polarity_scores(text)
        compound = scores['compound']
        
        # Determine sentiment label with granularity
        if compound >= 0.5:
            label = 'very_positive'
            emoji = '😄'
        elif compound >= 0.05:
            label = 'positive'
            emoji = '😊'
        elif compound > -0.05:
            label = 'neutral'
            emoji = '😐'
        elif compound > -0.5:
            label = 'negative'
            emoji = '😟'
        else:
            label = 'very_negative'
            emoji = '😢'
        
        return {
            'compound': round(compound, 4),
            'label': label,
            'emoji': emoji,
            'scores': {
                'pos': round(scores['pos'], 4),
                'neg': round(scores['neg'], 4),
                'neu': round(scores['neu'], 4),
                'compound': round(scores['compound'], 4)
            }
        }


if __name__ == '__main__':
    analyzer = SentimentAnalyzer()
    test_texts = [
        "I love learning about space!",
        "Black holes are terrifying",
        "What is the speed of light",
        "This is amazing and wonderful!",
        "I'm scared of the vastness of space"
    ]
    for text in test_texts:
        result = analyzer.analyze(text)
        print(f"'{text}' → {result['emoji']} {result['label']} ({result['compound']})")
