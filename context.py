# context.py — helper, mirrors same env loading as db.py (if used)
# top of context.py (and also top of aura/context.py)
from dotenv import load_dotenv
load_dotenv()



import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "aura_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "aura_db")

# Optional: small debug print
print(f"[context.py] DB_USER={DB_USER!r}, DB_NAME={DB_NAME!r}")
