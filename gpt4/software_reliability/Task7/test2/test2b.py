from flask import Flask, request, redirect, url_for, render_template, session, make_response
from datetime import timedelta
import sqlite3
import os

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Set session expiration time (30 minutes)

# Database file
DB_FILE = 'users.db'

# Database initialization: creating tables if they do not exist
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    
    # Create sessions table to store session tokens (for invalidation)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        session_token TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Helper function to get user by username
def get_user(username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

# Helper function to create a new session token and invalidate the old ones
def create_session(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Invalidate any previous sessions for this user
    cursor.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
    
    # Create a new session token
    new_session_token = os.urandom(24).hex()
    cursor.execute("INSERT INTO sessions (user_id, session_token) VALUES (?, ?)", (user_id, new_session_token))
    conn.commit()
    conn.close()

    return new_session_token

# Route to display login page
@app.route('/')
def login():
    return render_template('login.html')

# Route to handle login form submission
@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form['password']
    
    # Authenticate the user
    user = get_user(username)
    if user and user[2] == password:  # Assuming password is in column 2
        session.permanent = True
        session['user_id'] = user[0]
        
        # Create a new session token and invalidate old sessions
        session_token = create_session(user[0])
        
        # Set the session cookie (domain limited, not accessible for subdomains)
        resp = make_response(redirect(url_for('dashboard')))
        resp.set_cookie('session_token', session_token, httponly=True, secure=True, samesite='Lax', domain='your-domain.com')
        
        return resp
    else:
        return "Invalid credentials, please try again."

# Route to display user dashboard (requires authentication)
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']
        session_token = request.cookies.get('session_token')
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE user_id=? AND session_token=?", (user_id, session_token))
        valid_session = cursor.fetchone()
        conn.close()
        
        if valid_session:
            return f"Welcome to your dashboard, User {user_id}!"
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

# Route to handle logout (invalidate session)
@app.route('/logout')
def logout():
    if 'user_id' in session:
        user_id = session['user_id']
        
        # Invalidate session in the database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
    
    session.clear()  # Clear session data
    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie('session_token', domain='your-domain.com')  # Remove cookie
    return resp

if __name__ == '__main__':
    init_db()  # Initialize the database when the app starts
    app.run(debug=True)
``
