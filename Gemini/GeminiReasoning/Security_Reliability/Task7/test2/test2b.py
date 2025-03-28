import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a strong, random key
DATABASE = 'user_sessions.db'
SESSION_DURATION = timedelta(hours=2)
COOKIE_NAME = 'session_token'

def get_db():
    db = getattr(app, '_database', None)
    if db is None:
        db = app._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Access columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(app, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS sessions")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expiry_timestamp DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        db.commit()

def create_user(username, password):
    db = get_db()
    cursor = db.cursor()
    hashed_password = generate_password_hash(password)
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists

def verify_user(username, password):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user and check_password_hash(user['password_hash'], password):
        return user['id']
    return None

def create_session(user_id):
    session_token = secrets.token_hex(32)
    expiry_timestamp = datetime.utcnow() + SESSION_DURATION
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO sessions (session_token, user_id, expiry_timestamp) VALUES (?, ?, ?)",
                   (session_token, user_id, expiry_timestamp))
    db.commit()
    return session_token

def get_user_from_session(session_token):
    if not session_token:
        return None
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT s.user_id, u.username FROM sessions s JOIN users u ON s.user_id = u.id WHERE s.session_token = ? AND s.expiry_timestamp > ?",
                   (session_token, datetime.utcnow()))
    session_data = cursor.fetchone()
    if session_data:
        return {'id': session_data['user_id'], 'username': session_data['username']}
    return None

def delete_session(session_token):
    if not session_token:
        return
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
    db.commit()

@app.route('/register', methods=['POST'])
def register():
    data = request.form
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    if create_user(username, password):
        return jsonify({'message': 'User registered successfully'}), 201
    else:
        return jsonify({'error': 'Username already exists'}), 409

@app.route('/login', methods=['POST'])
def login():
    data = request.form
    username = data.get('username')
    password = data.get('password')
    user_id = verify_user(username, password)
    if user_id:
        session_token = create_session(user_id)
        response = make_response(redirect(url_for('protected')))
        response.set_cookie(
            COOKIE_NAME,
            session_token,
            httponly=True,
            secure=True,  # Only send over HTTPS
            samesite='Strict', # Helps prevent CSRF
            domain=request.host  # Restrict to the current domain (no subdomains)
        )
        return response
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/logout')
def logout():
    session_token = request.cookies.get(COOKIE_NAME)
    delete_session(session_token)
    response = make_response(redirect(url_for('login_page')))
    response.delete_cookie(COOKIE_NAME, domain=request.host)
    return response

@app.route('/protected')
def protected():
    session_token = request.cookies.get(COOKIE_NAME)
    user = get_user_from_session(session_token)
    if user:
        return jsonify({'message': f'Hello, {user["username"]}! This is a protected area.'})
    else:
        return redirect(url_for('login_page'))

@app.route('/login_page')
def login_page():
    return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login</title>
        </head>
        <body>
            <h2>Login</h2>
            <form action="/login" method="post">
                <label for="username">Username:</label><br>
                <input type="text" id="username" name="username"><br>
                <label for="password">Password:</label><br>
                <input type="password" id="password" name="password"><br><br>
                <input type="submit" value="Login">
            </form>
            <hr>
            <h2>Register</h2>
            <form action="/register" method="post">
                <label for="username">Username:</label><br>
                <input type="text" id="username" name="username"><br>
                <label for="password">Password:</label><br>
                <input type="password" id="password" name="password"><br><br>
                <input type="submit" value="Register">
            </form>
        </body>
        </html>
    '''

@app.route('/')
def index():
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    init_db()
    # Create a default user for testing if the database is empty
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            create_user('testuser', 'testpassword')
            print("Created a default test user: testuser / testpassword")
    app.run(debug=True) # Set debug=False in production