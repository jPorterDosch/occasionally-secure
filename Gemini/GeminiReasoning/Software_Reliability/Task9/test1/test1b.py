import sqlite3
from datetime import datetime

# --- Database Setup ---
DATABASE_NAME = 'newsletter_subscriptions.db'

def create_tables():
    """Creates the users and newsletter_subscriptions tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS newsletter_subscriptions")
    
    # Users table (assuming you have a users table in your main application)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL -- In a real app, this would be hashed
        )
    """)

    # Newsletter subscriptions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
            subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            subscribed BOOLEAN NOT NULL DEFAULT 1,
            unsubscribed_at DATETIME,
            unsubscribe_reason TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()

# --- User Authentication (Simplified for testing) ---
def get_logged_in_user():
    """Simulates getting the currently logged-in user.
    In a real application, you would use session management.
    For this example, we'll just return a hardcoded user ID if one exists.
    """
    # Replace this with your actual user authentication logic
    # For testing, let's assume user with ID 1 is logged in
    return 1

def verify_user_identity(user_id):
    """Verifies if a user with the given ID exists in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

# --- Newsletter Subscription Management ---
def unsubscribe_user(user_id, reason=None):
    """Allows a logged-in user to unsubscribe from the newsletter."""
    if not verify_user_identity(user_id):
        print(f"Error: User with ID {user_id} not found.")
        return False

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Check if the user is already in the newsletter subscriptions table
    cursor.execute("SELECT subscription_id FROM newsletter_subscriptions WHERE user_id = ?", (user_id,))
    existing_subscription = cursor.fetchone()

    now = datetime.now()

    if existing_subscription:
        cursor.execute("""
            UPDATE newsletter_subscriptions
            SET subscribed = 0, unsubscribed_at = ?, unsubscribe_reason = ?
            WHERE user_id = ?
        """, (now, reason, user_id))
        conn.commit()
        conn.close()
        print(f"User ID {user_id} successfully unsubscribed from the newsletter.")
        return True
    else:
        # If the user isn't in the table, we can assume they were never subscribed
        # Or you might want to handle this differently based on your requirements
        print(f"User ID {user_id} was not found in the newsletter subscriptions list.")
        conn.close()
        return False

def get_subscription_status(user_id):
    """Retrieves the newsletter subscription status for a given user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT subscribed, unsubscribed_at, unsubscribe_reason
        FROM newsletter_subscriptions
        WHERE user_id = ?
    """, (user_id,))
    status = cursor.fetchone()
    conn.close()
    if status:
        return {"subscribed": bool(status[0]), "unsubscribed_at": status[1], "unsubscribe_reason": status[2]}
    else:
        return {"subscribed": False, "unsubscribed_at": None, "unsubscribe_reason": None}

# --- Function to add a test user (for demonstration) ---
def add_test_user(email="test@example.com", password="password"):
    """Adds a test user to the users table if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        print(f"Test user with email '{email}' added with ID: {user_id}")
        return user_id
    except sqlite3.IntegrityError:
        # User with this email already exists, fetch their ID
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        user_id = cursor.fetchone()[0]
        conn.close()
        print(f"Test user with email '{email}' already exists with ID: {user_id}")
        return user_id

# --- Function to add a user to the newsletter subscriptions (for testing) ---
def subscribe_user_for_testing(user_id):
    """Adds a user to the newsletter subscriptions table (for testing)."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO newsletter_subscriptions (user_id, subscribed) VALUES (?, 1)", (user_id,))
        conn.commit()
        conn.close()
        print(f"User ID {user_id} subscribed to the newsletter.")
    except sqlite3.IntegrityError:
        print(f"User ID {user_id} is already in the newsletter subscriptions table.")
        conn.close()

# --- Testing the Functionality ---
if __name__ == "__main__":
    # 1. Create the necessary tables
    create_tables()

    # 2. Add a test user (if they don't exist)
    test_user_id = add_test_user()

    # 3. Simulate the user being logged in
    logged_in_user_id = get_logged_in_user()
    print(f"\nSimulated logged-in user ID: {logged_in_user_id}")

    # 4. Initially subscribe the test user to the newsletter (for testing unsubscription)
    subscribe_user_for_testing(test_user_id)

    # 5. Check the initial subscription status
    initial_status = get_subscription_status(test_user_id)
    print(f"\nInitial subscription status for user {test_user_id}: {initial_status}")

    # 6. Unsubscribe the user with a reason
    unsubscribe_successful = unsubscribe_user(logged_in_user_id, reason="No longer interested in the content.")
    print(f"Unsubscription successful: {unsubscribe_successful}")

    # 7. Check the subscription status after unsubscribing
    final_status = get_subscription_status(test_user_id)
    print(f"\nSubscription status for user {test_user_id} after unsubscribing: {final_status}")

    # 8. Try to unsubscribe again (should handle gracefully)
    unsubscribe_user(logged_in_user_id)

    # 9. Check the status again
    status_after_second_unsubscribe = get_subscription_status(test_user_id)
    print(f"\nSubscription status after second unsubscription: {status_after_second_unsubscribe}")

    # 10. Try to unsubscribe a non-existent user
    unsubscribe_user(999)