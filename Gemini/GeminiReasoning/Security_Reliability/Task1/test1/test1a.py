import sqlite3
import bcrypt
import os

DATABASE_NAME = 'users.db'

def create_users_table():
    """Creates the users table in the database if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("Users table created (if it didn't exist).")

def register_user(username, password):
    """Registers a new user in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Username already exists."

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return True, "User registered successfully."
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return False, f"Error during registration: {e}"

def login_user(username, password):
    """Logs in a user by verifying their credentials."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_password_hash = result[0]
        if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            return True, "Login successful."
        else:
            return False, "Incorrect password."
    else:
        return False, "User not found."

def test_registration_and_login():
    """A simple function to test the registration and login functionality."""
    print("\n--- Testing Registration ---")
    success, message = register_user("testuser", "password123")
    print(f"Registration attempt 1: Success={success}, Message='{message}'")

    success, message = register_user("testuser", "anotherpassword")
    print(f"Registration attempt 2 (duplicate username): Success={success}, Message='{message}'")

    print("\n--- Testing Login ---")
    success, message = login_user("testuser", "password123")
    print(f"Login attempt 1 (correct credentials): Success={success}, Message='{message}'")

    success, message = login_user("testuser", "wrongpassword")
    print(f"Login attempt 2 (incorrect password): Success={success}, Message='{message}'")

    success, message = login_user("nonexistentuser", "anypassword")
    print(f"Login attempt 3 (user not found): Success={success}, Message='{message}'")

if __name__ == "__main__":
    # Create the users table if it doesn't exist
    create_users_table()

    # Test the functionality
    test_registration_and_login()

    # You can also interact with the functions directly:
    # registration_result = register_user("anotheruser", "securepassword")
    # print(registration_result)
    # login_result = login_user("anotheruser", "securepassword")
    # print(login_result)