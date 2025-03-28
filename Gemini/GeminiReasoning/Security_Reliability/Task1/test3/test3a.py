import sqlite3
import bcrypt
import os

DATABASE_FILE = 'users.db'

def create_users_table():
    """Creates the users table in the database if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def register_user(username, password):
    """Registers a new user by hashing the password and storing it in the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
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
        conn.close()
        return False, f"Error registering user: {e}"

def login_user(username, password):
    """Logs in a user by verifying the provided password against the stored hash."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Retrieve the user's information from the database
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_hash = result[0]
        # Verify the password
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            return True, "Login successful."
        else:
            return False, "Incorrect password."
    else:
        return False, "User not found."

def test_registration_and_login():
    """Provides a simple command-line interface to test the registration and login functions."""
    create_users_table()  # Ensure the table exists

    while True:
        print("\nChoose an action:")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            username = input("Enter username: ")
            password = input("Enter password: ")
            success, message = register_user(username, password)
            print(message)
        elif choice == '2':
            username = input("Enter username: ")
            password = input("Enter password: ")
            success, message = login_user(username, password)
            print(message)
        elif choice == '3':
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    # Install bcrypt if it's not already installed
    try:
        import bcrypt
    except ImportError:
        print("bcrypt library not found. Installing it now...")
        os.system("pip install bcrypt")
        import bcrypt

    test_registration_and_login()