from flask import Flask, request, redirect, url_for, render_template, make_response
import sqlite3
import os
from hashlib import sha256
import hmac
import secrets
import json
from datetime import datetime, timedelta
from functools import wraps

# --- Configuration ---
DATABASE = 'users.db'
SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)  # Generate a strong secret key if not set as env variable
COOKIE_NAME = 'session_token'
COOKIE_EXPIRY_SECONDS = 3600  # Session duration: 1 hour
DOMAIN = 'localhost'  # Replace with your actual domain (e.g., '.example.com')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

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
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        db.commit()

        # Create a test user if the table is empty
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            # In a real application, use proper password hashing (e.g., bcrypt)
            hashed_password = sha256("testpassword".encode()).hexdigest()
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ('testuser', hashed_password))
            db.commit()

# --- Security Helper Functions ---
def hash_password(password):
    # In a real application, use a strong password hashing library like bcrypt or Argon2
    return sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password):
    return stored_hash == hash_password(password)

def generate_session_signature(session_data):
    message = json.dumps(session_data).encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), message, sha256).hexdigest()
    return signature

def create_signed_session_cookie(user_id):
    session_data = {'user_id': user_id, 'timestamp': datetime.utcnow().isoformat()}
    signature = generate_session_signature(session_data)
    signed_value = f"{json.dumps(session_data)}.{signature}"
    response = make_response(redirect(url_for('dashboard')))
    response.set_cookie(
        COOKIE_NAME,
        signed_value,
        httponly=True,
        secure=True,  # Ensure HTTPS is used
        samesite='Strict',  # Or 'Lax' depending on your needs
        domain=DOMAIN,
        expires=datetime.utcnow() + timedelta(seconds=COOKIE_EXPIRY_SECONDS)
    )
    return response

def get_session_from_cookie():
    signed_value = request.cookies.get(COOKIE_NAME)
    if not signed_value:
        return None

    try:
        value, signature = signed_value.rsplit('.', 1)
        session_data = json.loads(value)
        expected_signature = generate_session_signature(session_data)
        if hmac.compare_digest(signature, expected_signature):
            return session_data
    except Exception:
        # Log the error for debugging
        print("Error verifying session cookie")
        return None
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session = get_session_from_cookie()
        if session and 'user_id' in session:
            # You might want to fetch the user object from the database here
            request.current_user_id = session['user_id']
            return f(*args, **kwargs)
        return redirect(url_for('login'))
    return decorated_function

# --- Routes ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hash_password(password)))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            error = "Username already exists."
            return render_template('register.html', error=error)
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user and verify_password(user['password_hash'], password):
            return create_signed_session_cookie(user['id'])
        error = "Invalid username or password."
        return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.delete_cookie(COOKIE_NAME, domain=DOMAIN, path='/')
    return response

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (request.current_user_id,))
    user = cursor.fetchone()
    username = user['username'] if user else 'Unknown'
    return render_template('dashboard.html', username=username)

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

# --- Test Functionality ---
if __name__ == '__main__':
    from flask import g
    init_db()
    # To test, you'll need to run this Flask application and access it through a web browser.
    # Make sure you are accessing it over HTTPS for the 'secure' cookie flag to work in most browsers.
    # You can use tools like ngrok to expose your local development server over HTTPS for testing.
    app.run(debug=True, host='0.0.0.0', port=5000)