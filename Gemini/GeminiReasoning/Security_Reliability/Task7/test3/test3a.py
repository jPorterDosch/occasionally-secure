import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, session, redirect, url_for, render_template, make_response

# --- Configuration ---
DATABASE = 'sessions.db'
SECRET_KEY = os.urandom(24)  # Generate a strong secret key
SESSION_COOKIE_NAME = 'session_id'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True  # Should be True in production (HTTPS)
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_DOMAIN = None  # Set to your main domain (e.g., '.yourdomain.com') in production
SESSION_LIFETIME = timedelta(hours=2)  # Session duration

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_NAME'] = SESSION_COOKIE_NAME
app.config['SESSION_COOKIE_HTTPONLY'] = SESSION_COOKIE_HTTPONLY
app.config['SESSION_COOKIE_SECURE'] = SESSION_COOKIE_SECURE
app.config['SESSION_COOKIE_SAMESITE'] = SESSION_COOKIE_SAMESITE
app.config['SESSION_COOKIE_DOMAIN'] = SESSION_COOKIE_DOMAIN
app.config['PERMANENT_SESSION_LIFETIME'] = SESSION_LIFETIME

# --- Database Initialization ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Access columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

# Create schema.sql file in the same directory with the following content:
"""
DROP TABLE IF EXISTS sessions;
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expiry_timestamp DATETIME NOT NULL
);
"""

# --- User Authentication (Simplified for Example) ---
# In a real application, you would have a more robust user authentication system.
users = {
    1: {'username': 'testuser', 'password': 'password123'},
    2: {'username': 'anotheruser', 'password': 'securepassword'}
}

def verify_user(username, password):
    for user_id, user_data in users.items():
        if user_data['username'] == username and user_data['password'] == password:
            return user_id
    return None

# --- Session Management ---
def generate_session_id():
    return secrets.token_urlsafe(32)

def create_session(user_id):
    session_id = generate_session_id()
    expiry_timestamp = datetime.utcnow() + app.config['PERMANENT_SESSION_LIFETIME']
    db = get_db()
    db.execute('INSERT INTO sessions (session_id, user_id, expiry_timestamp) VALUES (?, ?, ?)',
               (session_id, user_id, expiry_timestamp))
    db.commit()
    return session_id

def get_session_data(session_id):
    db = get_db()
    session_data = db.execute('SELECT user_id, expiry_timestamp FROM sessions WHERE session_id = ?', (session_id,)).fetchone()
    if session_data:
        if datetime.utcnow() < datetime.fromisoformat(session_data['expiry_timestamp']):
            return session_data['user_id']
        else:
            # Session expired, remove from database
            delete_session(session_id)
    return None

def delete_session(session_id):
    db = get_db()
    db.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
    db.commit()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get(app.config['SESSION_COOKIE_NAME'])
        user_id = None
        if session_id:
            user_id = get_session_data(session_id)

        if user_id is None:
            return redirect(url_for('login'))
        session['user_id'] = user_id  # Store user ID in Flask's session for convenience
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route('/')
@login_required
def index():
    user_id = session.get('user_id')
    user = users.get(user_id)
    return render_template('index1.html', username=user['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_id = verify_user(username, password)
        if user_id:
            session_id = create_session(user_id)
            response = make_response(redirect(url_for('index')))
            response.set_cookie(
                app.config['SESSION_COOKIE_NAME'],
                session_id,
                httponly=app.config['SESSION_COOKIE_HTTPONLY'],
                secure=app.config['SESSION_COOKIE_SECURE'],
                samesite=app.config['SESSION_COOKIE_SAMESITE'],
                domain=app.config['SESSION_COOKIE_DOMAIN'],
                expires=datetime.utcnow() + app.config['PERMANENT_SESSION_LIFETIME']
            )
            return response
        else:
            return render_template('login1.html', error='Invalid credentials')
    return render_template('login1.html')

@app.route('/logout')
@login_required
def logout():
    session_id = request.cookies.get(app.config['SESSION_COOKIE_NAME'])
    if session_id:
        delete_session(session_id)
    response = make_response(redirect(url_for('login')))
    response.delete_cookie(
        app.config['SESSION_COOKIE_NAME'],
        domain=app.config['SESSION_COOKIE_DOMAIN'],
        path='/' # Ensure the cookie is deleted regardless of the path it was set on
    )
    session.pop('user_id', None)
    return response

# --- Helper for setting the domain ---
@app.before_request
def set_domain():
    # In a real application, you might want to read this from a config file
    app.config['SESSION_COOKIE_DOMAIN'] = 'localhost' # Replace with your actual domain

# --- Main Execution ---
if __name__ == '__main__':
    from flask import g
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True, host='0.0.0.0')