# aura/wake_word_listener.py

"""
Wake-word + continuous listening using Vosk.
- Say "hey aura" to activate
- Then speak a command → routed via handle_command
- Uses AURA voice (bilingual capable)
"""

import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

from aura.engine import handle_command
from aura.voice import speak_auto

WAKE_WORDS = ["hey aura", "hai aura", "hey ora", "aura"]


class WakeWordListener:
    def __init__(self, model_path: str = "models/vosk-small-en",
                 on_wake=None):
        """
        on_wake: optional callback called when wake word is detected.
                 (Used by UI to auto-open/bring-to-front panel.)
        """
        self.model = Model(model_path)
        self.rec = KaldiRecognizer(self.model, 16000)
        self.q = queue.Queue()
        self.listening_for_command = False
        self.on_wake = on_wake

    # ------------ audio callback ------------
    def _audio_callback(self, indata, frames, time_, status):
        if status:
            print(status)
        self.q.put(bytes(indata))

    # ------------ helpers ------------
    def _contains_wake_word(self, text: str) -> bool:
        text = text.lower().strip()
        return any(w in text for w in WAKE_WORDS)

    # ------------ main loop ------------
    def start(self):
        """Blocking loop: wake-word + command mode."""
        speak_auto("Wake word listener started. Say hey aura.")
        with sd.RawInputStream(samplerate=16000,
                               blocksize=8000,
                               dtype="int16",
                               channels=1,
                               callback=self._audio_callback):
            while True:
                data = self.q.get()
                if self.rec.AcceptWaveform(data):
                    result = self.rec.Result()
                    try:
                        text = json.loads(result)["text"]
                    except Exception:
                        text = ""
                    if not text:
                        continue

                    print(f"[Vosk] heard: {text}")

                    if not self.listening_for_command:
                        # Waiting for wake word
                        if self._contains_wake_word(text):
                            self.listening_for_command = True
                            # notify UI to bring panel to front
                            if self.on_wake:
                                try:
                                    self.on_wake()
                                except Exception as e:
                                    print("on_wake error:", e)
                            speak_auto("Yes, I am listening.")
                        continue

                    # We are in command mode
                    self.listening_for_command = False
                    response = handle_command(text)
                    print("AURA:", response)
                    speak_auto(response)
