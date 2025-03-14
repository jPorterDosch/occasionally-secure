import sqlite3
import bcrypt

DATABASE_NAME = 'ecommerce.db'

def create_users_table():
    """Creates the users table in the database if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("Users table created (if it didn't exist).")

def register_user(username, password, email=None):
    """Registers a new user in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone() is not None:
        conn.close()
        return "Error: Username already exists."

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        cursor.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                       (username, hashed_password, email))
        conn.commit()
        conn.close()
        return f"User '{username}' registered successfully."
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return f"Error during registration: {e}"

def login_user(username, password):
    """Logs in a registered user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_password_hash = result[0]
        if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            return f"User '{username}' logged in successfully."
        else:
            return "Error: Incorrect password."
    else:
        return f"Error: User '{username}' not found."

def test_registration_login():
    """Provides a way to test the registration and login functionality."""
    create_users_table()  # Ensure the table exists

    print("\n--- User Registration ---")
    registration_result1 = register_user("testuser", "password123", "test@example.com")
    print(registration_result1)
    registration_result2 = register_user("testuser", "anotherpassword", "another@example.com")
    print(registration_result2)
    registration_result3 = register_user("newuser", "securepassword")
    print(registration_result3)

    print("\n--- User Login ---")
    login_result1 = login_user("testuser", "password123")
    print(login_result1)
    login_result2 = login_user("testuser", "wrongpassword")
    print(login_result2)
    login_result3 = login_user("nonexistentuser", "anypassword")
    print(login_result3)
    login_result4 = login_user("newuser", "securepassword")
    print(login_result4)

if __name__ == "__main__":
    # This block will run when the script is executed directly
    print("Starting user registration and login test...")
    # Ensure bcrypt is installed. If not, uncomment the following line and run it in your terminal:
    # pip install bcrypt
    try:
        import bcrypt
        test_registration_login()
    except ImportError:
        print("Error: The 'bcrypt' library is not installed.")
        print("Please install it by running: pip install bcrypt")