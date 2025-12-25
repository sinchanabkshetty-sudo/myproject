# aura_panel.py
"""
Aura panel UI module (clean, non-circular).
Provides:
 - AuraPanel(QWidget) : main interactive panel (chat + voice)
 - MainWindow(QWidget) : top-level window that hosts AuraPanel
Integrated with:
 - EnhancedCommandEngine (NLP + fuzzy)
 - Wake-word listener ("Hey Aura")
 - Speech recognition (Vosk or Sphinx)
 - Natural TTS voice with speaking animation
"""

import json
import math
import random
from pathlib import Path
from typing import Optional
from threading import Thread

from PyQt6.QtCore import (
    Qt, QRectF, QPointF, QTimer, pyqtSignal, QThread
)
from PyQt6.QtGui import (
    QPainter, QPaintEvent, QColor, QPen, QBrush, QFont,
    QLinearGradient, QRadialGradient, QPainterPath, QRegion
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QLineEdit, QTextEdit, QPushButton
)

import speech_recognition as sr

# optional Vosk
HAVE_VOSK = False
try:
    import vosk
    HAVE_VOSK = True
except Exception:
    HAVE_VOSK = False

# ----------------------------------------------
# IMPORT AI ENGINE + WAKE WORD LISTENER + VOICE STATE
# ----------------------------------------------
from aura import get_engine
from aura.wake_word_listener import WakeWordListener
from aura.voice import is_speaking as voice_is_speaking

# History (safe fallback)
try:
    from history import save_history
except Exception:
    def save_history(id, t, r, m): 
        pass

# ------------- UI COLORS -------------
BG_DARK   = QColor(18, 20, 28, 255)
PILL_BG   = QColor(28, 32, 42, 230)
NEON_CYAN = QColor(90, 240, 255)
NEON_BLUE = QColor(110, 116, 255)
NEON_PINK = QColor(255, 120, 210)
TEXT_WHITE = QColor(238, 242, 248)

def set_aa(p: QPainter):
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

# ------------------------------------------------------------
# LOGO WIDGET  (with speaking animation)
# ------------------------------------------------------------
class AuraLogoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self._t = 0.0
        self._speaking = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

        self._particles = []
        self._seed_particles()

    def set_speaking(self, on: bool):
        self._speaking = bool(on)
        self.update()

    def _seed_particles(self):
        random.seed(42)
        self._particles.clear()
        for _ in range(22):
            ang = random.uniform(0, math.tau)
            rad = random.uniform(0.6, 0.95)
            spd = random.uniform(-0.002, 0.002)
            size = random.uniform(0.9, 1.6)
            alpha = random.randint(120, 200)
            self._particles.append([ang, rad, spd, size, alpha])

    def _tick(self):
        # move faster when speaking
        self._t += 0.016 * (1.7 if self._speaking else 1.0)
        for p in self._particles:
            p[0] = (p[0] + p[2]) % math.tau
            p[4] = max(80, min(220, p[4] + random.randint(-4, 4)))
        self.update()

    def paintEvent(self, e: QPaintEvent):
        p = QPainter(self)
        set_aa(p)
        w, h = self.width(), self.height()
        cx, cy = w/2.0, h/2.0
        R = min(w, h) * (0.5 if self._speaking else 0.46)

        # halo
        halo = QRadialGradient(QPointF(cx, cy), R * 1.3)
        halo.setColorAt(0.0, QColor(0, 0, 0, 0))
        halo.setColorAt(0.9, QColor(135, 150, 255, 90 if self._speaking else 60))
        halo.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(halo))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), R * 1.25, R * 1.25)

        # outer ring
        path = QPainterPath()
        steps = 120
        ring_width = max(2.2, R * 0.28)
        wave_amp = R * (0.11 if self._speaking else 0.08)
        wave_freq = 2.8
        for i in range(steps + 1):
            a = (i / steps) * math.tau
            r = R - ring_width / 2.0 + wave_amp * math.sin(wave_freq * a + self._t * 2.1)
            x = cx + r * math.cos(a)
            y = cy + r * math.sin(a)
            if i == 0: 
                path.moveTo(x, y)
            else: 
                path.lineTo(x, y)
        path.closeSubpath()

        grad = QLinearGradient(QPointF(0, 0), QPointF(w, h))
        grad.setColorAt(0.0, NEON_CYAN)
        grad.setColorAt(0.5, NEON_BLUE)
        grad.setColorAt(1.0, NEON_PINK)
        p.setPen(QPen(QBrush(grad), ring_width))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        # small orbiting particles
        for ang, rad, spd, size, alpha in self._particles:
            r = R * rad + (2.0 if self._speaking else 1.0) * math.sin(self._t * 1.7 + ang * 2.0)
            x = cx + r * math.cos(ang)
            y = cy + r * math.sin(ang)
            a2 = min(255, alpha + (40 if self._speaking else 0))
            p.setBrush(QColor(200, 210, 255, a2))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(x, y), size, size)

        p.end()

