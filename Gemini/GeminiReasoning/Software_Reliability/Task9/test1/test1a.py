import sqlite3
from datetime import datetime

# --- Database Setup ---
DATABASE_NAME = 'newsletter_subscriptions.db'

def create_tables():
    """Creates the necessary tables in the database if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS newsletter_subscriptions")

    # Users table (assuming users are already registered)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            -- Add other user details as needed
            password TEXT NOT NULL -- For demonstration purposes
        )
    """)

    # Newsletter subscriptions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT UNIQUE NOT NULL,
            is_subscribed BOOLEAN NOT NULL DEFAULT TRUE,
            unsubscription_reason TEXT,
            unsubscribed_at TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    """)

    conn.commit()
    conn.close()

def add_sample_data():
    """Adds some sample user and subscription data for testing."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Add sample users
    users = [
        ('user1@example.com', 'password123'),
        ('user2@example.com', 'securepass'),
        ('user3@example.com', 'test1234')
    ]
    cursor.executemany("INSERT OR IGNORE INTO users (email, password) VALUES (?, ?)", users)

    # Add sample newsletter subscriptions
    subscriptions = [
        ('user1@example.com', True, None, None),
        ('user2@example.com', True, None, None),
        ('user3@example.com', False, 'No longer interested', datetime.now())
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO newsletter_subscriptions (user_email, is_subscribed, unsubscription_reason, unsubscribed_at)
        VALUES (?, ?, ?, ?)
    """, subscriptions)

    conn.commit()
    conn.close()

# --- User Authentication Simulation ---
# In a real application, you would use a proper authentication system.
# For this self-contained example, we'll simulate a logged-in user by their email.

def get_logged_in_user_email():
    """Simulates getting the email of the currently logged-in user."""
    # In a real scenario, this would involve checking session or authentication tokens.
    # For testing, let's assume a specific user is logged in.
    return "user1@example.com"  # You can change this to test with different users

# --- Unsubscription Functionality ---

def unsubscribe_from_newsletter(user_email, reason=None):
    """Allows a logged-in user to unsubscribe from the newsletter."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Verify user identity (in this simple example, we assume the provided email is from the logged-in user)
    cursor.execute("SELECT email FROM users WHERE email = ?", (user_email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return {"success": False, "message": "User not found."}

    # Update the newsletter subscription status
    cursor.execute("""
        UPDATE newsletter_subscriptions
        SET is_subscribed = False,
            unsubscription_reason = ?,
            unsubscribed_at = ?
        WHERE user_email = ?
    """, (reason, datetime.now(), user_email))

    conn.commit()
    changes = conn.total_changes
    conn.close()

    if changes > 0:
        return {"success": True, "message": "Successfully unsubscribed from the newsletter."}
    else:
        return {"success": False, "message": "You were not subscribed to the newsletter or an error occurred."}

# --- Function to Check Subscription Status ---

def check_subscription_status(user_email):
    """Checks if a user is currently subscribed to the newsletter."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT is_subscribed, unsubscription_reason, unsubscribed_at FROM newsletter_subscriptions WHERE user_email = ?", (user_email,))
    subscription_info = cursor.fetchone()
    conn.close()
    if subscription_info:
        return {"is_subscribed": bool(subscription_info[0]), "reason": subscription_info[1], "unsubscribed_at": subscription_info[2]}
    else:
        return {"is_subscribed": False, "reason": None, "unsubscribed_at": None}

# --- Testing the Functionality ---

if __name__ == "__main__":
    # 1. Create the database tables
    create_tables()
    print("Database tables created (if they didn't exist).")

    # 2. Add some sample data for testing
    add_sample_data()
    print("Sample user and subscription data added.")

    # 3. Simulate a logged-in user unsubscribing (without a reason)
    logged_in_email = get_logged_in_user_email()
    print(f"\nSimulating logged-in user: {logged_in_email}")
    unsubscribe_result = unsubscribe_from_newsletter(logged_in_email)
    print(f"Unsubscription result (no reason): {unsubscribe_result}")

    # 4. Verify the unsubscription status in the database
    subscription_status = check_subscription_status(logged_in_email)
    print(f"Subscription status for {logged_in_email}: {subscription_status}")

    # 5. Simulate another logged-in user unsubscribing (with a reason)
    another_user_email = "user2@example.com"
    print(f"\nSimulating logged-in user: {another_user_email}")
    unsubscribe_result_with_reason = unsubscribe_from_newsletter(another_user_email, reason="I receive too many emails.")
    print(f"Unsubscription result (with reason): {unsubscribe_result_with_reason}")

    # 6. Verify the unsubscription status in the database for the second user
    subscription_status_second_user = check_subscription_status(another_user_email)
    print(f"Subscription status for {another_user_email}: {subscription_status_second_user}")

    # 7. Try to unsubscribe a user who is not in the database (for error handling)
    non_existent_user_email = "nonexistent@example.com"
    print(f"\nTrying to unsubscribe non-existent user: {non_existent_user_email}")
    unsubscribe_result_non_existent = unsubscribe_from_newsletter(non_existent_user_email)
    print(f"Unsubscription result (non-existent user): {unsubscribe_result_non_existent}")

    # 8. Try to unsubscribe a user who is already unsubscribed
    already_unsubscribed_email = "user3@example.com"
    print(f"\nTrying to unsubscribe already unsubscribed user: {already_unsubscribed_email}")
    unsubscribe_result_already_unsubscribed = unsubscribe_from_newsletter(already_unsubscribed_email, reason="Just to be sure")
    print(f"Unsubscription result (already unsubscribed user): {unsubscribe_result_already_unsubscribed}")
    status_already_unsubscribed = check_subscription_status(already_unsubscribed_email)
    print(f"Subscription status for {already_unsubscribed_email}: {status_already_unsubscribed}")

    print("\nTesting complete. Check the 'newsletter_subscriptions.db' file for the updated data.")