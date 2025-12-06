import sys, os, json, math, random, shutil
from pathlib import Path

from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, QSize, pyqtSignal, QThread
from PyQt6.QtGui import (
    QPainter, QPaintEvent, QColor, QPen, QBrush, QFont,
    QLinearGradient, QRadialGradient, QPainterPath, QRegion
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QLineEdit, QGraphicsDropShadowEffect, QTextEdit, QPushButton
)

# --- Speech backends (unchanged) --------------------------------------------
import speech_recognition as sr
HAVE_VOSK = False
HAVE_SPHINX = False
try:
    import vosk
    HAVE_VOSK = True
except Exception:
    HAVE_VOSK = False
try:
    from pocketsphinx import pocketsphinx
    HAVE_SPHINX = True
except Exception:
    HAVE_SPHINX = False

from aura.engine import handle_command

# NEW: import history saver
from history import save_history   # make sure history.py exists as we discussed

# --- Colors / theme ---------------------------------------------------------
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

# --- Aura logo (unchanged visual behavior) ---------------------------------
class AuraLogoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)
        self._particles = []
        self._seed_particles()

    def sizeHint(self):
        return QSize(44, 44)

    def _seed_particles(self):
        random.seed(42)
        self._particles.clear()
        for _ in range(26):
            ang = random.uniform(0, math.tau)
            rad = random.uniform(0.62, 0.95)
            spd = random.uniform(-0.0022, 0.0022)
            size = random.uniform(0.9, 1.8)
            alpha = random.randint(120, 200)
            self._particles.append([ang, rad, spd, size, alpha])

    def _tick(self):
        self._t += 0.016
        for p in self._particles:
            p[0] = (p[0] + p[2]) % math.tau
            p[4] = max(80, min(220, p[4] + random.randint(-4, 4)))
        self.update()

    def paintEvent(self, e: QPaintEvent):
        p = QPainter(self)
        set_aa(p)
        w, h = self.width(), self.height()
        cx, cy = w/2.0, h/2.0
        R = min(w, h) * 0.46

        halo = QRadialGradient(QPointF(cx, cy), R * 1.3)
        halo.setColorAt(0.0, QColor(0, 0, 0, 0))
        halo.setColorAt(0.8, QColor(135, 150, 255, 90))
        halo.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(halo))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), R * 1.25, R * 1.25)

        path = QPainterPath()
        steps = 160
        ring_width = max(2.5, R * 0.28)
        wave_amp = R * 0.10
        wave_freq = 3.0
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
        p.setPen(QPen(QBrush(grad), ring_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        inner = QRadialGradient(QPointF(cx, cy), R)
        inner.setColorAt(0.0, QColor(0, 0, 0, 0))
        inner.setColorAt(0.85, QColor(255, 255, 255, 20))
        inner.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(inner))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), R, R)

        for ang, rad, spd, size, alpha in self._particles:
            r = R * rad + 1.0 * math.sin(self._t * 1.7 + ang * 2.0)
            x = cx + r * math.cos(ang)
            y = cy + r * math.sin(ang)
            p.setBrush(QColor(200, 210, 255, alpha))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(x, y), size, size)
        p.end()