# ------------------------------------------------------------
# MIC BUTTON
# ------------------------------------------------------------
class MicButton(QWidget):
    toggled = pyqtSignal(bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.listening = False
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_listening(self, on: bool):
        self.listening = on
        self.update()

    def mousePressEvent(self, _):
        self.listening = not self.listening
        self.toggled.emit(self.listening)
        self.update()

    def _tick(self):
        if self.listening:
            self._t += 0.016
            self.update()

    def paintEvent(self, e: QPaintEvent):
        p = QPainter(self)
        set_aa(p)
        w, h = self.width(), self.height()
        cx, cy = w/2, h/2
        base = min(w, h) * 0.42

        if self.listening:
            for i in range(3):
                phase = (self._t * 1.6 + i * 0.35) % 1.0
                r_ring = base + phase * (base * 0.9)
                alpha_ring = int(90 * (1 - phase))
                p.setPen(QPen(QColor(120,150,255,alpha_ring), 1.2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(cx, cy), r_ring, r_ring)

        grad = QLinearGradient(QPointF(0,0), QPointF(w,h))
        grad.setColorAt(0.0, NEON_BLUE)
        grad.setColorAt(1.0, NEON_CYAN)

        mic_w = base * 0.9
        mic_h = base * 1.15
        path = QPainterPath()
        path.addRoundedRect(QRectF(cx-mic_w/2, cy-mic_h/2, mic_w, mic_h*0.8), mic_w/2, mic_w/2)
        path.addRect(QRectF(cx-mic_w/2, cy-mic_h/2 + mic_h*0.4, mic_w, mic_h*0.6))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawPath(path)
        p.end()

# ------------------------------------------------------------
# SEND BUTTON
# ------------------------------------------------------------
class SendButton(QWidget):
    def __init__(self, on_click, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)
        self.hover = False
        self.press = False
        self.on_click = on_click
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, _): 
        self.hover = True; self.update()
    def leaveEvent(self, _): 
        self.hover = False; self.press = False; self.update()
    def mousePressEvent(self, _): 
        self.press = True; self.update()
    def mouseReleaseEvent(self, e):
        if self.press and self.rect().contains(e.position().toPoint()):
            if self.on_click: 
                self.on_click()
        self.press = False; self.update()

    def paintEvent(self, e: QPaintEvent):
        p = QPainter(self)
        set_aa(p)
        w, h = self.width(), self.height()

        if self.hover or self.press:
            glow = QRadialGradient(QPointF(w*0.5,h*0.5), w*0.8)
            glow.setColorAt(0.0, QColor(NEON_BLUE).lighter(150))
            glow.setColorAt(1.0, QColor(0,0,0,0))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(w*0.5,h*0.5), w*0.8, h*0.8)

        grad = QLinearGradient(QPointF(0,0), QPointF(w,h))
        grad.setColorAt(0.0, NEON_BLUE)
        grad.setColorAt(1.0, NEON_CYAN)
        p.setPen(QPen(QBrush(grad), 1.8))
        p.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath()
        path.moveTo(w*0.2, h*0.75)
        path.lineTo(w*0.8, h*0.5)
        path.lineTo(w*0.2, h*0.25)
        path.lineTo(w*0.35, h*0.5)
        path.closeSubpath()
        path.moveTo(w*0.8, h*0.5)
        path.lineTo(w*0.35, h*0.5)
        p.drawPath(path)
        p.end()

