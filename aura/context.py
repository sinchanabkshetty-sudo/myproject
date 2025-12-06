# aura/context.py
import os
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

_db = None
_cursor = None

def _connect():
    global _db, _cursor
    if _db: return
    try:
        _db = mysql.connector.connect(
            host=os.getenv("DB_HOST","localhost"),
            user=os.getenv("DB_USER","root"),
            password=os.getenv("DB_PASSWORD",""),
            database=os.getenv("DB_NAME","aura_db"),
            auth_plugin="mysql_native_password",
        )
        _cursor = _db.cursor()
    except Exception:
        _db, _cursor = None, None

_connect()

def save_history(command: str, response: str):
    if not _cursor: return
    try:
        _cursor.execute(
            "INSERT INTO command_history (user_command, aura_response) VALUES (%s, %s)",
            (command, response[:255])
        )
        _db.commit()
    except Exception:
        pass
