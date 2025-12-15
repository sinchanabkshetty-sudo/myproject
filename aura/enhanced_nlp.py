# aura/enhanced_nlp.py

import re
from datetime import datetime

class EnhancedNLP:
    """Extract intent and entities from user input"""
    
    def __init__(self):
        self.intent_patterns = {
            'music': r'(play|pause|stop|music|song|spotify|next|skip|previous|back)',
            'youtube': r'(youtube|watch|video|utube)',
            'email': r'(email|mail|gmail|send|compose)',
            'search': r'(search|google|find|what is|tell me|how to)',
            'system': r'(lock|shutdown|restart|sleep|volume|brightness|wifi|bluetooth)',
            'screenshot': r'(screenshot|capture|screen shot)',
            'app': r'(open|launch|start|run)',
            'file': r'(open|file|folder|create|delete|document)',
            'time': r'(time|date|what day)',
            'weather': r'(weather|temperature|forecast)',
            'help': r'(help|what can|commands)',
        }
        
        self.known_apps = [
            'chrome', 'firefox', 'notepad', 'word', 'excel',
            'powerpoint', 'spotify', 'discord', 'telegram', 'vlc',
            'calculator', 'paint', 'edge'
        ]
        
        self.known_websites = [
            'facebook', 'twitter', 'instagram', 'linkedin', 'reddit',
            'stackoverflow', 'github', 'netflix', 'amazon', 'ebay',
            'youtube', 'gmail', 'google', 'wikipedia', 'whatsapp'
        ]
    
    def extract_intent(self, user_input):
        """Extract main intent from input"""
        user_input_lower = user_input.lower()
        
        for intent, pattern in self.intent_patterns.items():
            if re.search(pattern, user_input_lower):
                return intent
        
        return 'general'
    
    def extract_email(self, user_input):
        """Extract email addresses from input"""
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        emails = re.findall(email_pattern, user_input)
        
        if emails:
            return emails[0]
        return None
    
    def extract_app(self, user_input):
        """Extract application names from input"""
        user_input_lower = user_input.lower()
        
        for app in self.known_apps:
            if app in user_input_lower:
                return app
        
        return None
    
    def extract_website(self, user_input):
        """Extract website names from input"""
        user_input_lower = user_input.lower()
        
        for website in self.known_websites:
            if website in user_input_lower:
                return website
        
        return None
    
    def extract_number(self, user_input):
        """Extract numbers from input"""
        numbers = re.findall(r'\b\d+\b', user_input)
        return [int(n) for n in numbers] if numbers else None
    
    def extract_query(self, user_input):
        """Extract search query from input"""
        user_input_lower = user_input.lower()
        
        keywords_to_remove = [
            'search for', 'find', 'google', 'youtube', 'watch',
            'send email to', 'mail to', 'email', 'compose',
            'open', 'launch', 'start', 'run', 'play',
            'what is', 'tell me about', 'how to',
            'please', 'can you', 'could you'
        ]
        
        query = user_input_lower
        for keyword in keywords_to_remove:
            query = query.replace(keyword, '').strip()
        
        return query.strip()
    
    def extract_entities(self, user_input):
        """Extract all entities from user input"""
        entities = {}
        
        # Extract email
        email = self.extract_email(user_input)
        if email:
            entities['email'] = email
        
        # Extract app
        app = self.extract_app(user_input)
        if app:
            entities['app'] = app
        
        # Extract website
        website = self.extract_website(user_input)
        if website:
            entities['website'] = website
        
        # Extract numbers
        numbers = self.extract_number(user_input)
        if numbers:
            entities['numbers'] = numbers
        
        # Extract search query
        query = self.extract_query(user_input)
        if query and len(query) > 2:
            entities['query'] = query
        
        # Extract quoted text
        quoted = re.findall(r'"([^"]*)"', user_input)
        if quoted:
            entities['quoted'] = quoted
        
        return entities
    
    def parse(self, user_input):
        """Parse input to extract intent and entities"""
        intent = self.extract_intent(user_input)
        entities = self.extract_entities(user_input)
        entities['raw_input'] = user_input
        entities['timestamp'] = datetime.now().isoformat()
        
        return intent, entities