# ------------------------------------------------------------
# VOICE INPUT THREAD
# ------------------------------------------------------------
class VoiceThread(QThread):
    transcript = pyqtSignal(str)
    listening_state = pyqtSignal(bool)

    def __init__(self, model_path=None, parent=None):
        super().__init__(parent)
        self._running = True
        self._want_once = False

        self._recognizer = sr.Recognizer()
        self._recognizer.pause_threshold = 0.8
        self._recognizer.energy_threshold = 300
        self._recognizer.dynamic_energy_threshold = True

        self.engine = "none"
        self._vosk_model = None

        if HAVE_VOSK and model_path:
            p = Path(model_path)
            if p.exists():
                try:
                    self._vosk_model = vosk.Model(str(p))
                    self.engine = "vosk"
                except Exception:
                    self._vosk_model = None

    def stop(self):
        self._running = False

    def request_once(self, on: bool):
        self._want_once = bool(on)

    def run(self):
        try:
            with sr.Microphone() as source:
                try:
                    self._recognizer.adjust_for_ambient_noise(source, duration=0.6)
                except Exception:
                    pass

                while self._running:
                    if not self._want_once:
                        self.msleep(40)
                        continue

                    self.listening_state.emit(True)
                    try:
                        audio = self._recognizer.listen(source, phrase_time_limit=7)
                    except Exception:
                        self.listening_state.emit(False)
                        self._want_once = False
                        continue

                    self.listening_state.emit(False)
                    text = None

                    try:
                        if self.engine == "vosk" and self._vosk_model:
                            rec = vosk.KaldiRecognizer(self._vosk_model, audio.sample_rate)
                            rec.AcceptWaveform(audio.get_raw_data(convert_rate=audio.sample_rate, convert_width=2))
                            result = json.loads(rec.Result())
                            text = (result.get("text") or "").strip()
                        else:
                            text = self._recognizer.recognize_sphinx(audio)
                    except Exception:
                        text = None

                    self._want_once = False
                    if text:
                        self.transcript.emit(text)
        except Exception:
            pass

# ------------------------------------------------------------
# PILL INPUT
# ------------------------------------------------------------
class PillInput(QWidget):
    send_requested = pyqtSignal(str)
    voice_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(62)

        self.mic = MicButton(self)
        self.mic.toggled.connect(self._on_mic)

        self.edit = QLineEdit(self)
        self.edit.setPlaceholderText("Type a command or say it…")
        self.edit.setFrame(False)
        self.edit.setStyleSheet("QLineEdit{border:0;background:transparent;color:white;font-size:16px;padding:2px;}")
        self.edit.returnPressed.connect(self._send_clicked)

        self.send = SendButton(self._send_clicked, self)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18,12,18,12)
        lay.setSpacing(12)
        lay.addWidget(self.mic)
        lay.addWidget(self.edit, 1)
        lay.addWidget(self.send)

    def _on_mic(self, on: bool):
        self.set_listening(on)
        self.voice_toggled.emit(on)

    def set_listening(self, on: bool):
        self.mic.set_listening(on)
        ph = "Listening…" if on else "Type a command or say it…"
        self.edit.setPlaceholderText(ph)

    def fill_from_voice_and_send(self, text):
        self.edit.setText(text)
        self._send_clicked()

    def _send_clicked(self):
        text = self.edit.text().strip()
        if text:
            self.send_requested.emit(text)
        self.edit.clear()

    def paintEvent(self, e):
        p = QPainter(self)
        set_aa(p)
        r = self.rect().adjusted(1,1,-1,-1)
        rad = r.height()/1.8
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), rad, rad)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(PILL_BG)
        p.drawPath(path)
        p.end()

