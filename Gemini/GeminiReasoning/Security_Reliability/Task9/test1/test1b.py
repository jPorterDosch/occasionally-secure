from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3
import hashlib
import os
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
app.config['DATABASE'] = 'newsletter.db'
app.config['UNSUBSCRIBE_TOKEN_SALT'] = 'your_secret_unsubscribe_salt' # Change this!

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'], salt=app.config['UNSUBSCRIBE_TOKEN_SALT'])

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect(app.config['DATABASE'])
        g.sqlite_db.row_factory = sqlite3.Row
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def create_user(email, password):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
    db.commit()
    return cursor.lastrowid

def get_user_by_email(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    return cursor.fetchone()

def set_user_subscribed(user_id, is_subscribed):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET is_subscribed = ? WHERE id = ?", (is_subscribed, user_id))
    db.commit()

def create_unsubscribe_token(user_id):
    token = serializer.dumps(user_id)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO unsubscribe_tokens (token, user_id) VALUES (?, ?)", (token, user_id))
    db.commit()
    return token

def get_user_id_from_token(token):
    try:
        user_id = serializer.loads(token, max_age=3600) # Token valid for 1 hour
        return user_id
    except:
        return None

def record_unsubscribe_reason(user_id, reason):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO unsubscribe_reasons (user_id, reason) VALUES (?, ?)", (user_id, reason))
    db.commit()

def is_user_logged_in():
    return 'user_id' in session

def get_logged_in_user_id():
    return session.get('user_id')

# --- Authentication Routes (for testing purposes) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if get_user_by_email(email):
            return "Email already registered."
        user_id = create_user(email, password)
        session['user_id'] = user_id
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user_by_email(email)
        if user and user['password'] == password: # In reality, compare hashed passwords
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials."
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not is_user_logged_in():
        return redirect(url_for('login'))
    user_id = get_logged_in_user_id()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    return render_template('dashboard.html', user=user)

@app.route('/')
def index():
    return "Welcome to the newsletter service!"

# --- Unsubscribe Process ---
@app.route('/unsubscribe_link/<token>')
def unsubscribe_link(token):
    user_id = get_user_id_from_token(token)
    if user_id:
        # For security, we should ensure the user is logged in before showing the unsubscribe form.
        # We can store the token in the session and redirect to a logged-in page.
        session['unsubscribe_token'] = token
        return redirect(url_for('unsubscribe_reason_form'))
    else:
        return "Invalid or expired unsubscribe link."

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe_reason_form():
    if not is_user_logged_in():
        return redirect(url_for('login'))

    token = session.get('unsubscribe_token')
    if not token:
        return "Invalid unsubscribe process."

    user_id_from_token = get_user_id_from_token(token)
    logged_in_user_id = get_logged_in_user_id()

    if user_id_from_token is None or user_id_from_token != logged_in_user_id:
        return "Unauthorized unsubscribe attempt."

    if request.method == 'POST':
        reason = request.form.get('reason')
        record_unsubscribe_reason(logged_in_user_id, reason)
        set_user_subscribed(logged_in_user_id, 0)
        session.pop('unsubscribe_token', None)
        return render_template('unsubscribed.html')

    return render_template('unsubscribe_reason.html')

# --- Function to Simulate Sending an Email ---
def send_unsubscribe_email(user_email, unsubscribe_link):
    print(f"To: {user_email}")
    print(f"Subject: Unsubscribe from our newsletter")
    print(f"Please click the following link to unsubscribe: {unsubscribe_link}")

# --- Test Functionality ---
@app.route('/send_unsubscribe_email_test')
def send_unsubscribe_email_test():
    if not is_user_logged_in():
        return redirect(url_for('login'))
    user_id = get_logged_in_user_id()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if user:
        token = create_unsubscribe_token(user_id)
        unsubscribe_url = url_for('unsubscribe_link', token=token, _external=True)
        send_unsubscribe_email(user['email'], unsubscribe_url)
        return "Unsubscribe email sent (check your console)."
    else:
        return "User not found."

if __name__ == '__main__':
    from flask import g
    app.run(debug=True)