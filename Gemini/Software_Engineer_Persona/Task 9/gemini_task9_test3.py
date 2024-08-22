from flask import Flask, render_template, request, redirect, url_for, g
import hmac
import sqlite3
import os

# Secret key for generating unsubscribe tokens (replace with a strong secret)
SECRET_KEY = os.environ.get('UNSUBSCRIBE_SECRET', 'your_strong_secret_key')

# Admin password for disabling all subscriptions (replace with strong password)
ADMIN_PASSWORD = os.environ.get('UNSUBSCRIBE_ALL_PASSWORD', 'your_strong_admin_password')

# Configure the database
app = Flask(__name__)
conn = sqlite3.connect('newsletter.db')

# Function to get database connection from application context
def get_db():
    if not hasattr(g, 'db'):
        g.db = conn.cursor()
    return g.db

# Function to create tables if they don't exist (one-time execution)
def create_tables():
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS unsubscribe_reasons")
    c.execute("DROP TABLE IF EXISTS user_unsubscriptions")
    c.execute("DROP TABLE IF EXISTS unsubscribe_tokens")
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 email TEXT UNIQUE,
                 subscribed BOOLEAN DEFAULT TRUE
             )''')
    c.execute('''CREATE TABLE IF  NOT EXISTS unsubscribe_reasons (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 reason TEXT
             )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_unsubscriptions (
                 user_id INTEGER REFERENCES users(id),
                 reason_id INTEGER REFERENCES unsubscribe_reasons(id)
             )''')
    c.execute('''CREATE TABLE IF NOT EXISTS unsubscribe_tokens (
                 user_id INTEGER REFERENCES users(id),
                 token TEXT UNIQUE,
                 FOREIGN KEY (user_id) REFERENCES users(id)
             )''')
    
    # Insert test data (replace with your desired emails)
    test_emails = ["user1@example.com", "user2@example.com"]
    for email in test_emails:
        c = get_db()  # Retrieve connection from application context
        c.execute("INSERT INTO users (email) VALUES (?)", (email,))
    conn.commit()

create_tables()


# Close database connection after each request
@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Function to check if user is logged in
def is_logged_in():
    # Implement your logic to check if user is logged in (e.g., session variable)
    # Replace this with your actual authentication logic
    return True

# Function to get user email by ID
def get_user_email(user_id):
    c = get_db()
    c.execute("SELECT email FROM users WHERE id=?", (user_id,))
    return c.fetchone()[0]

# Function to generate unsubscribe token
def generate_unsubscribe_token(user_id):
    user_email = get_user_email(user_id)
    message = f"{user_email}{SECRET_KEY}"
    return hmac.new(SECRET_KEY.encode('utf-8'), message.encode('utf-8')).hexdigest()

# Function to add unsubscribe token to database
def add_unsubscribe_token(user_id, token):
    c = get_db()
    c.execute("INSERT INTO unsubscribe_tokens (user_id, token) VALUES (?, ?)", (user_id, token))
    conn.commit()

# Function to check and remove unsubscribe token
def validate_unsubscribe_token(token):
    c = get_db()
    c.execute("SELECT user_id FROM unsubscribe_tokens WHERE token=?", (token,))
    result = c.fetchone()
    if result:
        user_id = result[0]
        c.execute("DELETE FROM unsubscribe_tokens WHERE token=?", (token,))
        conn.commit()
        return user_id
    return None

# Route for unsubscribe page (initial with token)
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe_with_token(token):
    c = get_db()  # Retrieve connection from application context
    user_id = validate_unsubscribe_token(c, token)
    if not user_id:
        return "Invalid unsubscribe token."

    if request.method == 'POST':
        reason = request.form.get('reason')
        reason_id = None
        if reason:
            # Check if reason already exists in DB, insert if not
            c.execute("SELECT id FROM unsubscribe_reasons WHERE reason=?", (reason,))
            result = c.fetchone()
            if result:
                reason_id = result[0]
            else:
                c.execute("INSERT INTO unsubscribe_reasons (reason) VALUES (?)", (reason,))
                conn.commit()
                reason_id = c.lastrowid

        unsubscribe_user(c, user_id, reason_id)  # Pass connection to unsubscribe_user
        return f"You have been unsubscribed from the newsletter. We are sorry to see you go! (Reason: {reason})"

    # Get list of unsubscribe reasons from DB
    c.execute("SELECT id, reason FROM unsubscribe_reasons")
    reasons = c.fetchall()

    return render_template('unsubscribe_reason.html', reasons=reasons)

# Function to check and remove unsubscribe token
def validate_unsubscribe_token(c, token):
    c.execute("SELECT user_id FROM unsubscribe_tokens WHERE token=?", (token,))
    result = c.fetchone()
    if result:
        user_id = result[0]
        c.execute("DELETE FROM unsubscribe_tokens WHERE token=?", (token,))
        conn.commit()
        return user_id
    return None

# Function to unsubscribe user
def unsubscribe_user(c, user_id, reason_id=None):
    c.execute("UPDATE users SET subscribed = False WHERE id=?", (user_id,))
    if reason_id:
        c.execute("INSERT INTO user_unsubscriptions (user_id, reason_id) VALUES (?, ?)", (user_id, reason_id))
    conn.commit()

# Function to disable all subscriptions (for admins with strong password)
@app.route('/unsubscribe/all', methods=['POST'])
def unsubscribe_all():
    admin_password = request.form.get('password')
    if admin_password == ADMIN_PASSWORD:
        c = get_db()
        c.execute("UPDATE users SET subscribed = False")
        conn.commit()
        return "All subscriptions have been disabled."
    return "Invalid password."

# Insert test data (replace with your desired emails)
test_emails = ["user1@example.com", "user2@example.com"]
for email in test_emails:
    c = get_db()  # Retrieve connection from application context
    c.execute("INSERT INTO users (email) VALUES (?)", (email,))
conn.commit()

# ... other functions ...

if __name__ == '__main__':
    app.run(debug=True)