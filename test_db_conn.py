# test_db_conn.py
from db import get_connection

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DATABASE(), USER();")
    print("OK - connected. Info:", cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print("DB CONNECT ERROR:", type(e), e)
