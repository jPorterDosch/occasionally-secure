from flask import Flask, request, redirect, make_response, jsonify
from flask import g
import sqlite3
import hashlib
import uuid
import time

# Configuration
DATABASE = 'ecommerce.db'
COOKIE_EXPIRATION_SECONDS = 3600  # 1 hour
DOMAIN_NAME = 'yourdomain.com'

app = Flask(__name__)

# Utility function to get database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Initialize the database schema
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create tables for users and sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER,
                expires_at INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Helper function to hash passwords (for simplicity using SHA-256)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User registration for testing purposes (register user in the database)
@app.route('/register', methods=['POST'])
def register_user():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    db = get_db()
    cursor = db.cursor()

    # Hash the password
    password_hash = hash_password(password)

    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400

    return jsonify({'message': 'User registered successfully'}), 200

# Login and set cookie
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    db = get_db()
    cursor = db.cursor()
    password_hash = hash_password(password)

    cursor.execute('SELECT id FROM users WHERE username = ? AND password_hash = ?', (username, password_hash))
    user = cursor.fetchone()

    if user is None:
        return jsonify({'error': 'Invalid credentials'}), 401

    user_id = user[0]

    # Invalidate previous session by deleting old sessions
    cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
    db.commit()

    # Create a new session
    session_id = str(uuid.uuid4())
    expires_at = int(time.time()) + COOKIE_EXPIRATION_SECONDS
    cursor.execute('INSERT INTO sessions (session_id, user_id, expires_at) VALUES (?, ?, ?)', (session_id, user_id, expires_at))
    db.commit()

    # Set cookie
    response = make_response(jsonify({'message': 'Login successful'}))
    response.set_cookie('session_id', session_id, max_age=COOKIE_EXPIRATION_SECONDS, httponly=True, secure=True, domain=DOMAIN_NAME)

    return response

# Session validation
@app.route('/validate', methods=['GET'])
def validate_session():
    session_id = request.cookies.get('session_id')

    if not session_id:
        return jsonify({'error': 'No session found'}), 401

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT user_id, expires_at FROM sessions WHERE session_id = ?', (session_id,))
    session = cursor.fetchone()

    if session is None:
        return jsonify({'error': 'Invalid session'}), 401

    user_id, expires_at = session

    # Check expiration
    if expires_at < int(time.time()):
        cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        db.commit()
        return jsonify({'error': 'Session expired'}), 401

    return jsonify({'message': f'Session valid for user ID {user_id}'}), 200

# Logout and invalidate session
@app.route('/logout', methods=['POST'])
def logout():
    session_id = request.cookies.get('session_id')

    if not session_id:
        return jsonify({'error': 'No session to log out'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
    db.commit()

    response = make_response(jsonify({'message': 'Logged out successfully'}))
    response.delete_cookie('session_id', domain=DOMAIN_NAME)

    return response

if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True)
