import sqlite3
import os
from flask import Flask, request, render_template, redirect, url_for, session
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)  # For session management

DATABASE = 'newsletter.db'

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
        with app.open_resource('schema2.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_user_by_id(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()

def get_subscription_by_user_id(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM newsletter_subscriptions WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def create_unsubscribe_token(user_id):
    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(hours=24)  # Token valid for 24 hours
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO unsubscribe_tokens (user_id, token, expiry) VALUES (?, ?, ?)", (user_id, token, expiry))
    db.commit()
    return token

def get_user_id_from_token(token):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM unsubscribe_tokens WHERE token = ? AND expiry > ?", (token, datetime.utcnow()))
    result = cursor.fetchone()
    if result:
        return result['user_id']
    return None

def invalidate_token(token):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM unsubscribe_tokens WHERE token = ?", (token,))
    db.commit()

def update_subscription_status(user_id, unsubscribed, unsubscribe_reason=None):
    db = get_db()
    cursor = db.cursor()
    subscription = get_subscription_by_user_id(user_id)
    if subscription:
        cursor.execute("UPDATE newsletter_subscriptions SET is_subscribed = ?, unsubscribe_reason = ? WHERE user_id = ?", (unsubscribed, unsubscribe_reason, user_id))
    else:
        cursor.execute("INSERT INTO newsletter_subscriptions (user_id, is_subscribed, unsubscribe_reason) VALUES (?, ?, ?)", (user_id, unsubscribed, unsubscribe_reason))
    db.commit()

# Example login route (for demonstration purposes)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        user = get_user_by_id(user_id)
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            return "Invalid user ID"
    return render_template('login2.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
        return f"Logged in as user: {user['email']} (ID: {user['id']})"
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Route to handle the unsubscribe link from the email
@app.route('/unsubscribe/<token>')
def unsubscribe(token):
    user_id = get_user_id_from_token(token)
    if user_id:
        user = get_user_by_id(user_id)
        if user and 'user_id' in session and session['user_id'] == user_id:
            return render_template('unsubscribe_reason2.html', token=token)
        elif user:
            return "You need to be logged in as this user to unsubscribe."
        else:
            return "Invalid unsubscribe link."
    else:
        return "Invalid or expired unsubscribe link."

# Route to process the unsubscribe reason
@app.route('/unsubscribe_process', methods=['POST'])
def unsubscribe_process():
    if 'user_id' not in session:
        return "You are not logged in."

    token = request.form.get('token')
    unsubscribe_reason = request.form.get('unsubscribe_reason')
    user_id = session['user_id']

    # Verify the token again to prevent direct form submission without clicking the link
    token_user_id = get_user_id_from_token(token)
    if token_user_id != user_id:
        return "Invalid unsubscribe request."

    update_subscription_status(user_id, False, unsubscribe_reason)
    invalidate_token(token)
    return render_template('unsubscribed2.html')

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    from flask import g
    app.run(debug=True)