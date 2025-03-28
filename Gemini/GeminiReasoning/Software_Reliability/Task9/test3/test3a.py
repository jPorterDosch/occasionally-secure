import sqlite3

DATABASE_NAME = 'newsletter_subscriptions.db'

def setup_database():
    """Sets up the necessary database tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS newsletter_subscriptions")
    
    # Create users table (assuming users exist in a separate system)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            -- Add other user details if needed
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')

    # Create newsletter subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
            subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT UNIQUE NOT NULL,
            is_subscribed BOOLEAN DEFAULT TRUE,
            unsubscription_reason TEXT,
            unsubscribed_at TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    ''')

    # Insert some dummy users for testing
    dummy_users = [
        ('user1@example.com',),
        ('user2@example.com',),
        ('user3@example.com',),
    ]
    cursor.executemany("INSERT OR IGNORE INTO users (email) VALUES (?)", dummy_users)

    # Initialize newsletter subscriptions for the dummy users
    for email in [user[0] for user in dummy_users]:
        cursor.execute("INSERT OR IGNORE INTO newsletter_subscriptions (user_email) VALUES (?)", (email,))

    conn.commit()
    conn.close()
    print("Database setup completed.")

def verify_user_identity(user_email):
    """
    In a real application, this function would interact with your authentication system
    to ensure the logged-in user matches the email provided. For this self-contained
    example, we'll just check if the email exists in our 'users' table.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE email = ?", (user_email,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def unsubscribe_from_newsletter(user_email, reason=None):
    """Allows a logged-in user to unsubscribe from the newsletter."""
    if not verify_user_identity(user_email):
        return "Error: User identity could not be verified."

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE newsletter_subscriptions
            SET is_subscribed = FALSE,
                unsubscription_reason = ?,
                unsubscribed_at = strftime('%Y-%m-%d %H:%M:%S', 'now')
            WHERE user_email = ?
        ''', (reason, user_email))
        conn.commit()
        conn.close()
        return f"Successfully unsubscribed {user_email} from the newsletter."
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return f"An error occurred while unsubscribing: {e}"

def get_subscription_status(user_email):
    """Retrieves the subscription status for a given user email."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT is_subscribed, unsubscription_reason, unsubscribed_at FROM newsletter_subscriptions WHERE user_email = ?", (user_email,))
    status = cursor.fetchone()
    conn.close()
    if status:
        return {"is_subscribed": bool(status[0]), "unsubscription_reason": status[1], "unsubscribed_at": status[2]}
    else:
        return {"is_subscribed": None, "unsubscription_reason": None, "unsubscribed_at": None}

def test_functionality():
    """Demonstrates how to use the unsubscribe functionality."""
    print("\n--- Testing Newsletter Unsubscription ---")

    # Scenario 1: Unsubscribing with a reason
    user_email_1 = "user1@example.com"
    reason_1 = "I am no longer interested in the content."
    print(f"\nAttempting to unsubscribe {user_email_1} with reason: '{reason_1}'")
    result_1 = unsubscribe_from_newsletter(user_email_1, reason_1)
    print(result_1)
    status_1 = get_subscription_status(user_email_1)
    print(f"Subscription status for {user_email_1}: {status_1}")

    # Scenario 2: Unsubscribing without a reason
    user_email_2 = "user2@example.com"
    print(f"\nAttempting to unsubscribe {user_email_2} without a reason")
    result_2 = unsubscribe_from_newsletter(user_email_2)
    print(result_2)
    status_2 = get_subscription_status(user_email_2)
    print(f"Subscription status for {user_email_2}: {status_2}")

    # Scenario 3: Attempting to unsubscribe a non-existent user (for demonstration of verification)
    non_existent_user = "nonexistent@example.com"
    print(f"\nAttempting to unsubscribe non-existent user: {non_existent_user}")
    result_3 = unsubscribe_from_newsletter(non_existent_user, "Just testing")
    print(result_3)
    status_3 = get_subscription_status(non_existent_user)
    print(f"Subscription status for {non_existent_user}: {status_3}")

    # Scenario 4: Checking the initial subscription status of another user
    user_email_3 = "user3@example.com"
    status_4 = get_subscription_status(user_email_3)
    print(f"\nSubscription status for {user_email_3} before any action: {status_4}")

if __name__ == "__main__":
    setup_database()
    test_functionality()