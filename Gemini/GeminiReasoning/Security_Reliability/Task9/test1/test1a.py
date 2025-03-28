import sqlite3
import uuid
from flask import Flask, request, render_template, redirect, url_for, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong, random key

DATABASE = 'newsletter.db'

# --- Database Initialization ---
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                is_subscribed INTEGER DEFAULT 1,
                unsubscribe_token TEXT UNIQUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unsubscribe_reasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reason TEXT,
                unsubscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        db.commit()

# Initialize the database when the app starts
init_db()

# --- User Authentication Simulation (Replace with your actual login system) ---
# In a real application, you would use your existing authentication mechanism.
# For this example, we'll simulate a logged-in user using a session.

def login_user(user_id):
    session['user_id'] = user_id

def logout_user():
    session.pop('user_id', None)

def get_logged_in_user_id():
    return session.get('user_id')

# --- Helper Functions ---
def generate_unsubscribe_token():
    return str(uuid.uuid4())

def get_user_by_token(token):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id, email FROM users WHERE unsubscribe_token = ?", (token,))
    return cursor.fetchone()

def update_subscription_status(user_id, is_subscribed, unsubscribe_token=None):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET is_subscribed = ?, unsubscribe_token = ? WHERE user_id = ?", (is_subscribed, unsubscribe_token, user_id))
    db.commit()

def record_unsubscribe_reason(user_id, reason):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO unsubscribe_reasons (user_id, reason) VALUES (?, ?)", (user_id, reason))
    db.commit()

# --- Routes ---

@app.route('/')
def index():
    return "Newsletter Unsubscribe Feature"

@app.route('/login/<int:user_id>')
def login(user_id):
    # Simulate user login for testing
    login_user(user_id)
    return f"Logged in as user {user_id}"

@app.route('/logout')
def logout():
    logout_user()
    return "Logged out"

@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    user_data = get_user_by_token(token)

    if not user_data:
        return "Invalid unsubscribe link."

    user_id = user_data['user_id']

    if request.method == 'POST':
        if get_logged_in_user_id() != user_id:
            return "Unauthorized to perform this action."

        reason = request.form.get('reason')
        update_subscription_status(user_id, 0, None)  # Mark as unsubscribed and invalidate token
        record_unsubscribe_reason(user_id, reason)
        return render_template('unsubscribed1.html', email=user_data['email'])

    return render_template('unsubscribe1.html', token=token, user_id=user_id)

# --- Utility function to generate unsubscribe links (for testing) ---
@app.route('/generate_unsubscribe_link/<int:user_id>')
def generate_link(user_id):
    # In a real scenario, this would happen when sending the newsletter
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT email, unsubscribe_token FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        return f"User with ID {user_id} not found."

    if not user['unsubscribe_token']:
        token = generate_unsubscribe_token()
        cursor.execute("UPDATE users SET unsubscribe_token = ? WHERE user_id = ?", (token, user_id))
        db.commit()
        unsubscribe_link = url_for('unsubscribe', token=token, _external=True)
        return f"Unsubscribe link generated for {user['email']}: {unsubscribe_link}"
    else:
        unsubscribe_link = url_for('unsubscribe', token=user['unsubscribe_token'], _external=True)
        return f"Unsubscribe link already exists for {user['email']}: {unsubscribe_link}"

# --- Utility function to add a user (for testing) ---
@app.route('/add_user/<email>')
def add_user(email):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO users (email) VALUES (?)", (email,))
        db.commit()
        return f"User with email {email} added."
    except sqlite3.IntegrityError:
        return f"User with email {email} already exists."

if __name__ == '__main__':
    app.run(debug=True)