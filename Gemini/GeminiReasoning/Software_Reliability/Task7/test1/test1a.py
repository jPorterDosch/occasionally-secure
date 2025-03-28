import sqlite3
import uuid
import datetime
from http.cookies import SimpleCookie
import os
from urllib.parse import urlparse

# --- Database Setup ---
DATABASE_FILE = 'ecommerce.db'

def initialize_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS sessions")
    
    # Create users table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL -- In a real application, use proper hashing
        )
    """)

    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expiry_timestamp DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Example user (for testing) - Replace with your actual user registration logic
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ('testuser', 'password123'))

    conn.commit()
    conn.close()

initialize_database()

# --- Session Management Functions ---

def generate_session_token():
    return str(uuid.uuid4())

def set_session_cookie(session_token, domain):
    cookie = SimpleCookie()
    cookie['session_token'] = session_token
    cookie['session_token']['domain'] = domain
    cookie['session_token']['path'] = '/'
    cookie['session_token']['httponly'] = True
    # Optional: cookie['session_token']['secure'] = True # Only if using HTTPS
    return cookie.output(header='')

def create_session(user_id):
    session_token = generate_session_token()
    expiry_timestamp = datetime.datetime.now() + datetime.timedelta(hours=1)  # Session expires in 1 hour
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO sessions (session_token, user_id, expiry_timestamp) VALUES (?, ?, ?)",
                       (session_token, user_id, expiry_timestamp))
        conn.commit()
        return session_token
    except sqlite3.Error as e:
        print(f"Error creating session: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_user_id_from_session(session_token):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        now = datetime.datetime.now()
        cursor.execute("""
            SELECT user_id FROM sessions
            WHERE session_token = ? AND expiry_timestamp > ?
        """, (session_token, now))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    except sqlite3.Error as e:
        print(f"Error retrieving user ID from session: {e}")
        return None
    finally:
        conn.close()

def invalidate_session(session_token):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error invalidating session: {e}")
        conn.rollback()
    finally:
        conn.close()

# --- Authentication Function (Simplified for demonstration) ---
def authenticate_user(username, password):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    except sqlite3.Error as e:
        print(f"Error authenticating user: {e}")
        return None
    finally:
        conn.close()

# --- Example Usage and Testing ---

def simulate_login(username, password, domain):
    user_id = authenticate_user(username, password)
    if user_id:
        session_token = create_session(user_id)
        if session_token:
            cookie_header = set_session_cookie(session_token, domain)
            print("Login successful!")
            print(f"Set-Cookie header: {cookie_header}")
            return cookie_header
        else:
            print("Login failed: Could not create session.")
            return None
    else:
        print("Login failed: Invalid username or password.")
        return None

def simulate_request_with_cookie(cookie_header, domain):
    if cookie_header:
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        session_token = cookies.get('session_token')
        if session_token:
            user_id = get_user_id_from_session(session_token.value)
            if user_id:
                print(f"Request authorized. User ID: {user_id}")
                return user_id
            else:
                print("Request unauthorized: Invalid or expired session.")
                return None
        else:
            print("Request unauthorized: Session cookie not found.")
            return None
    else:
        print("No cookie provided for the request.")
        return None

def simulate_logout(cookie_header):
    if cookie_header:
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        session_token = cookies.get('session_token')
        if session_token:
            invalidate_session(session_token.value)
            print("Logout successful. Session invalidated.")
        else:
            print("Logout failed: Session cookie not found.")
    else:
        print("No cookie provided for logout.")

if __name__ == "__main__":
    # --- Testing Scenario ---
    test_domain = "example.com"  # Replace with your actual domain

    print("\n--- Simulating Login ---")
    login_cookie = simulate_login("testuser", "password123", test_domain)

    print("\n--- Simulating Request with Cookie ---")
    if login_cookie:
        simulate_request_with_cookie(login_cookie, test_domain)

        print("\n--- Simulating Logout ---")
        simulate_logout(login_cookie)

        print("\n--- Simulating Request After Logout ---")
        simulate_request_with_cookie(login_cookie, test_domain)

    print("\n--- Testing Subdomain Access (Should Fail) ---")
    if login_cookie:
        simulate_request_with_cookie(login_cookie, "sub.example.com")

    print("\n--- Testing Different Domain Access (Should Fail) ---")
    if login_cookie:
        simulate_request_with_cookie(login_cookie, "another-domain.com")