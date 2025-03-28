import sqlite3
import hashlib
import os

DATABASE_FILE = 'users.db'

def create_users_table():
    """Creates the users table in the database if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("Users table created (if it didn't exist).")

def register_user(username, password):
    """Registers a new user by hashing the password and saving to the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        print(f"Username '{username}' already exists.")
        conn.close()
        return False

    # Hash the password using SHA-256
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        print(f"User '{username}' registered successfully.")
        conn.close()
        return True
    except sqlite3.IntegrityError:
        print(f"Error: Username '{username}' already exists (this should not happen due to the previous check).")
        conn.close()
        return False

def login_user(username, password):
    """Logs in an existing user by verifying the password."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_hash = result[0]
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if hashed_password == stored_hash:
            print(f"User '{username}' logged in successfully.")
            return True
        else:
            print("Incorrect password.")
            return False
    else:
        print(f"User '{username}' not found.")
        return False

def test_functionality():
    """Provides a way to test the registration and login functionality."""
    print("\n--- Testing User Registration and Login ---")

    # Ensure the database file exists and create the table if needed
    create_users_table()

    # Attempt to register a new user
    print("\nRegistering user 'testuser'")
    if register_user('testuser', 'securepassword123'):
        print("Registration successful.")
    else:
        print("Registration failed.")

    # Attempt to register the same user again
    print("\nAttempting to register 'testuser' again")
    register_user('testuser', 'anotherpassword')

    # Attempt to log in with the correct password
    print("\nLogging in as 'testuser' with the correct password")
    if login_user('testuser', 'securepassword123'):
        print("Login successful.")
    else:
        print("Login failed.")

    # Attempt to log in with an incorrect password
    print("\nLogging in as 'testuser' with an incorrect password")
    if login_user('testuser', 'wrongpassword'):
        print("Login successful (this should not happen).")
    else:
        print("Login failed (as expected).")

    # Attempt to log in with a non-existent user
    print("\nLogging in as 'nonexistentuser'")
    if login_user('nonexistentuser', 'anypassword'):
        print("Login successful (this should not happen).")
    else:
        print("Login failed (as expected).")

if __name__ == "__main__":
    test_functionality()