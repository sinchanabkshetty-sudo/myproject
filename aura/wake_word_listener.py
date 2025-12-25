# aura/wake_word_listener.py

import json
import queue
from typing import Callable, Optional

import sounddevice as sd
from vosk import Model, KaldiRecognizer

from aura.engine import handle_command
from aura.voice import speak_auto


WAKE_WORDS = ["hey aura", "hai aura", "hey ora", "aura"]


class WakeWordListener:
    def __init__(self, model_path: str = "models/vosk-small-en",
                 on_wake: Optional[Callable] = None):
        self.model = Model(model_path)
        self.rec = KaldiRecognizer(self.model, 16000)
        self.q: queue.Queue[bytes] = queue.Queue()
        self.listening_for_command = False
        self.on_wake = on_wake

    def _audio_callback(self, indata, frames, time_, status):
        if status:
            print("[WakeWordListener]", status)
        self.q.put(bytes(indata))

    @staticmethod
    def _contains_wake_word(text: str) -> bool:
        text = text.lower().strip()
        return any(w in text for w in WAKE_WORDS)

    def start(self):
        speak_auto("Wake word listener started. Say hey aura.")
        with sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
        ):
            while True:
                data = self.q.get()
                if not self.rec.AcceptWaveform(data):
                    continue

                result = self.rec.Result()
                try:
                    text = json.loads(result).get("text", "").strip()
                except Exception:
                    text = ""

                if not text:
                    continue

                print(f"[Vosk] heard: {text}")

                if not self.listening_for_command:
                    if self._contains_wake_word(text):
                        self.listening_for_command = True
                        if self.on_wake:
                            try:
                                self.on_wake()
                            except Exception as e:
                                print("on_wake error:", e)
                        speak_auto("Yes, I am listening.")
                    continue

                self.listening_for_command = False
                try:
                    response = handle_command(text)
                except Exception as e:
                    print("handle_command error:", e)
                    response = "Sorry, there was an error handling that command."
                print("AURA:", response)
                speak_auto(response)
