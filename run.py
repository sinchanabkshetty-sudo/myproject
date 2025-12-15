# run.py — simplified controller to launch login and open panel on success
from dotenv import load_dotenv
load_dotenv() 
import sys
from PyQt6.QtWidgets import QApplication
from aura_login import AuraLoginWindow
# top of run.py (first lines)
  # ensures .env values are available via os.getenv()

class Controller:
    def __init__(self):
        self.login = AuraLoginWindow()
        self.login.show()

    def run(self):
        # The login window itself opens the panel after success; controller just shows login.
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = Controller()
    sys.exit(app.exec())
