"""
Web search fallback for CosmosBot.

When a question is not covered by intents.json, CosmosBot looks it up online:
1. Wikipedia (search API + page summary API) — free, no API key
2. DuckDuckGo Instant Answer API — free, no API key (used if Wikipedia finds nothing)

Environment variables:
    WEB_SEARCH_ENABLED   "true" (default) or "false"
    WEB_SEARCH_TIMEOUT   seconds per HTTP request (default 6)
"""

import os
import re
from urllib.parse import quote

import requests

USER_AGENT = 'CosmosBot/1.0 (https://github.com/kv225511/nlp-chatbot; educational-space-bot)'
WIKI_API = 'https://en.wikipedia.org/w/api.php'
WIKI_SUMMARY = 'https://en.wikipedia.org/api/rest_v1/page/summary/'
DDG_API = 'https://api.duckduckgo.com/'

MAX_SENTENCES = 3
MAX_CHARS = 700
CACHE_SIZE = 256

# Question prefixes and suffixes to strip so the search engine receives the core topic
QUESTION_PREFIX = re.compile(
    r"^(please\s+)?(can you\s+|could you\s+)?"
    r"(tell me (more )?about|what is|what's|what are|what was|what were|who is|who's|who are|"
    r"who was|who were|explain|describe|define|give me (some )?(info|information) (on|about)|"
    r"i want to know about|do you know about|search for|search|look up|more about|"
    r"how many|how much|how long|how far|how big|how fast|how old|"
    r"how does|how do|how did|how can|how is|how are|"
    r"why is|why are|why do|why does|why did|"
    r"where is|where are|when was|when did|when is|"
    r"which is|which are|list of|name of)\s+",
    re.IGNORECASE
)
QUESTION_SUFFIX = re.compile(
    r"\s+(are there(\s+in\s+the\s*world)?|in\s+the\s*world|in\s+the\s*universe|in\s+space|on\s+earth|around\s+the\s*world|exist(s)?|right\s+now|today|of\s+all\s+time|in\s+history)[\s\?\!\.]*$",
    re.IGNORECASE
)
LEADING_ARTICLE = re.compile(r"^(the|a|an)\s+", re.IGNORECASE)

# Messages made only of these words are small talk, not questions to look up
SMALL_TALK_WORDS = {
    'ok', 'okay', 'k', 'cool', 'nice', 'great', 'good', 'awesome', 'wow', 'lol', 'haha', 'hmm',
    'hm', 'yes', 'yeah', 'yep', 'no', 'nope', 'nah', 'sure', 'fine', 'right', 'alright', 'thx',
    'ty', 'please', 'so', 'and', 'oh', 'ah', 'uh', 'um', 'really', 'very', 'interesting', 'amazing'
}


