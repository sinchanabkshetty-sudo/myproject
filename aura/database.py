# aura/database.py
from dotenv import load_dotenv
load_dotenv()

import os
import mysql.connector
from mysql.connector import Error

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "")

def get_connection():
    if not DB_USER:
        raise RuntimeError("DB_USER missing in .env")

    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        return conn

    except Error as e:
        print(f"[database.py] Connection error: {e}")
        raise


def save_command(user_command, aura_response, user_id=None, mode="voice"):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO command_history (user_id, user_command, aura_response, input_mode)
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(sql, (user_id, user_command, aura_response, mode))
        conn.commit()

    except Exception as e:
        print(f"[database.py] Save error: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
