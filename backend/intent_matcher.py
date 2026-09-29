"""
TF-IDF pattern matcher for CosmosBot.

Gives a second opinion next to the neural network: how close is the user's
question to a pattern that actually exists in intents.json? The neural
network's softmax is close to 100% even for questions the dataset does not
cover, so this similarity is what decides "I know this" vs "search the web".
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from model.preprocessing import clean_text


class IntentMatcher:
    """Character n-gram TF-IDF nearest-pattern lookup."""

    def __init__(self, intents_data):
        self.patterns = []
        self.tags = []
        for intent in intents_data['intents']:
            for pattern in intent['patterns']:
                cleaned = clean_text(pattern)
                if cleaned:
                    self.patterns.append(cleaned)
                    self.tags.append(intent['tag'])

        # char_wb n-grams tolerate typos and plural/singular differences
        self.vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4), sublinear_tf=True)
        self.pattern_matrix = self.vectorizer.fit_transform(self.patterns)

    def best_match(self, cleaned_text):
        """
        Args:
            cleaned_text: text already passed through clean_text()

        Returns:
            (tag, similarity) of the closest pattern; similarity is in [0, 1]
        """
        if not cleaned_text.strip():
            return None, 0.0
        similarities = cosine_similarity(self.vectorizer.transform([cleaned_text]), self.pattern_matrix)[0]
        best = int(similarities.argmax())
        return self.tags[best], float(similarities[best])
