import sys
from PyQt6.QtWidgets import QApplication
from aura_login import AuraLoginWindow
from aura_panel import MainWindow

class Controller:
    def __init__(self):
        # Create login window
        self.login = AuraLoginWindow()

        # Wrap original attempt_login() so we can detect success
        original_attempt = self.login.attempt_login

        def wrapped_attempt():
            original_attempt()
            # Check if success text appears (your login code sets this EXACT text)
            if "Signed in successfully" in self.login.error_label.text():
                QTimer.singleShot(300, self.open_panel)

        from PyQt6.QtCore import QTimer
        self.login.attempt_login = wrapped_attempt

        self.login.show()

    def open_panel(self):
        self.login.close()
        self.panel = MainWindow()
        self.panel.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = Controller()
    sys.exit(app.exec())
