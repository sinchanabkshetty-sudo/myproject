import customtkinter as ctk
import threading
import speech_recognition as sr
import pyttsx3
from aura.engine import handle_command

# Initialize TTS Engine
tts_engine = pyttsx3.init()
def speak(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

# Voice Command Function
def listen_voice():
    append_chat("AURA: 🎤 Listening...")
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5)
        command = recognizer.recognize_google(audio)
        append_chat(f"You (Voice): {command}")
        process_command(command)
    except Exception as e:
        append_chat(f"AURA: ❌ Voice error: {str(e)}")
        speak("I couldn't understand. Please try again.")

# Append messages to UI
def append_chat(message):
    chat_window.configure(state="normal")
    chat_window.insert("end", message + "\n")
    chat_window.configure(state="disabled")
    chat_window.see("end")

# Process both text & voice commands
def process_command(command):
    response = handle_command(command)
    append_chat(f"AURA: {response}")
    speak(response)

# Send button click
def send_text():
    command = input_box.get().strip()
    if command:
        append_chat(f"You: {command}")
        input_box.delete(0, "end")
        process_command(command)

# Voice button in thread
def start_voice_thread():
    threading.Thread(target=listen_voice, daemon=True).start()

# ---------------------- UI SECTION ---------------------
ctk.set_appearance_mode("dark")  # options: light, dark, system
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("AURA - Adaptive Unified Resource Assistant")
app.geometry("800x500")

chat_window = ctk.CTkTextbox(app, width=750, height=350, state="disabled")
chat_window.pack(pady=10)

input_frame = ctk.CTkFrame(app)
input_frame.pack(fill="x", pady=10)

input_box = ctk.CTkEntry(input_frame, placeholder_text="Type your command here...", width=500)
input_box.pack(side="left", padx=10)

send_button = ctk.CTkButton(input_frame, text="Send", command=send_text)
send_button.pack(side="left", padx=5)

voice_button = ctk.CTkButton(input_frame, text="🎤 Speak", command=start_voice_thread)
voice_button.pack(side="left", padx=5)

append_chat("AURA: Hello! How can I assist you today?")
speak("Hello! How can I assist you today?")

app.mainloop()
