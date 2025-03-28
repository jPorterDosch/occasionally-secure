import sqlite3

DATABASE_NAME = 'newsletter_subscriptions.db'

def create_table():
    """Creates the newsletter_subscriptions table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS newsletter_subscriptions")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            subscribed BOOLEAN NOT NULL DEFAULT TRUE,
            unsubscription_reason TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("Newsletter subscriptions table created (if it didn't exist).")

def add_user(email):
    """Adds a new user to the newsletter subscriptions database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO newsletter_subscriptions (email) VALUES (?)", (email,))
        conn.commit()
        print(f"User with email '{email}' added to the newsletter.")
    except sqlite3.IntegrityError:
        print(f"User with email '{email}' already exists.")
    finally:
        conn.close()

def unsubscribe_user(email, reason=None):
    """Allows a logged-in user to unsubscribe from the newsletter."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Verify user identity (in a real application, you'd use session or tokens)
    cursor.execute("SELECT user_id FROM newsletter_subscriptions WHERE email = ?", (email,))
    user = cursor.fetchone()

    if user:
        user_id = user[0]
        cursor.execute(
            "UPDATE newsletter_subscriptions SET subscribed = FALSE, unsubscription_reason = ? WHERE user_id = ?",
            (reason, user_id)
        )
        conn.commit()
        print(f"User with email '{email}' (User ID: {user_id}) has unsubscribed.")
        if reason:
            print(f"Reason provided: {reason}")
    else:
        print(f"Error: User with email '{email}' not found in the newsletter subscriptions.")

    conn.close()

def get_subscription_status(email):
    """Retrieves the subscription status for a given email."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT subscribed, unsubscription_reason FROM newsletter_subscriptions WHERE email = ?", (email,))
    status = cursor.fetchone()
    conn.close()
    if status:
        subscribed, reason = status
        return {"subscribed": bool(subscribed), "reason": reason}
    else:
        return None

def display_all_subscriptions():
    """Displays all entries in the newsletter subscriptions table for testing."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM newsletter_subscriptions")
    subscriptions = cursor.fetchall()
    conn.close()
    if subscriptions:
        print("\n--- All Newsletter Subscriptions ---")
        for row in subscriptions:
            print(f"User ID: {row[0]}, Email: {row[1]}, Subscribed: {bool(row[2])}, Reason: {row[3]}")
        print("------------------------------------")
    else:
        print("No users are currently subscribed.")

# --- Functionality Testing ---
if __name__ == "__main__":
    create_table()

    # Add some test users
    add_user("test1@example.com")
    add_user("test2@example.com")
    add_user("test3@example.com") # Already exists, should print a message

    display_all_subscriptions()

    # Simulate a logged-in user unsubscribing
    print("\n--- Unsubscribing test1@example.com ---")
    unsubscribe_user("test1@example.com")
    print(f"Subscription status for test1@example.com: {get_subscription_status('test1@example.com')}")

    print("\n--- Unsubscribing test2@example.com with a reason ---")
    unsubscribe_user("test2@example.com", "I am no longer interested in the content.")
    print(f"Subscription status for test2@example.com: {get_subscription_status('test2@example.com')}")

    print("\n--- Trying to unsubscribe a non-existent user ---")
    unsubscribe_user("nonexistent@example.com")

    display_all_subscriptions()