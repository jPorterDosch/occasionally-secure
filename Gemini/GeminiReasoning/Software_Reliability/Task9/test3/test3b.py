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
    
    # Create users table (for simulating logged-in users)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL -- In a real app, this would be hashed
        )
    ''')

    # Create newsletter_subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
            user_id INTEGER UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            is_subscribed INTEGER DEFAULT 1, -- 1 for subscribed, 0 for unsubscribed
            unsubscription_reason TEXT,
            unsubscribed_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database tables created (if they didn't exist).")

# --- User Authentication Simulation ---
def simulate_login(email, password):
    """Simulates a user login and returns the user ID if successful."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

# --- Newsletter Unsubscription Functionality ---
def unsubscribe_user(user_id, reason=None):
    """Allows a logged-in user to unsubscribe from the newsletter."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Verify user exists
    cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        print(f"Error: User with ID {user_id} not found.")
        conn.close()
        return False

    user_email = user[0]

    # Check if the user is already unsubscribed
    cursor.execute("SELECT is_subscribed FROM newsletter_subscriptions WHERE user_id = ?", (user_id,))
    subscription_status = cursor.fetchone()
    if subscription_status and subscription_status[0] == 0:
        print(f"User with ID {user_id} ({user_email}) is already unsubscribed.")
        conn.close()
        return True

    try:
        cursor.execute('''
            INSERT INTO newsletter_subscriptions (user_id, email, is_subscribed, unsubscription_reason, unsubscribed_at)
            VALUES (?, ?, 0, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                is_subscribed = 0,
                unsubscription_reason = ?,
                unsubscribed_at = ?
        ''', (user_id, user_email, reason, datetime.now(), reason, datetime.now()))
        conn.commit()
        print(f"User with ID {user_id} ({user_email}) has successfully unsubscribed.")
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database error during unsubscription: {e}")
        conn.rollback()
        conn.close()
        return False

# --- Utility Function to Check Subscription Status ---
def check_subscription_status(user_id):
    """Checks the newsletter subscription status of a user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT is_subscribed, unsubscription_reason, unsubscribed_at FROM newsletter_subscriptions WHERE user_id = ?", (user_id,))
    subscription_info = cursor.fetchone()
    conn.close()
    if subscription_info:
        status = "Subscribed" if subscription_info[0] == 1 else "Unsubscribed"
        reason = subscription_info[1]
        unsubscribed_at = subscription_info[2]
        return f"User ID {user_id} is {status}. Reason: {reason}, Unsubscribed At: {unsubscribed_at}"
    else:
        return f"User ID {user_id} not found in newsletter subscriptions."

# --- Functions for Testing ---
def populate_test_data():
    """Populates the database with some test users."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    users = [
        ('user1@example.com', 'password123'),
        ('user2@example.com', 'securepwd'),
        ('user3@example.com', 'test1234')
    ]
    for email, password in users:
        try:
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        except sqlite3.IntegrityError:
            print(f"User with email {email} already exists.")
    conn.commit()
    conn.close()
    print("Test users populated.")

def test_unsubscription():
    """Tests the newsletter unsubscription functionality."""
    create_tables()
    populate_test_data()

    # Simulate user logins
    user1_id = simulate_login('user1@example.com', 'password123')
    user2_id = simulate_login('user2@example.com', 'securepwd')
    user3_id = simulate_login('user3@example.com', 'wrongpassword') # Invalid login

    if user1_id:
        print(f"\nAttempting unsubscription for User ID {user1_id}...")
        unsubscribe_user(user1_id, reason="No longer interested")
        print(check_subscription_status(user1_id))

    if user2_id:
        print(f"\nAttempting unsubscription for User ID {user2_id}...")
        unsubscribe_user(user2_id) # No reason provided
        print(check_subscription_status(user2_id))

        print(f"\nAttempting to unsubscribe User ID {user2_id} again...")
        unsubscribe_user(user2_id, reason="Still not interested") # Try unsubscribing again with a reason
        print(check_subscription_status(user2_id))

    if user3_id is None:
        print("\nAttempting unsubscription for a non-logged-in user (simulated)...")
        unsubscribe_user(999, reason="Just testing") # Simulate unsubscription for a non-existent user
        print(check_subscription_status(999))

# --- Main Execution Block ---
if __name__ == "__main__":
    test_unsubscription()