# --- Mic button with rings --------------------------------------------------
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
        cx, cy = w / 2.0, h / 2.0
        base = min(w, h) * 0.42

        # Glowing rings when listening
        if self.listening:
            for i in range(3):
                phase = (self._t * 1.6 + i * 0.35) % 1.0
                r_ring = base + phase * (base * 0.9)
                alpha_ring = int(90 * (1.0 - phase))
                p.setPen(QPen(QColor(120, 150, 255, alpha_ring), 1.2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(cx, cy), r_ring, r_ring)

        # Mic body (softer shape)
        mic_h = base * 1.15
        mic_w = base * 0.9
        
        path = QPainterPath()
        path.addRoundedRect(QRectF(cx - mic_w / 2, cy - mic_h / 2, mic_w, mic_h * 0.8), mic_w / 2, mic_w / 2)
        path.addRect(QRectF(cx - mic_w / 2, cy - mic_h / 2 + mic_h * 0.4, mic_w, mic_h * 0.6))

        mic_shape_path = QPainterPath()
        mic_shape_path.addRoundedRect(QRectF(cx - mic_w * 0.4, cy - mic_h * 0.5, mic_w * 0.8, mic_h * 0.9), mic_w * 0.4, mic_w * 0.4)
        mic_shape_path.addRect(QRectF(cx - mic_w * 0.15, cy + mic_h * 0.3, mic_w * 0.3, mic_h * 0.3))
        mic_shape_path.addRoundedRect(QRectF(cx - mic_w * 0.3, cy + mic_h * 0.6, mic_w * 0.6, mic_h * 0.15), mic_w * 0.15, mic_w * 0.15)

        grad = QLinearGradient(QPointF(0, 0), QPointF(w, h))
        grad.setColorAt(0.0, NEON_BLUE)
        grad.setColorAt(1.0, NEON_CYAN)
        
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawPath(mic_shape_path)
        
        p.setPen(QPen(QColor(NEON_CYAN).darker(120), 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(mic_shape_path)

        p.end()

# --- Send button ------------------------------------------------------------
class SendButton(QWidget):
    def __init__(self, on_click, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)
        self.hover = False
        self.press = False
        self.on_click = on_click
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, _):
        self.hover = True
        self.update()

    def leaveEvent(self, _):
        self.hover = False
        self.press = False
        self.update()

    def mousePressEvent(self, _):
        self.press = True
        self.update()

    def mouseReleaseEvent(self, e):
        if self.press and self.rect().contains(e.position().toPoint()):
            if self.on_click:
                self.on_click()
        self.press = False
        self.update()

    def paintEvent(self, e: QPaintEvent):
        p = QPainter(self)
        set_aa(p)
        w, h = self.width(), self.height()
        
        if self.hover or self.press:
            glow = QRadialGradient(QPointF(w * 0.5, h * 0.5), w * 0.8)
            glow.setColorAt(0.0, QColor(NEON_BLUE).lighter(150))
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(w * 0.5, h * 0.5), w * 0.8, h * 0.8)

        grad = QLinearGradient(QPointF(0, 0), QPointF(w, h))
        grad.setColorAt(0.0, NEON_BLUE)
        grad.setColorAt(1.0, NEON_CYAN)
        
        p.setPen(QPen(QBrush(grad), 2.0 if self.press else 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath()
        path.moveTo(w * 0.2, h * 0.75)
        path.lineTo(w * 0.8, h * 0.5)
        path.lineTo(w * 0.2, h * 0.25)
        path.lineTo(w * 0.35, h * 0.5)
        path.closeSubpath()

        path.moveTo(w * 0.8, h * 0.5)
        path.lineTo(w * 0.35, h * 0.5)

        p.drawPath(path)
        p.end()

# --- Pill input -------------------------------------------------------------
class PillInput(QWidget):
    send_requested = pyqtSignal(str)
    voice_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(62)
        self.hover = False
        self.focused = False

        self.mic = MicButton(self)
        self.mic.toggled.connect(self._on_mic_toggled)

        self.edit = QLineEdit(self)
        self.edit.setPlaceholderText("Type a command")
        self.edit.setText("")
        self.edit.setFrame(False)
        self.edit.setStyleSheet(
            "QLineEdit {border: 0; background: transparent; color: rgb(235,238,245); font-size: 16px; padding: 2px;}"
        )
        self.edit.returnPressed.connect(self._send_clicked)
        self.edit.textEdited.connect(lambda _: self.update())
        self.edit.focusInEvent = self._focus_in
        self.edit.focusOutEvent = self._focus_out

        self.send = SendButton(self._send_clicked, self)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 12, 18, 12)
        lay.setSpacing(12)
        lay.addWidget(self.mic, 0)
        lay.addWidget(self.edit, 1)
        lay.addWidget(self.send, 0)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def _on_mic_toggled(self, on: bool):
        self.set_listening(on)
        self.voice_toggled.emit(on)

    def set_listening(self, on: bool):
        self.mic.set_listening(on)
        if on:
            self._prev_ph = self.edit.placeholderText()
            self.edit.setPlaceholderText("Listening…")
        else:
            if hasattr(self, "_prev_ph"):
                self.edit.setPlaceholderText(self._prev_ph)
        self.update()

    def fill_from_voice_and_send(self, text: str):
        self.edit.setText(text)
        self._send_clicked()

    def _send_clicked(self):
        text = self.edit.text().strip()
        if not text:
            return
        self.send_requested.emit(text)
        self.edit.clear()
        self._flash_alpha = 160
        if not hasattr(self, "_flash_timer"):
            self._flash_timer = QTimer(self)
            self._flash_timer.timeout.connect(self._flash_tick)
        self._flash_timer.start(16)

    def _flash_tick(self):
        self._flash_alpha = int(self._flash_alpha * 0.85)
        if self._flash_alpha < 8:
            self._flash_timer.stop()
        self.update()

    def _focus_in(self, e):
        QLineEdit.focusInEvent(self.edit, e)
        self.focused = True
        self.update()

    def _focus_out(self, e):
        QLineEdit.focusOutEvent(self.edit, e)
        self.focused = False
        self.update()

    def enterEvent(self, _):
        self.hover = True
        self.update()

    def leaveEvent(self, _):
        self.hover = False
        self.update()

    def paintEvent(self, e: QPaintEvent):
        p = QPainter(self)
        set_aa(p)
        r = self.rect().adjusted(1, 1, -1, -1)
        radius = r.height() / 1.8
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), radius, radius)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(PILL_BG)
        p.drawPath(path)

        if self.hover or self.focused:
            p.setPen(QPen(QColor(90, 240, 255, 160), 2.2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)

        inner_r = r.adjusted(6, 6, -6, -6)
        inner_path = QPainterPath()
        inner_radius = inner_r.height() / 1.8
        inner_path.addRoundedRect(QRectF(inner_r), inner_radius, inner_radius)
        p.setPen(QPen(QColor(110, 116, 255, 90), 1.2))
        p.drawPath(inner_path)

        if hasattr(self, "_flash_alpha") and self._flash_alpha > 0:
            p.setBrush(QColor(120, 160, 255, self._flash_alpha))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(path)
        p.end()

# --- Voice thread (unchanged) -----------------------------------------------
class VoiceThread(QThread):
    transcript = pyqtSignal(str)
    listening_state = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._want_listen_once = False
        self._recognizer = sr.Recognizer()
        self._recognizer.pause_threshold = 0.8
        self._recognizer.energy_threshold = 300
        self._recognizer.dynamic_energy_threshold = True

        self.engine = "none"
        self._vosk_model = None
        if HAVE_VOSK:
            model_path = str(Path("C:/AURA_PROJECT/models/vosk-small-en").resolve())
            if Path(model_path).exists():
                try:
                    self._vosk_model = vosk.Model(model_path)
                    self.engine = "vosk"
                except Exception:
                    self._vosk_model = None
            else:
                self.engine = "vosk-missing"
        elif HAVE_SPHINX:
            self.engine = "sphinx"
        else:
            self.engine = "none"

    def stop(self):
        self._running = False

    def request_once(self, on: bool):
        self._want_listen_once = bool(on)

    def run(self):
        try:
            with sr.Microphone() as source:
                try:
                    self._recognizer.adjust_for_ambient_noise(source, duration=0.6)
                except Exception:
                    pass
                while self._running:
                    if not self._want_listen_once:
                        self.msleep(40)
                        continue
                    self.listening_state.emit(True)
                    try:
                        audio = self._recognizer.listen(source, timeout=None, phrase_time_limit=7)
                    except Exception:
                        self.listening_state.emit(False)
                        self._want_listen_once = False
                        continue
                    self.listening_state.emit(False)

                    text = None
                    try:
                        if self.engine == "vosk" and self._vosk_model is not None:
                            rec = vosk.KaldiRecognizer(self._vosk_model, audio.sample_rate)
                            rec.AcceptWaveform(audio.get_raw_data(convert_rate=audio.sample_rate, convert_width=2))
                            result = json.loads(rec.Result())
                            text = (result.get("text") or "").strip()
                        elif self.engine == "sphinx":
                            text = self._recognizer.recognize_sphinx(audio)
                    except sr.UnknownValueError:
                        text = None
                    except Exception:
                        text = None

                    self._want_listen_once = False
                    if text:
                        self.transcript.emit(text)
        except Exception:
            pass

# --- Main panel and window --------------------------------------------------
class AuraPanel(QWidget):
    def __init__(self, parent=None, corner_radius: int = 32):
        super().__init__(parent)
        self.corner_radius = corner_radius
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(60)
        shadow.setOffset(0, 22)
        shadow.setColor(QColor(20, 30, 70, 150))
        self.setGraphicsEffect(shadow)

        self.logo = AuraLogoWidget(self)
        self.title = QLabel("AURA", self)
        self.title.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        self.title.setStyleSheet("color: rgb(238,242,248); letter-spacing: 1px;")

        self.subtitle = QLabel("Ready (offline: checking…)", self)
        self.subtitle.setStyleSheet("color: rgba(200,210,230,220); font: 13px 'Segoe UI';")

        header_left = QVBoxLayout()
        header_left.setSpacing(2)
        header_left.addWidget(self.title)
        header_left.addWidget(self.subtitle)

        self.toggle_chat_btn = QPushButton("☰")
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

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)
        header.addWidget(self.logo, 0)
        header.addLayout(header_left, 0)
        header.addStretch(1)
        header.addWidget(self.toggle_chat_btn, 0)
        header.addWidget(self.close_btn, 0)

        self.pill = PillInput(self)
        self.pill.send_requested.connect(self._handle_text_command)
        self.pill.voice_toggled.connect(self._handle_voice_toggle)

        self.chat = QTextEdit(self)
        self.chat.setReadOnly(True)
        self.chat.setStyleSheet("QTextEdit{background:transparent;color:rgb(235,238,245);border:0;font:14px 'Segoe UI';padding:8px;}")
        self.chat.hide()

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 20, 26, 20)
        root.setSpacing(12)
        root.addLayout(header)
        root.addWidget(self.pill)
        root.addWidget(self.chat)

        self.voice = VoiceThread(self)
        self.voice.listening_state.connect(self._on_listening)
        self.voice.transcript.connect(self._on_voice_text)
        self.voice.start()

        self.subtitle.setText(f"Ready (offline: {self.voice.engine})")

    def _toggle_chat(self):
        self.chat.setVisible(not self.chat.isVisible())

    def _handle_voice_toggle(self, on: bool):
        self.voice.request_once(on)
        self.pill.set_listening(on)

    def _on_listening(self, is_on: bool):
        self.pill.set_listening(is_on)
        self.subtitle.setText("Listening…" if is_on else f"Ready (offline: {self.voice.engine})")

    def _on_voice_text(self, text: str):
        self._handle_text_command(text, from_voice=True)

    def _append_chat(self, speaker: str, message: str):
        self.chat.append(f"<b>{speaker}:</b> {message}")

    def _handle_text_command(self, text: str, from_voice: bool=False):
        if not text:
            return

        # Get user info from parent MainWindow (set by aura_login.py)
        main_window = self.window()
        user_id = getattr(main_window, "user_id", None)
        user_name = getattr(main_window, "user_name", "")

        self._append_chat("You (Voice)" if from_voice else "You", text)

        try:
            response = handle_command(text)
        except Exception as e:
            response = f"Error: {e}"

        self._append_chat("AURA", response)
        self.subtitle.setText(f"Ready (offline: {self.voice.engine})")

        # --- SAVE TO DATABASE (history) ----------------------------------
        try:
            if user_id is not None:
                mode = "voice" if from_voice else "text"
                save_history(user_id, text, response, mode)
        except Exception as e:
            # Don't crash UI if DB fails; just log to console
            print("Error saving history:", e)

    def paintEvent(self, e: QPaintEvent):
        p = QPainter(self)
        set_aa(p)
        r = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), self.corner_radius, self.corner_radius)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(BG_DARK)
        p.drawPath(path)

        grad = QLinearGradient(QPointF(r.left(), r.top()), QPointF(r.right(), r.bottom()))
        grad.setColorAt(0.0, QColor(255, 255, 255, 10))
        grad.setColorAt(0.5, QColor(255, 255, 255, 6))
        grad.setColorAt(1.0, QColor(255, 255, 255, 10))
        p.setBrush(QBrush(grad))
        p.drawPath(path)

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 18), 1))
        p.drawPath(path)
        p.end()

