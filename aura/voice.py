# aura/voice.py
import pyttsx3
import speech_recognition as sr

_tts = pyttsx3.init()
def speak(text: str):
    try:
        _tts.say(text)
        _tts.runAndWait()
    except Exception:
        pass

def mic_ready() -> bool:
    try:
        sr.Microphone()  # will throw if no device / driver
        return True
    except Exception:
        return False

def transcribe_once(timeout=6, phrase_time_limit=8) -> str | None:
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.4)
        audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    try:
        return r.recognize_google(audio)
    except sr.UnknownValueError:
        return None
    except Exception:
        return None
