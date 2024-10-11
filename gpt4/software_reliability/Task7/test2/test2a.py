from flask import Flask, request, redirect, url_for, make_response, render_template, session
import sqlite3
import os
import hashlib
import time

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required to use sessions
SESSION_DURATION = 300  # Session valid for 5 minutes (300 seconds)

# Database setup
def init_db():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    # Create table for users if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )''')
    conn.commit()
    conn.close()

# Dummy function to add test user
def add_test_user():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    username = "testuser"
    password = hashlib.sha256("password".encode()).hexdigest()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    except sqlite3.IntegrityError:
        pass  # User already exists
    conn.commit()
    conn.close()

# Check user credentials from the database
def check_user(username, password):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

# Invalidate previous session
def invalidate_previous_sessions():
    session.clear()

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        user = check_user(username, password)
        
        if user:
            # Invalidate any previous sessions
            invalidate_previous_sessions()
            
            # Create new session and cookie
            session['username'] = username
            session['session_id'] = hashlib.sha256((username + str(time.time())).encode()).hexdigest()
            resp = make_response(redirect(url_for('dashboard')))
            
            # Set the cookie for the session, valid for this domain only (no subdomains)
            resp.set_cookie('session_id', session['session_id'], max_age=SESSION_DURATION, httponly=True, samesite='Strict')
            return resp
        else:
            return "Invalid credentials"
    return render_template('login.html')

# Route for dashboard (protected route)
@app.route('/dashboard')
def dashboard():
    session_id = request.cookies.get('session_id')
    
    # Validate session and cookie
    if 'session_id' in session and session_id == session.get('session_id'):
        return f"Welcome to the dashboard, {session.get('username')}!"
    else:
        return redirect(url_for('login'))

# Route for logout (invalidate session)
@app.route('/logout')
def logout():
    invalidate_previous_sessions()
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('session_id', '', expires=0)  # Clear the session cookie
    return resp

# Initialize database and create test user
if __name__ == '__main__':
    if not os.path.exists('user_data.db'):
        init_db()
    add_test_user()
    app.run(debug=True)
