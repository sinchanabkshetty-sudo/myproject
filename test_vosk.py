from pathlib import Path
import sys
import vosk

model_path = Path(r"C:\AURA_PROJECT\models\vosk-small-en")
print("Model path:", model_path)

if not model_path.exists():
    print("MODEL MISSING")
    sys.exit(2)

try:
    m = vosk.Model(str(model_path))
    print("Vosk model loaded OK")
    rec = vosk.KaldiRecognizer(m, 16000)
    print("Recognizer created OK — offline model ready")
except Exception as e:
    print("Vosk init failed:", e)
    sys.exit(4)