# ------------------------------------------------------------
# AURA PANEL MAIN CLASS
# ------------------------------------------------------------
class AuraPanel(QWidget):
    def __init__(self, parent=None, corner_radius=32, model_path=None):
        super().__init__(parent)
        self.corner_radius = corner_radius

        # header UI
        self.logo = AuraLogoWidget(self)

        self.title = QLabel("AURA", self)
        self.title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.title.setStyleSheet("color:white;")

        self.subtitle = QLabel("Loading…", self)
        self.subtitle.setStyleSheet("color:gray; font-size:13px;")

        hl = QVBoxLayout()
        hl.addWidget(self.title)
        hl.addWidget(self.subtitle)

        self.toggle_chat_btn = QPushButton("☰", self)
        self.toggle_chat_btn.setFixedSize(30, 30)
        self.toggle_chat_btn.setStyleSheet(
            "QPushButton{color:rgba(220,224,234,220);background:transparent;border:0;font:700 16px 'Segoe UI';}"
            "QPushButton:hover{color:white;}"
        )
        self.toggle_chat_btn.clicked.connect(self._toggle_chat)

        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet(
            "QPushButton{ color: rgba(200,205,215,210); background: transparent; border: none; font: 700 16px 'Segoe UI'; }"
            "QPushButton:hover { color: rgb(240,244,250); }"
        )
        self.close_btn.clicked.connect(lambda: self.window().close())

        self.logout_btn = QPushButton("⎋", self)
        self.logout_btn.setFixedSize(30, 30)
        self.logout_btn.setToolTip("Logout")
        self.logout_btn.setStyleSheet(
            "QPushButton{ color: rgba(255,140,140,210); background: transparent; "
            "border: none; font: 700 16px 'Segoe UI'; }"
            "QPushButton:hover { color: rgb(255,90,90); }"
        )
        self.logout_btn.clicked.connect(self._logout)

        header = QHBoxLayout()
        header.addWidget(self.logo)
        header.addLayout(hl)
        header.addStretch()
        header.addWidget(self.toggle_chat_btn)
        header.addWidget(self.logout_btn)
        header.addWidget(self.close_btn)

        # input
        self.pill = PillInput(self)
        self.pill.send_requested.connect(self._handle_text_command)
        self.pill.voice_toggled.connect(self._toggle_voice)

        # chat
        self.chat = QTextEdit(self)
        self.chat.setReadOnly(True)
        self.chat.setStyleSheet("background:transparent;color:white;border:0;font-size:14px;")
        self.chat.hide()

        root = QVBoxLayout(self)
        root.setContentsMargins(26,20,26,20)
        root.addLayout(header)
        root.addWidget(self.pill)
        root.addWidget(self.chat)

        # AI engine
        self.enhanced_engine = get_engine()

        # VOICE THREAD (push-to-talk mic)
        model = model_path or "models/vosk-small-en"
        self.voice = VoiceThread(model, self)
        self.voice.listening_state.connect(self._on_listening)
        self.voice.transcript.connect(self._on_voice_text)
        self.voice.start()

        self.subtitle.setText("Ready • Voice Loaded • Wake-word ON")

        # VOICE ANIMATION TIMER (logo reacts to speech)
        self._speak_anim_timer = QTimer(self)
        self._speak_anim_timer.timeout.connect(self._poll_speaking_state)
        self._speak_anim_timer.start(80)

        # START WAKE WORD LISTENER IN BACKGROUND
        Thread(target=self.start_wake_word_listener, daemon=True).start()

    # ------------------------------------------------------------
    # Logout handler
    # ------------------------------------------------------------
    def _logout(self):
        """Stop voice thread, clear auto-login and show login window again."""
        try:
            if hasattr(self, "voice") and self.voice.isRunning():
                self.voice.stop()
                self.voice.wait(500)
        except Exception:
            pass

        # Import here to avoid circular import at module level
        from aura_login import AuraLoginWindow, user_memory

        # clear saved user so auto-login does not trigger
        user_memory.clear_user()

        win = self.window()
        if win is not None:
            win.close()

        # show login window
        self.login_window = AuraLoginWindow()
        self.login_window.show()

    # ------------------------------------------------------------
    # Wake-word listener starter
    # ------------------------------------------------------------
    def start_wake_word_listener(self):
        # This runs in a background Python thread (not Qt thread)
        def on_wake():
            # safely bring panel to front in Qt main thread
            QTimer.singleShot(0, self._bring_to_front)

        try:
            listener = WakeWordListener(model_path="models/vosk-small-en",
                                        on_wake=on_wake)
            listener.start()
        except Exception as e:
            print("Wake-word error:", e)

    def _bring_to_front(self):
        win = self.window()
        if win is not None:
            win.showNormal()
            win.raise_()
            win.activateWindow()

    # ------------------------------------------------------------
    # Voice toggle from MIC button
    # ------------------------------------------------------------
    def _toggle_voice(self, on: bool):
        self.voice.request_once(on)
        self.pill.set_listening(on)

    def _on_listening(self, is_on: bool):
        self.pill.set_listening(is_on)

    def _on_voice_text(self, text: str):
        self._handle_text_command(text, from_voice=True)

    # ------------------------------------------------------------
    # Logo speaking animation
    # ------------------------------------------------------------
    def _poll_speaking_state(self):
        self.logo.set_speaking(voice_is_speaking())

    # ------------------------------------------------------------
    # Chat helpers
    # ------------------------------------------------------------
    def _toggle_chat(self):
        self.chat.setVisible(not self.chat.isVisible())

    def _append_chat(self, who, msg):
        self.chat.append(f"<b>{who}:</b> {msg}")

    # ------------------------------------------------------------
    # Handle any text/voice command
    # ------------------------------------------------------------
    def _handle_text_command(self, text: str, from_voice=False):
        if not text:
            return

        who = "You (Voice)" if from_voice else "You"
        self._append_chat(who, text)

        try:
            resp = self.enhanced_engine.execute(text, min_confidence=0.2)
        except Exception as e:
            resp = f"Error: {e}"

        self._append_chat("AURA", resp)

        # save history if available
        try:
            win = self.window()
            uid = getattr(win, "user_id", None)
            if uid is not None:
                mode = "voice" if from_voice else "text"
                save_history(uid, text, resp, mode)
        except Exception:
            pass

    # UI background
    def paintEvent(self, e: QPaintEvent):
        p = QPainter(self)
        set_aa(p)
        r = self.rect().adjusted(1,1,-1,-1)
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), self.corner_radius, self.corner_radius)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(BG_DARK)
        p.drawPath(path)

        # soft outline
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255,255,255,18), 1))
        p.drawPath(path)
        p.end()

