import sqlite3
import bcrypt

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
    """Registers a new user by hashing the password and saving to the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
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
        conn.close()
        return False, f"Error during registration: {e}"

def login_user(username, password):
    """Logs in a user by verifying the provided password against the stored hash."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_hash = result[0]
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            return True, "Login successful."
        else:
            return False, "Incorrect password."
    else:
        return False, "User not found."

def test_registration_and_login():
    """A simple function to test the registration and login functionality."""
    create_users_table()  # Ensure the table exists

    # Test registration
    print("\nTesting Registration:")
    registration_success, registration_message = register_user("testuser", "securepassword")
    print(f"- Registering 'testuser': {registration_message} (Success: {registration_success})")

    registration_fail, fail_message = register_user("testuser", "anotherpassword")
    print(f"- Registering 'testuser' again: {fail_message} (Success: {registration_fail})")

    registration_success_2, success_message_2 = register_user("anotheruser", "differentpassword")
    print(f"- Registering 'anotheruser': {success_message_2} (Success: {registration_success_2})")

    # Test login
    print("\nTesting Login:")
    login_success, login_message = login_user("testuser", "securepassword")
    print(f"- Logging in 'testuser' with correct password: {login_message} (Success: {login_success})")

    login_fail, fail_message = login_user("testuser", "wrongpassword")
    print(f"- Logging in 'testuser' with incorrect password: {fail_message} (Success: {login_fail})")

    login_fail_user, fail_message_user = login_user("nonexistentuser", "anypassword")
    print(f"- Logging in 'nonexistentuser': {fail_message_user} (Success: {login_fail_user})")

if __name__ == "__main__":
    test_registration_and_login()