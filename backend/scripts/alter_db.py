import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "app.db")
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE chat_history ADD COLUMN mode VARCHAR DEFAULT 'general';")
    conn.commit()
    print("Column added successfully.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("Column already exists.")
    else:
        print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
