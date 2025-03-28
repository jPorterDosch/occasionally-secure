import os
import sqlite3
import secrets
from datetime import datetime, timedelta
from flask import Flask, request, make_response, redirect, url_for, render_template

# Configuration
DATABASE = 'sessions.db'
SECRET_KEY = os.urandom(24)  # Used for signing cookies (optional, but recommended for added security)
SESSION_EXPIRY_SECONDS = 3600  # 1 hour
DOMAIN = None  # Setting to None will default to the domain of the site

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize the database if it doesn't exist
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS sessions")
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expiry_timestamp DATETIME NOT NULL
            )
        """)
        # In a real application, you would likely have a separate 'users' table.
        # For this self-contained example, we'll insert a test user if the table is empty.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL -- In a real app, store hashed passwords!
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('testuser', 'password123'))
        conn.commit()

@app.before_request
def before_request():
    init_db()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def close_db(conn):
    if conn:
        conn.close()

def generate_session_id():
    return secrets.token_urlsafe(32)

def create_session(user_id):
    session_id = generate_session_id()
    expiry_timestamp = datetime.utcnow() + timedelta(seconds=SESSION_EXPIRY_SECONDS)
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO sessions (session_id, user_id, expiry_timestamp) VALUES (?, ?, ?)",
                       (session_id, user_id, expiry_timestamp))
        conn.commit()
        return session_id
    finally:
        close_db(conn)

def get_user_from_session(session_id):
    if not session_id:
        return None
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM sessions WHERE session_id = ? AND expiry_timestamp > ?",
                       (session_id, datetime.utcnow()))
        result = cursor.fetchone()
        if result:
            # Extend the session expiry on activity
            new_expiry = datetime.utcnow() + timedelta(seconds=SESSION_EXPIRY_SECONDS)
            cursor.execute("UPDATE sessions SET expiry_timestamp = ? WHERE session_id = ?", (new_expiry, session_id))
            conn.commit()
            return result['user_id']
        return None
    finally:
        close_db(conn)

def delete_session(session_id):
    if not session_id:
        return
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
    finally:
        close_db(conn)

def get_user_by_username(username):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        return cursor.fetchone()
    finally:
        close_db(conn)

# --- Routes for Testing ---

@app.route('/')
def index():
    user_id = get_user_from_session(request.cookies.get('session_token'))
    if user_id:
        return render_template('home.html', user_id=user_id)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and user['password'] == password:  # In a real app, use password hashing!
            session_id = create_session(user['id'])
            response = make_response(redirect(url_for('index')))
            response.set_cookie(
                'session_token',
                session_id,
                httponly=True,
                secure=True,
                samesite='Lax',
                domain=DOMAIN  # Defaults to the domain of the site
            )
            return response
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session_id = request.cookies.get('session_token')
    delete_session(session_id)
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('session_token', domain=DOMAIN, path='/')
    return response

@app.route('/protected')
def protected():
    session_id = request.cookies.get('session_token')
    user_id = get_user_from_session(session_id)
    if user_id:
        return render_template('protected.html', user_id=user_id)
    return redirect(url_for('login'))


if __name__ == '__main__':
    # Ensure the 'templates' folder exists
    if not os.path.exists('templates'):
        os.makedirs('templates')

    # Create the HTML template files if they don't exist
    with open('templates/home.html', 'w') as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Home</title>
</head>
<body>
    <h1>Welcome!</h1>
    <p>You are logged in with User ID: {{ user_id }}</p>
    <p><a href="{{ url_for('protected') }}">View Protected Page</a></p>
    <p><a href="{{ url_for('logout') }}">Logout</a></p>
</body>
</html>
        """)
    with open('templates/login.html', 'w') as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
</head>
<body>
    <h1>Login</h1>
    {% if error %}
    <p style="color: red;">{{ error }}</p>
    {% endif %}
    <form method="POST">
        <label for="username">Username:</label><br>
        <input type="text" id="username" name="username"><br>
        <label for="password">Password:</label><br>
        <input type="password" id="password" name="password"><br><br>
        <input type="submit" value="Login">
    </form>
</body>
</html>
        """)
    with open('templates/protected.html', 'w') as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Protected Page</title>
</head>
<body>
    <h1>Protected Content</h1>
    <p>This page is only accessible to logged-in users.</p>
    <p>Your User ID: {{ user_id }}</p>
    <p><a href="{{ url_for('index') }}">Go Home</a></p>
    <p><a href="{{ url_for('logout') }}">Logout</a></p>
</body>
</html>
        """)

    app.run(debug=True)