# --- MainWindow that applies mask so top-level corners are rounded -----------
class MainWindow(QWidget):
    def __init__(self, user_id: int = 0, user_name: str = "Guest"):
        super().__init__()
        self.user_id = user_id
        self.user_name = user_name

        self.corner_radius = 34
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.resize(790, 148)

        self.panel = AuraPanel(self, corner_radius=self.corner_radius)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.panel)
        self._drag = None
        self._apply_rounded_mask()

    def showEvent(self, _):
        scr = QApplication.primaryScreen().availableGeometry()
        self.move(scr.center().x() - self.width() // 2, scr.center().y() - self.height() // 2)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._apply_rounded_mask()

    def _apply_rounded_mask(self):
        r = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(r, self.corner_radius, self.corner_radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag and (e.buttons() & Qt.MouseButton.LeftButton):
            self.move(e.globalPosition().toPoint() - self._drag)
            e.accept()

    def mouseReleaseEvent(self, _):
        self._drag = None

    def closeEvent(self, _):
        try:
            self.panel.voice.stop()
            self.panel.voice.wait(500)
        except Exception:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("AURA Panel")
    app.setFont(QFont("Segoe UI", 10))
    # Standalone test: dummy user
    w = MainWindow(user_id=0, user_name="Guest")
    w.show()
    sys.exit(app.exec())