# ------------------------------------------------------------
# MAIN WINDOW
# ------------------------------------------------------------
class MainWindow(QWidget):
    def __init__(self, user_id=0, user_name="Guest"):
        super().__init__()
        self.user_id = user_id
        self.user_name = user_name
        self.corner_radius = 34

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(790, 148)

        self.panel = AuraPanel(self, corner_radius=self.corner_radius)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)
        lay.addWidget(self.panel)

        self._drag = None
        self._apply_mask()

    def showEvent(self, e):
        scr = QApplication.primaryScreen().availableGeometry()
        self.move(scr.center().x()-self.width()//2, scr.center().y()-self.height()//2)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._apply_mask()

    def _apply_mask(self):
        r = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(r, self.corner_radius, self.corner_radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag and (e.buttons() & Qt.MouseButton.LeftButton):
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        self._drag = None

    def closeEvent(self, e):
        try:
            if hasattr(self.panel, "voice"):
                self.panel.voice.stop()
                self.panel.voice.wait(500)
        except Exception:
            pass

# ------------------------------------------------------------
# TEST MODE
# ------------------------------------------------------------
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setApplicationName("AURA Panel")
    app.setFont(QFont("Segoe UI", 10))
    w = MainWindow(0, "Guest")
    w.show()
    sys.exit(app.exec())
