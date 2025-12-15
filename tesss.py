# explicit_db_test.py
import os, traceback
from importlib import reload

print("ENV read by os.getenv():", {k: os.getenv(k) for k in ("DB_HOST","DB_USER","DB_PASSWORD","DB_NAME")})

# try to import your db.get_connection
try:
    import db
    reload(db)
    print("[db.py] DB_HOST='%s', DB_USER='%s', DB_NAME='%s'" % (
        getattr(db, "DB_HOST", None), getattr(db, "DB_USER", None), getattr(db, "DB_NAME", None)
    ))
except Exception as e:
    print("IMPORT db error:", e)
    traceback.print_exc()

# explicit connect (bypass your project helpers)
try:
    import mysql.connector
    cfg = {
        "host": os.getenv("DB_HOST","localhost"),
        "user": os.getenv("DB_USER",""),
        "password": os.getenv("DB_PASSWORD",""),
        "database": os.getenv("DB_NAME","")
    }
    print("Trying mysql.connector.connect with:", cfg)
    conn = mysql.connector.connect(**cfg)
    cur = conn.cursor()
    cur.execute("SELECT DATABASE(), USER(), CURRENT_USER();")
    print("SELECT ->", cur.fetchone())
    cur.close()
    conn.close()
    print("EXPLICIT SUCCESS: connected as above user.")
except Exception as e:
    print("EXPLICIT CONNECT ERROR:", type(e).__name__, str(e))
    traceback.print_exc()
