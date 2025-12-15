# verify_fix.py
from aura import get_engine

engine = get_engine()
app_handler = engine.handlers['app']

# Test the matching
text = "open chrome"
confidence = app_handler.matches(text.lower())

print(f"Text: '{text}'")
print(f"Keywords: {app_handler.keywords}")
print(f"Confidence: {confidence}")
print(f"Should match? {confidence > 0.2}")