# CosmosBot only answers space and astronomy questions. A web result is used only if
# its title/description contains one of these words, or its summary contains two.
SPACE_KEYWORDS = {
    # Core disciplines & concepts
    'space', 'astronomy', 'astronomical', 'astronomer', 'astronomers', 'astrophysics', 'astrophysicist',
    'astrophysicists', 'astronaut', 'astronauts', 'cosmonaut', 'cosmonauts', 'taikonaut', 'taikonauts',
    'cosmos', 'cosmology', 'cosmic', 'universe', 'galaxy', 'galaxies', 'galactic', 'intergalactic',
    'deep space', 'outer space', 'interstellar', 'interplanetary', 'celestial',

    # Celestial bodies & structures
    'planet', 'planets', 'planetary', 'exoplanet', 'exoplanets', 'moon', 'moons', 'lunar',
    'solar', 'sun', 'star', 'stars', 'stellar', 'supernova', 'supernovae', 'nebula', 'nebulae',
    'constellation', 'constellations', 'comet', 'comets', 'asteroid', 'asteroids',
    'meteor', 'meteorite', 'meteoroid', 'meteoroids', 'orbit', 'orbital', 'orbiter',
    'black hole', 'black holes', 'singularity', 'event horizon', 'neutron star', 'neutron stars',
    'pulsar', 'pulsars', 'quasar', 'quasars', 'white dwarf', 'red giant', 'brown dwarf', 'magnetar',

    # Solar system members
    'mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto',
    'ceres', 'kuiper belt', 'oort cloud', 'milky way', 'andromeda', 'proxima centauri',
    'alpha centauri', 'europa', 'titan', 'enceladus', 'ganymede', 'callisto', 'io',

    # Spaceflight, hardware, agencies, & operations
    'space agency', 'space agencies', 'space administration', 'space program', 'space programs',
    'space exploration', 'space mission', 'space missions', 'space system', 'space systems',
    'space science', 'space technology', 'space flight', 'spaceflight', 'human spaceflight',
    'spacecraft', 'satellite', 'satellites', 'rocket', 'rockets', 'rocketry',
    'launch vehicle', 'launch vehicles', 'space station', 'space stations',
    'space probe', 'space probes', 'probe', 'probes', 'rover', 'rovers', 'lander', 'landers',
    'telescope', 'telescopes', 'observatory', 'observatories', 'space telescope', 'space suit',
    'spacesuit', 'spacewalk', 'space walk', 'space travel', 'space weather', 'space debris',
    'aerospace', 'propulsion', 'space force',

    # Agencies & organizations
    'nasa', 'isro', 'esa', 'spacex', 'roscosmos', 'jaxa', 'cnsa', 'cnes', 'dlr', 'asi',
    'uk space agency', 'canadian space agency', 'blue origin', 'rocket lab', 'virgin galactic',

    # Famous missions & equipment
    'international space station', 'iss', 'artemis', 'apollo', 'chandrayaan', 'mangalyaan',
    'gaganyaan', 'aditya-l1', 'hubble', 'webb', 'james webb', 'jwst', 'voyager', 'cassini',
    'curiosity', 'perseverance', 'new horizons',

    # Astrophysical phenomena
    'big bang', 'dark matter', 'dark energy', 'gravity', 'gravitational wave',
    'gravitational waves', 'speed of light', 'light-year', 'light year', 'light-years',
    'parsec', 'parsecs', 'redshift', 'cosmic microwave background', 'solar flare',
    'eclipse', 'eclipses', 'solar eclipse', 'lunar eclipse'
}
_KEYWORD_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(SPACE_KEYWORDS, key=len, reverse=True)) + r")\b"
)


# Words that also mean something else (Mercury poisoning, Rocket League, Space Jam, personal space).
# A title containing only one of these is not enough on its own.
AMBIGUOUS_KEYWORDS = {
    'space', 'mercury', 'rocket', 'sun', 'star', 'stars', 'moon', 'moons', 'probe',
    'apollo', 'mars', 'webb', 'cosmos', 'universe', 'solar', 'orbit', 'gravity', 'esa', 'earth'
}


# Entertainment/media pages are rejected unless the description itself is clearly about space
# (so "Space Jam" is refused but "Interstellar (film)" style pages need a strong space word).
MEDIA_WORDS = re.compile(
    r"\b(film|movie|video game|album|song|band|television|tv series|sitcom|novel|newspaper|"
    r"magazine|anime|comic|musician|singer|actor|actress|footballer|cricketer|"
    r"businessman|entrepreneur|industrialist|politician|banker|investor)\b"
)


def is_space_topic(title, description, extract):
    """
    True if a search result is about space or astronomy:
    - title/description has an unambiguous space word, or
    - combined text contains at least two different space words.
    """
    headline = set(_KEYWORD_PATTERN.findall(f"{title} {description}".lower()))
    if headline - AMBIGUOUS_KEYWORDS:
        return True
    if MEDIA_WORDS.search(f"{description} {(extract or '')[:160]}".lower()):
        return False
    everything = headline | set(_KEYWORD_PATTERN.findall((extract or '').lower()))
    return len(everything) >= 2


def is_user_query_space_related(question):
    """
    Checks whether the user's question itself mentions space or astronomy concepts.
    If True, the question is legitimate space discussion and should NEVER be
    dismissed with an off-topic refusal.
    """
    cleaned = question.lower()
    matches = set(_KEYWORD_PATTERN.findall(cleaned))
    if matches - AMBIGUOUS_KEYWORDS:
        return True
    return bool(matches)


def is_small_talk(text):
    """True for messages like "ok cool" or "lol" that should never be searched."""
    words = re.findall(r"[a-z']+", text.lower())
    return not words or all(word in SMALL_TALK_WORDS for word in words)


