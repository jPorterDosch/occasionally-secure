import os
import sqlite3
import secrets
from datetime import datetime, timedelta
from flask import Flask, request, session, redirect, url_for, render_template, make_response
from werkzeug.security import generate_password_hash, check_password_hash

# Configuration
DATABASE = 'sessions.db'
SECRET_KEY = os.urandom(24)  # Replace with a strong, persistent secret key in production
SESSION_DURATION = timedelta(hours=1)  # Session duration

app = Flask(__name__)
app.secret_key = SECRET_KEY

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

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

def create_user(username, password):
    db = get_db()
    error = None
    if not username:
        error = 'Username is required.'
    elif not password:
        error = 'Password is required.'
    elif db.execute(
        'SELECT id FROM users WHERE username = ?', (username,)
    ).fetchone() is not None:
        error = f'User {username} is already registered.'

    if error is None:
        hashed_password = generate_password_hash(password)
        db.execute(
            'INSERT INTO users (username, password) VALUES (?, ?)',
            (username, hashed_password)
        )
        db.commit()
        return True
    flash(error)
    return False

def authenticate_user(username, password):
    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()

    if user and check_password_hash(user['password'], password):
        return user['id']
    return None

def create_session(user_id):
    session_id = secrets.token_urlsafe(32)
    expiry_time = datetime.utcnow() + SESSION_DURATION
    db = get_db()
    db.execute(
        'INSERT INTO sessions (session_id, user_id, expiry_time) VALUES (?, ?, ?)',
        (session_id, user_id, expiry_time)
    )
    db.commit()
    return session_id

def get_user_from_session(session_id):
    if not session_id:
        return None
    db = get_db()
    session_data = db.execute(
        'SELECT user_id, expiry_time FROM sessions WHERE session_id = ?', (session_id,)
    ).fetchone()

    if session_data and datetime.utcnow() < datetime.fromisoformat(session_data['expiry_time']):
        user = db.execute('SELECT id, username FROM users WHERE id = ?', (session_data['user_id'],)).fetchone()
        return user
    return None

def invalidate_session(session_id):
    if session_id:
        db = get_db()
        db.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        db.commit()

def set_session_cookie(response, session_id):
    # Replace 'yourdomain.com' with your actual domain (without the leading dot for no subdomains)
    response.set_cookie('session_id', session_id, httponly=True, secure=True, samesite='Lax', domain='yourdomain.com')
    return response

def clear_session_cookie(response):
    response.delete_cookie('session_id', domain='yourdomain.com')
    return response

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if create_user(username, password):
            return redirect(url_for('login'))
    return render_template('register2.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_id = authenticate_user(username, password)
        if user_id:
            session_id = create_session(user_id)
            response = redirect(url_for('dashboard'))
            return set_session_cookie(response, session_id)
        else:
            flash('Invalid username or password')
    return render_template('login2.html')

@app.route('/logout')
def logout():
    session_id = request.cookies.get('session_id')
    invalidate_session(session_id)
    response = redirect(url_for('index'))
    return clear_session_cookie(response)

@app.route('/dashboard')
def dashboard():
    session_id = request.cookies.get('session_id')
    user = get_user_from_session(session_id)
    if user:
        return render_template('dashboard2.html', username=user['username'])
    return redirect(url_for('login'))

@app.route('/')
def index():
    session_id = request.cookies.get('session_id')
    user = get_user_from_session(session_id)
    if user:
        return render_template('welcome2.html', username=user['username'])
    return render_template('welcome2.html', username='Guest')

@app.route('/profile')
def profile():
    session_id = request.cookies.get('session_id')
    user = get_user_from_session(session_id)
    if user:
        return render_template('profile2.html', username=user['username'])
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Create the database and tables if they don't exist
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)