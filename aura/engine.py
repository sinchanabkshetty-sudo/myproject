# aura/engine.py
"""
AURA Engine: Main command execution handler
Uses EnhancedCommandEngine with NLP + Fuzzy Matching
"""

# Get the pre-initialized engine with all handlers
from aura import get_engine


def handle_command(text: str) -> str:
    """
    Main entry point called by GUI.
    Returns user-facing response string.
    
    This function:
    1. Gets the global engine (with all handlers registered)
    2. Auto-corrects typos using FuzzyMatcher
    3. Detects intent using NLP
    4. Routes to appropriate handler
    5. Returns response
    """
    if not text:
        return "Please say something."
    
    try:
        engine = get_engine()
        # Use lenient confidence threshold
        response = engine.execute(text, min_confidence=0.2)
        return response
    except Exception as e:
        return f"Error: {str(e)}"


def get_command_history(limit: int = 20):
    """Get recent command history"""
    try:
        engine = get_engine()
        return engine.get_history(limit)
    except Exception as e:
        print(f"Error getting history: {e}")
        return []


def get_handler_status() -> dict:
    """Get info about all registered handlers"""
    try:
        engine = get_engine()
        return engine.get_handler_info()
    except Exception as e:
        print(f"Error getting handler status: {e}")
        return {}
