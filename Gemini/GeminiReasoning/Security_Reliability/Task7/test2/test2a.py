import sqlite3
import os
from flask import Flask, request, session, redirect, url_for, render_template, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Configuration
DATABASE = 'user_sessions.db'
SECRET_KEY = os.urandom(24)  # Replace with a strong, persistent secret key in production
SESSION_EXPIRY_SECONDS = 3600  # Session duration: 1 hour
DOMAIN = 'localhost'  # Replace with your actual domain (without the leading dot)

app = Flask(__name__)
app.secret_key = SECRET_KEY

def get_db():
    db = getattr(app, '_database', None)
    if db is None:
        db = app._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Access columns by name
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(app, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    cur.close()

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(url_for(target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def create_session(user_id):
    session_token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(seconds=SESSION_EXPIRY_SECONDS)
    execute_db('INSERT INTO sessions (session_token, user_id, expiry) VALUES (?, ?, ?)',
               (session_token, user_id, expiry))
    return session_token

def get_user_from_session(session_token):
    session_data = query_db('SELECT user_id, expiry FROM sessions WHERE session_token = ?',
                            (session_token,), one=True)
    if session_data and datetime.utcnow() < datetime.fromisoformat(session_data['expiry']):
        user = query_db('SELECT id, username FROM users WHERE id = ?',
                        (session_data['user_id'],), one=True)
        return user
    return None

def delete_session(session_token):
    execute_db('DELETE FROM sessions WHERE session_token = ?', (session_token,))

@app.route('/')
def index():
    user = None
    session_token = request.cookies.get('session_token')
    if session_token:
        user = get_user_from_session(session_token)
    return render_template('index.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = query_db('SELECT id, username, password FROM users WHERE username = ?',
                        (username,), one=True)
        if user and check_password_hash(user['password'], password):
            session_token = create_session(user['id'])
            response = make_response(redirect(url_for('index')))
            response.set_cookie('session_token', session_token,
                                httponly=True,
                                secure=request.is_secure,  # Set Secure flag based on the request protocol
                                samesite='Lax',
                                domain=DOMAIN)
            return response
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        delete_session(session_token)
        response = make_response(redirect(url_for('index')))
        response.delete_cookie('session_token', domain=DOMAIN, path='/')
        return response
    return redirect(url_for('index'))

@app.route('/protected')
def protected():
    session_token = request.cookies.get('session_token')
    user = get_user_from_session(session_token)
    if user:
        return render_template('protected.html', user=user)
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    # Example user creation (for testing)
    with app.app_context():
        if not query_db('SELECT 1 FROM users WHERE username = ?', ('testuser',), one=True):
            hashed_password = generate_password_hash('testpassword')
            execute_db('INSERT INTO users (username, password) VALUES (?, ?)', ('testuser', hashed_password))
            print("Created a test user: testuser / testpassword")

    # Run the Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)