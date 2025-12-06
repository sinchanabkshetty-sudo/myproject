# aura_login.py (FINAL CLEAN WORKING VERSION)
import sys
import re

from auth import login_user
from aura_panel import MainWindow   # opens panel after login

from PyQt6.QtCore import Qt, QRectF, QTimer, QByteArray
from PyQt6.QtGui import QPainter, QColor, QFont, QPainterPath, QPixmap, QIcon, QRegion
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QGraphicsDropShadowEffect, QPushButton, QLineEdit, QCheckBox,
    QSizePolicy, QSpacerItem
)

# -------------------- THEME ---------------------
NEON_CYAN = QColor(90,240,255)
NEON_BLUE = QColor(110,116,255)
TEXT_WHITE = QColor(238,242,248)
BUTTON_WIDTH = 420
BUTTON_HEIGHT = 48

# --------------- SVG EYE ICONS -------------------
EYE_OUTLINE_SVG = b"""<svg xmlns='http://www.w3.org/2000/svg' ... ></svg>"""
EYE_SLASH_OUTLINE_SVG = b"""<svg xmlns='http://www.w3.org/2000/svg' ... ></svg>"""

# -----------------------------------------------
def svg_to_icon(svg_bytes: bytes, size: int = 18):
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return QIcon(pix)

def set_aa(p):
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)


# ==================================================
#               LOGIN WINDOW
# ==================================================
class AuraLoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.corner_radius = 20
        self._drag_pos = None
        self.setup_window()
        self.build_ui()

    def setup_window(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(560, 460)
        self.center_on_screen()
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 14)
        shadow.setColor(QColor(20,30,70,140))
        self.setGraphicsEffect(shadow)

    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.center().x() - self.width()//2,
                  screen.center().y() - self.height()//2)

    # ---------------- UI -----------------
    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20,18,20,18)

        # HEADER
        header = QHBoxLayout()
        title = QLabel("AURA LOGIN")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")

        close_btn = QPushButton("✕")
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(30,30)
        close_btn.setStyleSheet("background:transparent;color:white;border:0;")

        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(close_btn)
        root.addLayout(header)

        # Email
        self.email_field = QLineEdit()
        self.email_field.setPlaceholderText("you@example.com")
        self.style_input(self.email_field)
        root.addWidget(self.email_field)

        # Password
        pwd_box = QHBoxLayout()
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_field.setPlaceholderText("Password")
        self.style_input(self.password_field)

        self.eye_btn = QPushButton()
        self.eye_btn.setCheckable(True)
        self.eye_btn.setIcon(svg_to_icon(EYE_OUTLINE_SVG))
        self.eye_btn.clicked.connect(self.toggle_eye)
        self.eye_btn.setFixedSize(40,40)
        self.eye_btn.setStyleSheet("border:0;background:transparent;")

        pwd_box.addWidget(self.password_field)
        pwd_box.addWidget(self.eye_btn)
        pwd_widget = QWidget()
        pwd_widget.setLayout(pwd_box)
        root.addWidget(pwd_widget)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color:#ff7070;font-size:13px;")
        self.error_label.setVisible(False)
        root.addWidget(self.error_label)

        # Buttons
        self.login_btn = QPushButton("SIGN IN")
        self.login_btn.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.style_button(self.login_btn)
        self.login_btn.clicked.connect(self.handle_login)

        root.addWidget(self.login_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        root.addItem(QSpacerItem(20,20,QSizePolicy.Policy.Minimum,QSizePolicy.Policy.Expanding))

    # ---------------- STYLE METHODS ----------------
    def style_input(self, w):
        w.setFixedHeight(44)
        w.setStyleSheet("""
            QLineEdit {
                border:2px solid rgba(110,116,255,100);
                border-radius:22px;
                padding-left:14px;
                color:white;
                background-color:rgba(40,45,58,230);
                font-size:15px;
            }
        """)

    def style_button(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                border:0;
                border-radius:24px;
                color:white;
                font-weight:700;
                background-color:qlineargradient(
                    x1:0,y1:0,x2:1,y2:1,
                    stop:0 rgba(110,116,255,255),
                    stop:1 rgba(90,240,255,255)
                );
            }
        """)

    # ------------- Eye toggle -------------
    def toggle_eye(self):
        if self.eye_btn.isChecked():
            self.password_field.setEchoMode(QLineEdit.EchoMode.Normal)
            self.eye_btn.setIcon(svg_to_icon(EYE_SLASH_OUTLINE_SVG))
        else:
            self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
            self.eye_btn.setIcon(svg_to_icon(EYE_OUTLINE_SVG))

    # ------------- VALIDATION -------------
    def validate_inputs(self):
        email = self.email_field.text().strip()
        pwd = self.password_field.text()

        if not email:
            return False, "Email cannot be empty."
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return False, "Invalid email format."
        if not pwd:
            return False, "Password cannot be empty."

        return True, ""

    # ------------- REAL LOGIN -------------
    def handle_login(self):
        valid, msg = self.validate_inputs()
        if not valid:
            return self.show_error(msg)

        email = self.email_field.text().strip()
        password = self.password_field.text().strip()

        ok, msg, user_id, user_name = login_user(email, password)

        if not ok:
            return self.show_error(msg)

        # SUCCESS
        self.error_label.setStyleSheet("color:#80ff9a;font-size:13px;")
        self.error_label.setText("Login successful!")
        self.error_label.setVisible(True)

        QTimer.singleShot(500, lambda: self.open_panel(user_id, user_name))

    def open_panel(self, user_id, user_name):
        self.panel = MainWindow(user_id, user_name)
        self.panel.show()
        self.close()

    def show_error(self, msg):
        self.error_label.setStyleSheet("color:#ff7070;font-size:13px;")
        self.error_label.setText(msg)
        self.error_label.setVisible(True)

    # ---------------- Rounded UI ----------------
    def resizeEvent(self, e):
        r = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(r, self.corner_radius, self.corner_radius)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def paintEvent(self, e):
        p = QPainter(self)
        set_aa(p)
        r = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(r, self.corner_radius, self.corner_radius)

        grad = QColor(24,28,38)
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(path)


# -----------------------------------------
# MAIN
# -----------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AuraLoginWindow()
    win.show()
    sys.exit(app.exec())
from db import get_connection

def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id, name FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        result = cursor.fetchone()

        if result:
            return True, "Login successful", result[0], result[1]
        else:
            return False, "Invalid email or password", None, None

    except Exception as e:
        return False, str(e), None, None
    finally:
        cursor.close()
        conn.close()
