# aura/smart_intent.py
import re
from wikipedia import summary
import webbrowser


class SmartIntent:
    """
    AI-like intent analyzer for full assistant mode.
    Decides automatically what the user wants:
        - YouTube search
        - Google search
        - Wikipedia answer
        - System command
        - App command
    """

    def __init__(self):
        pass

    def is_question(self, text):
        return any(word in text.lower() for word in [
            "who is", "what is", "meaning of", "define", "tell me about"
        ])

    def is_youtube(self, text):
        return any(word in text.lower() for word in [
            "video", "watch", "song", "movie", "trailer", "youtube"
        ])

    def is_music(self, text):
        return any(word in text.lower() for word in [
            "play song", "play music", "play playlist"
        ])

    def extract_query(self, text):
        return re.sub(r"(who is|what is|meaning of|define|tell me about|youtube|play|video|watch)", "", text, flags=re.I).strip()

    def answer_question(self, question):
        """Try Wikipedia first, fallback to Google."""
        try:
            return "📘 " + summary(question, sentences=2)
        except:
            url = f"https://www.google.com/search?q={question.replace(' ', '+')}"
            webbrowser.open(url)
            return f"🔎 Searching Google for '{question}'..."

    def to_youtube(self, query):
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"📺 Searching YouTube for '{query}'..."

    def to_google(self, query):
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"🔎 Searching Google for '{query}'..."

    def handle(self, text):
        """Main AI-level decision-maker."""
        q = self.extract_query(text)

        if self.is_question(text):
            return self.answer_question(q)

        if self.is_youtube(text):
            return self.to_youtube(q)

        if "open" in text.lower() and "." in text.lower():
            # "open instagram", "open flipkart", "open github"
            site = q.replace("open", "").strip()
            url = f"https://www.{site}.com"
            webbrowser.open(url)
            return f"🌐 Opening {site}..."

        return self.to_google(q)