def build_search_query(question):
    """Strip question words, fillers, and punctuation so the search engine gets the core topic."""
    # Normalize common run-together words (e.g. 'intheworld' -> 'in the world')
    normalized = re.sub(r'\bin\s*the\s*world\b', 'in the world', question, flags=re.IGNORECASE)
    normalized = re.sub(r'\bintheworld\b', 'in the world', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\baroundtheworld\b', 'around the world', normalized, flags=re.IGNORECASE)

    query = normalized.strip().rstrip('?!.').strip()
    query = QUESTION_PREFIX.sub('', query)
    query = QUESTION_SUFFIX.sub('', query)
    query = LEADING_ARTICLE.sub('', query)
    return query.strip() or question.strip()


def _shorten(text):
    """Keep the first few sentences so the chat bubble stays readable."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    short = ' '.join(sentences[:MAX_SENTENCES])
    if len(short) > MAX_CHARS:
        short = short[:MAX_CHARS].rsplit(' ', 1)[0] + '…'
    return short


class WebSearchService:
    """Looks up questions the local model cannot answer."""

    def __init__(self):
        self.enabled = os.environ.get('WEB_SEARCH_ENABLED', 'true').lower() == 'true'
        self.timeout = float(os.environ.get('WEB_SEARCH_TIMEOUT', '6'))
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self._cache = {}  # successful results only, so network errors are retried

    def search(self, question):
        """
        Returns:
            dict { answer, title, url, provider } for a space-related result,
            {'off_topic': True} if results were found but none were about space,
            or None if nothing was found
        """
        if not self.enabled or not question or is_small_talk(question):
            return None

        user_is_asking_space = is_user_query_space_related(question)
        query = build_search_query(question).lower()

        if query in self._cache:
            cached = self._cache[query]
            if not (cached.get('off_topic') and user_is_asking_space):
                return cached

        # Try search with the cleaned query first, then original topic if different
        candidate_queries = [query]
        raw_query = question.strip().rstrip('?!.').strip().lower()
        if raw_query != query and len(raw_query.split()) <= 8:
            candidate_queries.append(raw_query)

        found_off_topic = False
        for q_try in candidate_queries:
            for provider in (self._search_wikipedia, self._search_duckduckgo):
                try:
                    result = provider(q_try)
                except (requests.RequestException, ValueError, KeyError) as e:
                    print(f"Web search error ({provider.__name__}): {e}")
                    result = None

                if result and not result.get('off_topic'):
                    if len(self._cache) >= CACHE_SIZE:
                        self._cache.pop(next(iter(self._cache)))
                    self._cache[query] = result
                    return result
                elif result and result.get('off_topic'):
                    found_off_topic = True
                    # If Wikipedia explicitly confirmed this entity exists and is off-topic,
                    # do not let backup DDG override with incidental mentions in text
                    if provider == self._search_wikipedia:
                        break

        # If the user explicitly asked about space, NEVER classify as off-topic!
        # Returning None allows CosmosBot to use its space fallback instead of refusing.
        if user_is_asking_space:
            return None

        if found_off_topic:
            res = {'off_topic': True}
            self._cache[query] = res
            return res

        return None

    def _search_wikipedia(self, query):
        response = self.session.get(WIKI_API, params={
            'action': 'query', 'list': 'search', 'srsearch': query,
            'srlimit': 5, 'format': 'json'
        }, timeout=self.timeout)
        response.raise_for_status()
        hits = response.json().get('query', {}).get('search', [])
        found_off_topic = False

        for hit in hits:
            title = hit['title']
            summary = self.session.get(
                WIKI_SUMMARY + quote(title.replace(' ', '_'), safe=''),
                timeout=self.timeout
            )
            if summary.status_code != 200:
                continue
            data = summary.json()
            if data.get('type') == 'disambiguation' or not data.get('extract'):
                continue
            if not is_space_topic(data.get('title', title), data.get('description', ''), data['extract']):
                found_off_topic = True
                continue
            return {
                'answer': _shorten(data['extract']),
                'title': data.get('title', title),
                'url': data.get('content_urls', {}).get('desktop', {}).get(
                    'page', f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
                ),
                'provider': 'Wikipedia'
            }
        return {'off_topic': True} if found_off_topic else None

    def _search_duckduckgo(self, query):
        response = self.session.get(DDG_API, params={
            'q': query, 'format': 'json', 'no_html': 1, 'skip_disambig': 1
        }, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        text = data.get('AbstractText') or data.get('Answer')
        if not text:
            return None
        if not is_space_topic(data.get('Heading', ''), '', text):
            return {'off_topic': True}
        return {
            'answer': _shorten(text),
            'title': data.get('Heading') or query,
            'url': data.get('AbstractURL') or f"https://duckduckgo.com/?q={quote(query)}",
            'provider': data.get('AbstractSource') or 'DuckDuckGo'
        }


if __name__ == '__main__':
    service = WebSearchService()
    for q in ["What is ISRO?", "Tell me about Chandrayaan 3", "Why is Mars red", "ok cool"]:
        result = service.search(q)
        print(f"\n{q} -> query '{build_search_query(q)}'")
        print(result)
