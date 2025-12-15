# aura/command_engine.py
"""Enhanced command engine with NLP and fuzzy matching"""

from enum import Enum
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
from .fuzzy_matcher import FuzzyMatcher
from .enhanced_nlp import EnhancedNLP


class CommandCategory(Enum):
    """Command categories"""
    ENTERTAINMENT = "entertainment"
    COMMUNICATION = "communication"
    INFORMATION = "information"
    SYSTEM = "system"
    PRODUCTIVITY = "productivity"
    OTHER = "other"


@dataclass
class Match:
    """Represents a command match"""
    handler_name: str
    confidence: float
    category: CommandCategory


class SimpleKeywordHandler:
    """Simple handler based on keywords"""
    
    def __init__(self, name: str, keywords: List[str], response_func: Callable, 
                 category: CommandCategory = CommandCategory.OTHER):
        self.name = name
        self.keywords = [k.lower() for k in keywords]
        self.response_func = response_func
        self.category = category
    
    def matches(self, text: str) -> float:
        """
        Return confidence 0-1.

        - If keywords list is empty ⇒ fallback handler (low but non-zero confidence)
        - Otherwise ⇒ confidence based on how many keywords match.
        """
        text_lower = text.lower()

        # Fallback handler: no keywords → always a small confidence
        if len(self.keywords) == 0:
            return 0.25

        matched_keywords = sum(1 for kw in self.keywords if kw in text_lower)
        if matched_keywords == 0:
            return 0.0

        # Higher confidence when more keywords match
        return min(1.0, 0.3 + (matched_keywords * 0.2))
    
    def handle(self, text: str) -> str:
        """Execute handler"""
        return self.response_func(text)


class EnhancedCommandEngine:
    """Main command engine with NLP + Fuzzy Matching"""
    
    def __init__(self):
        self.handlers: Dict[str, SimpleKeywordHandler] = {}
        self.fuzzy_matcher = FuzzyMatcher()
        self.nlp = EnhancedNLP()
        self.history: List[Tuple[str, str]] = []
    
    def register_handler(self, name: str, handler: SimpleKeywordHandler):
        """Register a command handler"""
        self.handlers[name] = handler
    
    def find_best_match(self, text: str, min_confidence: float = 0.2) -> Optional[Match]:
        """Find the best matching handler"""
        text_lower = text.lower()
        best_match = None
        best_confidence = min_confidence
        
        for handler_name, handler in self.handlers.items():
            confidence = handler.matches(text_lower)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = Match(
                    handler_name=handler_name,
                    confidence=confidence,
                    category=handler.category
                )
        
        return best_match
    
    def execute(self, text: str, min_confidence: float = 0.2) -> str:
        """Execute a command"""
        if not text:
            return "Please say something."
        
        # Step 1: Auto-correct typos using FuzzyMatcher
        corrected_text = text
        try:
            corrected_text = self.fuzzy_matcher.correct(text)
        except Exception as e:
            # If fuzzy matching fails, use original text
            print(f"Fuzzy matching skipped: {e}")
            corrected_text = text
        
        if corrected_text != text:
            print(f"🔧 Auto-corrected: '{text}' → '{corrected_text}'")
        
        # Step 2: Find best matching handler
        match = self.find_best_match(corrected_text, min_confidence=min_confidence)
        
        if match and match.handler_name in self.handlers:
            handler = self.handlers[match.handler_name]
            try:
                response = handler.handle(corrected_text)
                self.history.append((text, response))
                return response
            except Exception as e:
                return f"Error executing command: {str(e)}"
        
        # No match found at all (should rarely happen now)
        suggestions = [
            "try 'play music'",
            "try 'open chrome'",
            "try 'search for python'",
            "try 'what time'",
            "try 'help'"
        ]
        return f"I didn't understand that. {', or '.join(suggestions)}."
    
    def get_history(self, limit: int = 20) -> List[Tuple[str, str]]:
        """Get command history"""
        return self.history[-limit:]
    
    def get_handler_info(self) -> dict:
        """Get info about registered handlers"""
        return {
            name: {
                'keywords': handler.keywords,
                'category': handler.category.value
            }
            for name, handler in self.handlers.items()
        }
