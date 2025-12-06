import mysql.connector

def save_command(user_command, aura_response):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="WJ28@KRHPS",
            database="aura_db"
        )
        cursor = conn.cursor()
        query = "INSERT INTO command_history (user_command, aura_response) VALUES (%s, %s)"
        cursor.execute(query, (user_command, aura_response))
        conn.commit()
    except Exception as e:
        print(f"Database Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
