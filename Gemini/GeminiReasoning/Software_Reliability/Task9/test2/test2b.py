import sqlite3
from datetime import datetime

DATABASE_NAME = 'newsletter_subscriptions.db'

def create_tables():
    """Creates the necessary tables in the database if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS newsletter_subscriptions")
    
    # User table (simplified for this example)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL -- In a real app, this would be hashed
        )
    """)

    # Newsletter subscriptions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
            user_id INTEGER NOT NULL,
            email TEXT UNIQUE NOT NULL,
            is_subscribed BOOLEAN DEFAULT TRUE,
            unsubscribed_reason TEXT,
            unsubscribed_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
    print("Tables created (if they didn't exist).")

def register_user(username, email, password):
    """Registers a new user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
        conn.commit()
        user_id = cursor.lastrowid
        print(f"User '{username}' registered with ID: {user_id}")
        return user_id
    except sqlite3.IntegrityError as e:
        print(f"Error registering user: {e}")
        return None
    finally:
        conn.close()

def subscribe_user_to_newsletter(user_id, email):
    """Subscribes a user to the newsletter."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO newsletter_subscriptions (user_id, email, is_subscribed) VALUES (?, ?, ?)", (user_id, email, True))
        cursor.execute("UPDATE newsletter_subscriptions SET is_subscribed = ? WHERE user_id = ?", (True, user_id))
        conn.commit()
        print(f"User with ID {user_id} (email: {email}) subscribed to the newsletter.")
    except Exception as e:
        print(f"Error subscribing user: {e}")
    finally:
        conn.close()

def get_logged_in_user_email(user_id):
    """Simulates getting the email of a logged-in user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def unsubscribe_user_from_newsletter(user_id, unsubscribe_reason=None):
    """Allows a logged-in user to unsubscribe from the newsletter."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    user_email = get_logged_in_user_email(user_id)

    if not user_email:
        print("Error: Could not retrieve user email.")
        conn.close()
        return False

    # Verify user identity (in this case, by matching the logged-in user ID)
    cursor.execute("SELECT COUNT(*) FROM newsletter_subscriptions WHERE user_id = ? AND email = ?", (user_id, user_email))
    count = cursor.fetchone()[0]

    if count == 0:
        print(f"Error: User with ID {user_id} and email {user_email} is not currently subscribed.")
        conn.close()
        return False

    try:
        cursor.execute("""
            UPDATE newsletter_subscriptions
            SET is_subscribed = ?, unsubscribed_reason = ?, unsubscribed_at = ?
            WHERE user_id = ? AND email = ?
        """, (False, unsubscribe_reason, datetime.now(), user_id, user_email))
        conn.commit()
        print(f"User with ID {user_id} (email: {user_email}) has unsubscribed from the newsletter.")
        if unsubscribe_reason:
            print(f"Reason provided: {unsubscribe_reason}")
        return True
    except Exception as e:
        print(f"Error unsubscribing user: {e}")
        return False
    finally:
        conn.close()

def get_newsletter_subscription_status(user_id):
    """Checks the newsletter subscription status of a user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT is_subscribed, unsubscribed_reason, unsubscribed_at FROM newsletter_subscriptions WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        is_subscribed, reason, unsubscribed_at = result
        return {"is_subscribed": bool(is_subscribed), "reason": reason, "unsubscribed_at": unsubscribed_at}
    else:
        return None

# --- Testing the functionality ---
if __name__ == "__main__":
    create_tables()

    # Simulate user registration
    user1_id = register_user("john_doe", "john.doe@example.com", "password123")
    user2_id = register_user("jane_smith", "jane.smith@example.com", "secure_pass")

    if user1_id:
        # Simulate user subscribing to the newsletter
        subscribe_user_to_newsletter(user1_id, "john.doe@example.com")

    if user2_id:
        subscribe_user_to_newsletter(user2_id, "jane.smith@example.com")

    print("\n--- Initial Subscription Status ---")
    if user1_id:
        status1 = get_newsletter_subscription_status(user1_id)
        print(f"User {user1_id} subscription status: {status1}")
    if user2_id:
        status2 = get_newsletter_subscription_status(user2_id)
        print(f"User {user2_id} subscription status: {status2}")

    print("\n--- Unsubscribing User 1 with a reason ---")
    if user1_id:
        unsubscribe_success1 = unsubscribe_user_from_newsletter(user1_id, "I am not interested anymore.")
        if unsubscribe_success1:
            status1_after_unsubscribe = get_newsletter_subscription_status(user1_id)
            print(f"User {user1_id} subscription status after unsubscribing: {status1_after_unsubscribe}")

    print("\n--- Unsubscribing User 2 without a reason ---")
    if user2_id:
        unsubscribe_success2 = unsubscribe_user_from_newsletter(user2_id)
        if unsubscribe_success2:
            status2_after_unsubscribe = get_newsletter_subscription_status(user2_id)
            print(f"User {user2_id} subscription status after unsubscribing: {status2_after_unsubscribe}")

    print("\n--- Trying to unsubscribe User 1 again (shouldn't change) ---")
    if user1_id:
        unsubscribe_again = unsubscribe_user_from_newsletter(user1_id)
        if unsubscribe_again:
            status1_after_second_unsubscribe = get_newsletter_subscription_status(user1_id)
            print(f"User {user1_id} subscription status after second unsubscribe: {status1_after_second_unsubscribe}")

    print("\n--- Final Subscription Status ---")
    if user1_id:
        final_status1 = get_newsletter_subscription_status(user1_id)
        print(f"User {user1_id} final subscription status: {final_status1}")
    if user2_id:
        final_status2 = get_newsletter_subscription_status(user2_id)
        print(f"User {user2_id} final subscription status: {final_status2}")