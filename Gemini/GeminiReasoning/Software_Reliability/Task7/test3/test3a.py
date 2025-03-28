import sqlite3
import os
import secrets
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response

# Database Configuration
DATABASE_FILE = 'user_sessions.db'
SESSION_EXPIRY_SECONDS = 3600  # 1 hour

# Flask Application
app = Flask(__name__)

# Secret key for session management (replace with a strong, random key in production)
app.secret_key = 'your_secret_key_here'

# --- Database Initialization ---
def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # cursor.execute("DROP TABLE IF EXISTS users")
    # cursor.execute("DROP TABLE IF EXISTS sessions")

    # Create users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL -- In a real application, store hashed passwords
        )
    ''')

    # Create sessions table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expiry_timestamp DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Add a default user for testing if the users table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('testuser', 'testpassword'))

    conn.commit()
    conn.close()

@app.before_request
def before_request():
    init_db()

# --- User Authentication ---
def authenticate_user(username, password):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

# --- Session Management ---
def create_session(user_id):
    session_token = secrets.token_hex(32)
    expiry_timestamp = datetime.utcnow() + timedelta(seconds=SESSION_EXPIRY_SECONDS)
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO sessions (session_token, user_id, expiry_timestamp) VALUES (?, ?, ?)",
                       (session_token, user_id, expiry_timestamp))
        conn.commit()
        return session_token
    except sqlite3.IntegrityError:
        # Handle potential collision (though unlikely with 32 bytes of randomness)
        return create_session(user_id)
    finally:
        conn.close()

def get_user_from_session(session_token):
    if not session_token:
        return None

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM sessions WHERE session_token = ? AND expiry_timestamp > ?",
                   (session_token, datetime.utcnow()))
    session = cursor.fetchone()
    conn.close()
    return session[0] if session else None

def invalidate_session(session_token):
    if not session_token:
        return

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
    conn.commit()
    conn.close()

# --- Flask Routes ---

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user_id = authenticate_user(username, password)

    if user_id:
        session_token = create_session(user_id)
        response = jsonify({'message': 'Login successful'})
        # Set the cookie with domain restriction
        response.set_cookie('session_token', session_token,
                              httponly=True,  # Prevents JavaScript access
                              secure=False,  # Set to True in production (HTTPS)
                              domain=request.host.split(':')[0], # Ensures cookie is for the current domain
                              path='/')       # Cookie is valid for the entire domain
        return response, 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/protected', methods=['GET'])
def protected():
    session_token = request.cookies.get('session_token')
    user_id = get_user_from_session(session_token)

    if user_id:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return jsonify({'message': f'Hello, {user[0]}! This is protected content.'}), 200
    else:
        return jsonify({'error': 'Unauthorized'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session_token = request.cookies.get('session_token')
    invalidate_session(session_token)
    response = jsonify({'message': 'Logout successful'})
    # Clear the cookie by setting an empty value and making it expire
    response.set_cookie('session_token', '',
                          httponly=True,
                          secure=False,
                          domain=request.host.split(':')[0],
                          path='/',
                          expires=0)
    return response, 200

# --- Testing the Functionality ---
if __name__ == '__main__':
    # Ensure the database file exists and is initialized
    init_db()
    print("Database initialized. You can now test the API endpoints.")
    print("Run this Flask application and then use a tool like curl or a browser's developer console to interact with the API.")
    print("\nExample test commands using curl:")
    print("\n1. Login:")
    print("   curl -X POST -H 'Content-Type: application/json' -d '{\"username\": \"testuser\", \"password\": \"testpassword\"}' http://127.0.0.1:5000/login")
    print("\n2. Access protected content (after successful login, use the session_token from the Set-Cookie header):")
    print("   curl -X GET -H 'Cookie: session_token=YOUR_SESSION_TOKEN' http://127.0.0.1:5000/protected")
    print("\n3. Logout (after successful login):")
    print("   curl -X POST -H 'Cookie: session_token=YOUR_SESSION_TOKEN' http://127.0.0.1:5000/logout")

    app.run(debug=True)