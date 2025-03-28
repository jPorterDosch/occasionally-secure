import sqlite3
from flask import Flask, request, redirect, url_for, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime, timedelta
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Replace with a strong, persistent secret key for production

DATABASE = 'ecommerce.db'

# --- Database Helper Functions ---

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
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# --- Database Initialization ---

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

# --- Decorator for Protected Routes ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = request.cookies.get('session_token')
        if not session_token:
            return redirect(url_for('login'))

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT user_id, expiry FROM sessions WHERE session_token = ?", (session_token,))
        session_data = cursor.fetchone()

        if not session_data:
            response = make_response(redirect(url_for('login')))
            response.delete_cookie('session_token', domain=request.host)
            return response

        expiry = datetime.fromisoformat(session_data['expiry'])
        if datetime.now() > expiry:
            cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
            db.commit()
            response = make_response(redirect(url_for('login')))
            response.delete_cookie('session_token', domain=request.host)
            return response

        cursor.execute("SELECT username FROM users WHERE id = ?", (session_data['user_id'],))
        user = cursor.fetchone()
        if not user:
            response = make_response(redirect(url_for('login')))
            response.delete_cookie('session_token', domain=request.host)
            return response

        session['user_id'] = session_data['user_id']
        session['username'] = user['username']
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters long.'

        if error is None:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone() is not None:
                error = f'User {username} is already registered.'
            else:
                hashed_password = generate_password_hash(password)
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                db.commit()
                return redirect(url_for('login'))
        flash(error)
    return '''
        <h1>Register</h1>
        <form method="post">
            <label for="username">Username:</label>
            <input type="text" name="username" id="username" required><br><br>
            <label for="password">Password:</label>
            <input type="password" name="password" id="password" required><br><br>
            <input type="submit" value="Register">
        </form>
        <p>Already have an account? <a href="/login">Log In</a></p>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session_token = str(uuid.uuid4())
            expiry_date = datetime.now() + timedelta(hours=2)  # Session expires in 2 hours

            cursor.execute(
                "INSERT INTO sessions (session_token, user_id, expiry) VALUES (?, ?, ?)",
                (session_token, user['id'], expiry_date.isoformat())
            )
            db.commit()

            response = make_response(redirect(url_for('home')))
            response.set_cookie(
                'session_token',
                session_token,
                domain=request.host,  # Ensures the cookie is only for the current domain
                httponly=True,      # Prevents JavaScript access to the cookie
                secure=True,        # Only send the cookie over HTTPS (in production)
                samesite='Strict'   # Prevents the cookie from being sent on cross-site requests
            )
            return response
        flash(error)
    return '''
        <h1>Log In</h1>
        <form method="post">
            <label for="username">Username:</label>
            <input type="text" name="username" id="username" required><br><br>
            <label for="password">Password:</label>
            <input type="password" name="password" id="password" required><br><br>
            <input type="submit" value="Log In">
        </form>
        <p>Don't have an account? <a href="/register">Register</a></p>
    '''

@app.route('/')
@login_required
def home():
    return f'''
        <h1>Welcome, {session['username']}!</h1>
        <p><a href="/logout">Log Out</a></p>
    '''

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
        db.commit()

    response = make_response(redirect(url_for('login')))
    response.delete_cookie('session_token', domain=request.host)
    return response

@app.route('/profile')
@login_required
def profile():
    return f'''
        <h1>User Profile</h1>
        <p>User ID: {session['user_id']}</p>
        <p>Username: {session['username']}</p>
        <p><a href="/">Home</a> | <a href="/logout">Log Out</a></p>
    '''

from flask import flash

@app.route('/protected')
@login_required
def protected():
    return f'''
        <h1>This is a Protected Page</h1>
        <p>You are logged in as user ID: {session['user_id']}</p>
        <p><a href="/">Home</a> | <a href="/profile">Profile</a> | <a href="/logout">Log Out</a></p>
    '''

# --- Helper for Flashing Messages ---
def flash(message):
    session['flash'] = session.get('flash', []) + [message]

@app.route('/flash-messages')
def show_flash_messages():
    messages = session.pop('flash', [])
    if messages:
        return ''.join([f'<p style="color: red;">{msg}</p>' for msg in messages])
    return ''

if __name__ == '__main__':
    # This part is for development and testing.
    # In a production environment, you would typically use a WSGI server like Gunicorn or uWSGI.
    with app.app_context():
        init_db() # Initialize the database if it doesn't exist
    app.run(debug=True, host='127.0.0.1', port=5000)