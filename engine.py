# aura/engine.py
"""
AURA Engine: Main command execution handler
Uses EnhancedCommandEngine for extensible, modular command routing
"""

from .command_engine import EnhancedCommandEngine
from .setup_handlers import initialize_engine

# Try to import database (optional)
try:
    from aura.database import save_command
except ImportError:
    def save_command(text, response):
        pass  # Fallback if database not available


# Create engine instance (global/singleton)
_engine = None


def get_engine() -> EnhancedCommandEngine:
    """Get or create the command engine with all handlers"""
    global _engine
    if _engine is None:
        _engine = initialize_engine()  # This registers all handlers
    return _engine


def handle_command(text: str) -> str:
    """
    Main entry point called by GUI.
    Returns user-facing response string.
    """
    if not text:
        return "Please say something."
    
    engine = get_engine()
    response = engine.execute(text, min_confidence=0.2)  # LOWERED to 0.2
    
    # Save to database if available
    try:
        save_command(text, response)
    except Exception as e:
        print(f"Warning: Could not save command: {e}")
    
    return response


def get_command_history(limit: int = 20):
    """Get recent command history"""
    return get_engine().get_history(limit)


def get_handler_status() -> dict:
    """Get info about all registered handlers"""
    return get_engine().get_handler_info()
