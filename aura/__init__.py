# aura/__init__.py

"""
AURA package initializer
Creates and exposes the global EnhancedCommandEngine instance.
"""

from .command_engine import EnhancedCommandEngine, SimpleKeywordHandler, CommandCategory
from .enhanced_nlp import EnhancedNLP
from .fuzzy_matcher import FuzzyMatcher

# Global engine instance (lazy-loaded)
_engine = None


def get_engine():
    """
    Return the global engine.
    If not initialized, create and initialize it using setup_handlers.initialize_engine().
    """
    global _engine

    if _engine is None:
        try:
            from .setup_handlers import initialize_engine
            _engine = initialize_engine()  # build engine + register all handlers
            print("🔧 AURA Engine initialized successfully.")
        except Exception as e:
            print("❌ Engine failed to initialize:", e)
            raise e

    return _engine


__all__ = [
    "EnhancedCommandEngine",
    "SimpleKeywordHandler",
    "CommandCategory",
    "EnhancedNLP",
    "FuzzyMatcher",
    "get_engine",
]
