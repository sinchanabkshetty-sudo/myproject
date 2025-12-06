# history.py – save Aura panel history into MySQL

from db import get_connection


def save_history(user_id: int, user_command: str, aura_response: str, input_mode: str = "text"):
    """
    Save one interaction into command_history table.
    :param user_id: ID from users table (can be None if unknown)
    :param user_command: what the user asked/typed/said
    :param aura_response: text response from Aura
    :param input_mode: "text" or "voice"
    """
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        sql = """
        INSERT INTO command_history (user_id, user_command, aura_response, input_mode)
        VALUES (%s, %s, %s, %s)
        """
        cur.execute(sql, (user_id, user_command, aura_response, input_mode))
        conn.commit()

    except Exception as e:
        # For now we just print; later you can log to a file
        print("Error saving history:", e)

    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
