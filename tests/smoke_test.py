"""
Smoke test for CosmosBot's answer routing.

Run from the project root (needs internet for the web search part):
    python tests/smoke_test.py

Checks that:
- questions from intents.json are answered from the dataset with a stable score
- questions the dataset does not cover are NOT answered from the dataset
- web search finds ISRO / Chandrayaan-3, ignores small talk and refuses non-space topics
"""

import io
import os
import sys
import contextlib

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with contextlib.redirect_stdout(io.StringIO()):
    from backend.chatbot_engine import ChatbotEngine
    from backend.web_search import WebSearchService
    engine = ChatbotEngine()

KNOWN = {
    "Tell me about black holes": "black_holes",
    "Tell me about Apollo 11": "space_exploration_history",
    "What is the speed of light": "light_speed",
    "speed of light": "light_speed",
    "How do rockets work": "rocket_science",
    "how big is jupiter": "jupiter_facts",
    "Hello": "greeting",
    "Thanks": "thanks",
}
UNKNOWN = [
    "What is ISRO",
    "What is Chandrayaan 3",
    "Who is Kalpana Chawla",
    "What is the capital of France",
    "asdkjhfaskjdfh",
]

failures = []

for question, expected in KNOWN.items():
    result = engine.predict_intent(question)
    ok = result['is_known'] and result['intent'] == expected and result['confidence'] >= 0.8
    print(f"[{'PASS' if ok else 'FAIL'}] dataset  {question!r} -> {result['intent']} ({result['confidence']:.2f})")
    if not ok:
        failures.append(question)

for question in UNKNOWN:
    result = engine.predict_intent(question)
    ok = not result['is_known']
    print(f"[{'PASS' if ok else 'FAIL'}] unknown  {question!r} -> is_known={result['is_known']}")
    if not ok:
        failures.append(question)

web = WebSearchService()
for question, expected_title in [("What is ISRO?", "ISRO"), ("Tell me about Chandrayaan 3", "Chandrayaan-3")]:
    result = web.search(question)
    ok = result is not None and result['title'] == expected_title and result['url'].startswith('https://')
    print(f"[{'PASS' if ok else 'FAIL'}] web      {question!r} -> {result['title'] if result else None}")
    if not ok:
        failures.append(question)

for question in ["What is the capital of France", "Who is Elon Musk", "recipe for pasta", "what is bitcoin"]:
    result = web.search(question)
    ok = result is not None and result.get('off_topic') is True
    print(f"[{'PASS' if ok else 'FAIL'}] off-topic {question!r} -> {'refused' if ok else result}")
    if not ok:
        failures.append(question)

for question in ["ok cool", "lol"]:
    ok = web.search(question) is None
    print(f"[{'PASS' if ok else 'FAIL'}] no-web   {question!r}")
    if not ok:
        failures.append(question)

print()
if failures:
    print(f"❌ {len(failures)} check(s) failed: {failures}")
    sys.exit(1)
print("✅ All smoke checks passed")
