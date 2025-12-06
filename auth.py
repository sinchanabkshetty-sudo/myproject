from db import get_connection

def register_user(name, email, password):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, password)
        )
        conn.commit()
        return True, "User registered successfully!"
    except Exception as e:
        return False, str(e)
    finally:
        cursor.close()
        conn.close()
