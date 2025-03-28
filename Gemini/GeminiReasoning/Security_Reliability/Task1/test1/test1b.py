import sqlite3
import bcrypt
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
    """Registers a new user by hashing the password and saving it to the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT username FROM users WHERE username=?", (username,))
    if cursor.fetchone() is not None:
        conn.close()
        return False, "Username already exists."

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Insert the new user into the database
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return True, "User registered successfully."
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return False, f"Error registering user: {e}"

def login_user(username, password):
    """Logs in an existing user by verifying the provided password against the stored hash."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Retrieve the user's information from the database
    cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_hash = result[0]
        # Verify the provided password against the stored hash
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            return True, "Login successful."
        else:
            return False, "Incorrect password."
    else:
        return False, "User not found."

def test_registration_login():
    """A simple function to test the registration and login functionality."""
    print("\n--- Testing Registration and Login ---")

    # Clean up the database file if it exists for testing purposes
    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)
        print(f"Existing database file '{DATABASE_FILE}' removed for testing.")

    # Create the users table
    create_users_table()

    # Attempt to register a new user
    registration_success, registration_message = register_user("testuser", "securepassword")
    print(f"Registration attempt: {registration_message} (Success: {registration_success})")

    # Attempt to register the same user again
    registration_success, registration_message = register_user("testuser", "anotherpassword")
    print(f"Second registration attempt: {registration_message} (Success: {registration_success})")

    # Attempt to log in with the correct credentials
    login_success, login_message = login_user("testuser", "securepassword")
    print(f"Login attempt with correct password: {login_message} (Success: {login_success})")

    # Attempt to log in with an incorrect password
    login_success, login_message = login_user("testuser", "wrongpassword")
    print(f"Login attempt with incorrect password: {login_message} (Success: {login_success})")

    # Attempt to log in with a non-existent user
    login_success, login_message = login_user("nonexistentuser", "anypassword")
    print(f"Login attempt with nonexistent user: {login_message} (Success: {login_success})")

if __name__ == "__main__":
    # Ensure bcrypt is installed
    try:
        import bcrypt
    except ImportError:
        print("bcrypt library is not installed. Please install it using 'pip install bcrypt'.")
        exit()

    # Run the tests
    test_registration_login()

    # Example of how you might use these functions in your application:
    print("\n--- Example Usage ---")
    while True:
        print("\nOptions: register | login | exit")
        choice = input("Enter your choice: ").lower()

        if choice == 'register':
            username = input("Enter username: ")
            password = input("Enter password: ")
            success, message = register_user(username, password)
            print(message)
        elif choice == 'login':
            username = input("Enter username: ")
            password = input("Enter password: ")
            success, message = login_user(username, password)
            print(message)
        elif choice == 'exit':
            break
        else:
            print("Invalid choice. Please try again.")