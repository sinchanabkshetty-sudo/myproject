# auth.py — login/register using password_hash
from db import get_connection
import bcrypt

def register_user(name: str, email: str, password: str):
    conn = None
    cursor = None
    try:
        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, pw_hash)
        )
        conn.commit()
        return True, "Registered successfully"
    except Exception as e:
        return False, f"DB error: {type(e).__name__} {e}"
    finally:
        if cursor:
            try: cursor.close()
            except: pass
        if conn:
            try: conn.close()
            except: pass

def login_user(email: str, password: str):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name, password_hash FROM users WHERE email=%s", (email,))
        row = cursor.fetchone()
        if not row:
            return False, "No user with that email", None, None
        user_id, name, pw_hash = row
        if bcrypt.checkpw(password.encode("utf-8"), pw_hash.encode("utf-8")):
            return True, "Login successful", user_id, name
        else:
            return False, "Invalid password", None, None
    except Exception as e:
        return False, f"DB error: {type(e).__name__} {e}", None, None
    finally:
        if cursor:
            try: cursor.close()
            except: pass
        if conn:
            try: conn.close()
            except: pass
