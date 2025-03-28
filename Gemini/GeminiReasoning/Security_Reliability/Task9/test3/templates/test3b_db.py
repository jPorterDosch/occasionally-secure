import sqlite3
import os

DATABASE_FILE = 'newsletter.db'

def initialize_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Assuming a users table exists with at least 'id' and 'email' columns
    try:
        cursor.execute("SELECT 1 FROM users LIMIT 1")
    except sqlite3.OperationalError:
        print("Warning: 'users' table not found. Please ensure it exists with 'id' and 'email' columns.")
        return

    # Create newsletter_subscriptions table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
            user_id INTEGER PRIMARY KEY,
            subscribed BOOLEAN NOT NULL DEFAULT TRUE,
            unsubscribe_reason TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

if not os.path.exists(DATABASE_FILE):
    initialize_database()
else:
    # Check if the newsletter_subscriptions table exists
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM newsletter_subscriptions LIMIT 1")
    except sqlite3.OperationalError:
        initialize_database() # Create the table if it's missing
    conn.close()

print(f"Database initialized or checked: {DATABASE_FILE}")