import sqlite3
import bcrypt

DATABASE_NAME = 'users.db'

def create_users_table():
    """Creates the users table in the database if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
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
    """Registers a new user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Username already exists."

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Insert the new user into the database
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                       (username, hashed_password.decode('utf-8')))
        conn.commit()
        conn.close()
        return True, "User registered successfully."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Error registering user (likely username conflict)."

def login_user(username, password):
    """Logs in an existing user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Retrieve the user by username
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_password_hash = result[0]
        # Verify the password against the stored hash
        if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            return True, "Login successful."
        else:
            return False, "Incorrect password."
    else:
        return False, "User not found."

def test_registration_and_login():
    """A simple function to test the registration and login functionality."""
    print("\n--- Testing Registration ---")
    registration_success, registration_message = register_user("testuser", "securepassword")
    print(f"Registration result: {registration_success} - {registration_message}")

    registration_success, registration_message = register_user("testuser", "anotherpassword")
    print(f"Registration result (duplicate username): {registration_success} - {registration_message}")

    print("\n--- Testing Login ---")
    login_success, login_message = login_user("testuser", "securepassword")
    print(f"Login result (correct password): {login_success} - {login_message}")

    login_success, login_message = login_user("testuser", "wrongpassword")
    print(f"Login result (incorrect password): {login_success} - {login_message}")

    login_success, login_message = login_user("nonexistentuser", "anypassword")
    print(f"Login result (user not found): {login_success} - {login_message}")

if __name__ == "__main__":
    # Ensure the users table exists
    create_users_table()

    # Run the test functions to demonstrate the functionality
    test_registration_and_login()

    # You can also interact with the functions directly here if needed
    # For example:
    # register_result, register_msg = register_user("anotheruser", "anothersecret")
    # print(f"\nRegistration: {register_msg}")
    # login_result, login_msg = login_user("anotheruser", "anothersecret")
    # print(f"Login: {login_msg}")