from flask import Flask, request, redirect, url_for, render_template, session
import sqlite3
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong, random key

DATABASE = 'newsletter_subscriptions.db'

# --- Database Initialization ---
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

# --- User Management (Simplified for demonstration) ---
# In a real application, you would likely have a more robust user authentication system.

def create_user(email, password):
    hashed_password = generate_password_hash(password)
    try:
        execute_db("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
        return True
    except sqlite3.IntegrityError:
        return False  # Email already exists

def get_user_by_email(email):
    return query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)

def verify_password(user, password):
    return check_password_hash(user['password'], password)

def login_user(user):
    session['user_id'] = user['id']

def logout_user():
    session.pop('user_id', None)

def get_logged_in_user():
    user_id = session.get('user_id')
    if user_id:
        return query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
    return None

# --- Unsubscribe Functionality ---

def generate_unsubscribe_token(user_id):
    token = str(uuid.uuid4())
    expiry_time = datetime.now() + timedelta(hours=24)  # Token valid for 24 hours
    execute_db("INSERT INTO unsubscribe_tokens (user_id, token, expiry_time) VALUES (?, ?, ?)",
               (user_id, token, expiry_time))
    return token

def is_valid_unsubscribe_token(token, user_id):
    token_data = query_db("SELECT * FROM unsubscribe_tokens WHERE token = ? AND user_id = ? AND expiry_time > ?",
                          (token, user_id, datetime.now()), one=True)
    return token_data is not None

def invalidate_unsubscribe_token(token):
    execute_db("DELETE FROM unsubscribe_tokens WHERE token = ?", (token,))

def get_user_subscription_status(user_id):
    subscription = query_db("SELECT is_subscribed FROM newsletter_subscriptions WHERE user_id = ?", (user_id,), one=True)
    return subscription['is_subscribed'] if subscription else True # Default to subscribed

def update_subscription_preferences(user_id, is_subscribed, unsubscribe_reason=None):
    existing_subscription = query_db("SELECT * FROM newsletter_subscriptions WHERE user_id = ?", (user_id,), one=True)
    if existing_subscription:
        execute_db("UPDATE newsletter_subscriptions SET is_subscribed = ?, unsubscribe_reason = ? WHERE user_id = ?",
                   (is_subscribed, unsubscribe_reason, user_id))
    else:
        execute_db("INSERT INTO newsletter_subscriptions (user_id, is_subscribed, unsubscribe_reason) VALUES (?, ?, ?)",
                   (user_id, is_subscribed, unsubscribe_reason))

# --- Routes ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if create_user(email, password):
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error='Email already exists')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user_by_email(email)
        if user and verify_password(user, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))
    subscription_status = get_user_subscription_status(user['id'])
    return render_template('dashboard.html', user=user, subscription_status=subscription_status)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/unsubscribe/<token>')
def unsubscribe_page(token):
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))

    if not is_valid_unsubscribe_token(token, user['id']):
        return render_template('message.html', message='Invalid or expired unsubscribe link.')

    return render_template('unsubscribe_reason.html', token=token)

@app.route('/unsubscribe_submit', methods=['POST'])
def unsubscribe_submit():
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))

    token = request.form['token']
    reason = request.form['reason']

    if not is_valid_unsubscribe_token(token, user['id']):
        return render_template('message.html', message='Invalid or expired unsubscribe link.')

    update_subscription_preferences(user['id'], False, reason)
    invalidate_unsubscribe_token(token)
    return render_template('message.html', message='You have successfully unsubscribed from our newsletter.')

# --- Helper function to simulate sending an email ---
def send_unsubscribe_email(user_email, unsubscribe_link):
    print(f"Simulating sending email to: {user_email}")
    print(f"Unsubscribe Link: {unsubscribe_link}")

# --- Example usage (to be run manually or as a test) ---
def test_unsubscribe_flow(user_email="test@example.com", password="password123"):
    with app.test_client() as client:
        # 1. Register a test user
        client.post('/register', data={'email': user_email, 'password': password})

        # 2. Login the test user
        client.post('/login', data={'email': user_email, 'password': password}, follow_redirects=True)
        with client.session_transaction() as sess:
            user_id = sess['user_id']

        # 3. Simulate generating an unsubscribe link (as part of a newsletter email)
        unsubscribe_token = generate_unsubscribe_token(user_id)
        unsubscribe_link = url_for('unsubscribe_page', token=unsubscribe_token, _external=True)
        send_unsubscribe_email(user_email, unsubscribe_link)

        # 4. Simulate the user clicking the link (requires the user to be logged in)
        #    We are already logged in in this test.
        response = client.get(f'/unsubscribe/{unsubscribe_token}', follow_redirects=True)
        assert response.status_code == 200
        assert b"Reason for Unsubscribing" in response.data

        # 5. Simulate the user submitting the unsubscribe reason
        response = client.post('/unsubscribe_submit', data={'token': unsubscribe_token, 'reason': 'Not interested anymore'}, follow_redirects=True)
        assert response.status_code == 200
        assert b"You have successfully unsubscribed" in response.data

        # 6. Verify the user's subscription status in the database
        user_data = get_user_by_email(user_email)
        subscription_status = get_user_subscription_status(user_data['id'])
        assert not subscription_status

        # 7. Try to use the same token again (should be invalid)
        response = client.get(f'/unsubscribe/{unsubscribe_token}', follow_redirects=True)
        assert b"Invalid or expired unsubscribe link." in response.data

        print("Unsubscribe flow test completed successfully!")

if __name__ == '__main__':
    # Create the database and tables if they don't exist
    with app.app_context():
        get_db()

    # Run the test flow
    test_unsubscribe_flow()

    # Run the Flask development server (for manual testing)
    app.run(debug=True)