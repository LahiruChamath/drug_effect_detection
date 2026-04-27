import sqlite3
import os

# Path to your database file - update based on where Flask is run from
import os
base = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base, 'instance', 'safepose.db')
alt_db_path = os.path.join(base, 'api', 'instance', 'safepose.db')

def migrate():
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add fcm_token
        print("Adding fcm_token column...")
        cursor.execute("ALTER TABLE users ADD COLUMN fcm_token VARCHAR(255)")
    except sqlite3.OperationalError:
        print("fcm_token column already exists.")

    try:
        # Add push_enabled (default True)
        print("Adding push_enabled column...")
        cursor.execute("ALTER TABLE users ADD COLUMN push_enabled BOOLEAN DEFAULT 1")
    except sqlite3.OperationalError:
        print("push_enabled column already exists.")

    try:
        # Add email_enabled (default False)
        print("Adding email_enabled column...")
        cursor.execute("ALTER TABLE users ADD COLUMN email_enabled BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        print("email_enabled column already exists.")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
