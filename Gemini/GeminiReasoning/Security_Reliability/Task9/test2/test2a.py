import os
import sqlite3
from flask import Flask, request, render_template, redirect, url_for, session
from itsdangerous import URLSafeTimedSerializer

# Configuration
DATABASE = 'newsletter_subscriptions.db'
SECRET_KEY = 'your_secret_key'  # Replace with a strong, random key
UNSUBSCRIBE_TOKEN_SALT = 'unsubscribe-salt'
TOKEN_EXPIRATION_TIME = 3600  # 1 hour in seconds

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Initialize the database
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def generate_unsubscribe_token(user_id):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'], salt=UNSUBSCRIBE_TOKEN_SALT)
    return serializer.dumps({'user_id': user_id})

def verify_unsubscribe_token(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'], salt=UNSUBSCRIBE_TOKEN_SALT)
    try:
        data = serializer.loads(token, max_age=TOKEN_EXPIRATION_TIME)
        return data.get('user_id')
    except Exception as e:
        return None

# Dummy function to simulate getting user details from the database
def get_user(user_id):
    db = get_db()
    user = db.execute("SELECT id, email FROM users WHERE id = ?", (user_id,)).fetchone()
    return user

# Dummy function to simulate checking if a user is subscribed
def is_subscribed(user_id):
    db = get_db()
    subscription = db.execute("SELECT is_subscribed FROM newsletter_subscriptions WHERE user_id = ?", (user_id,)).fetchone()
    return subscription and subscription['is_subscribed'] == 1

# Dummy function to simulate updating subscription preferences
def update_subscription(user_id, is_subscribed, unsubscribe_reason=None):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO newsletter_subscriptions (user_id, is_subscribed, unsubscribe_reason) VALUES (?, ?, ?)",
        (user_id, is_subscribed, unsubscribe_reason)
    )
    db.commit()

# --- Routes ---

@app.route('/')
def index():
    # This is just a basic homepage for testing
    return render_template('index.html')

@app.route('/newsletter/unsubscribe/request', methods=['GET'])
def unsubscribe_request():
    # In a real application, this would be triggered when a logged-in user
    # requests to unsubscribe from their account settings.
    # For testing, we'll simulate a logged-in user.
    # Replace this with your actual user session logic.
    session['user_id'] = 1  # Simulate user ID 1 being logged in
    user_id = session.get('user_id')

    if not user_id:
        return "You need to be logged in to unsubscribe."

    user = get_user(user_id)
    if not user:
        return "User not found."

    if not is_subscribed(user_id):
        return "You are not currently subscribed to the newsletter."

    token = generate_unsubscribe_token(user_id)
    unsubscribe_link = url_for('unsubscribe', token=token, _external=True)

    # In a real application, you would send this link to the user's email address.
    print(f"Unsubscribe Link for user {user['email']}: {unsubscribe_link}")

    return render_template('unsubscribe_request.html', email=user['email'], unsubscribe_link=unsubscribe_link)

@app.route('/newsletter/unsubscribe/<token>', methods=['GET'])
def unsubscribe(token):
    user_id = verify_unsubscribe_token(token)
    if user_id is None:
        return "Invalid or expired unsubscribe link."

    user = get_user(user_id)
    if not user:
        return "User not found."

    # For added security, you might want to ensure the user is still logged in
    # before showing the unsubscribe reason form.
    session['unsubscribe_user_id'] = user_id  # Store user ID for the next step
    return render_template('unsubscribe_reason.html', email=user['email'])

@app.route('/newsletter/unsubscribe/submit', methods=['POST'])
def unsubscribe_submit():
    user_id = session.pop('unsubscribe_user_id', None)
    if user_id is None:
        return "Invalid unsubscribe request."

    unsubscribe_reason = request.form.get('reason')
    update_subscription(user_id, False, unsubscribe_reason)

    return render_template('unsubscribe_success.html')

# --- Initialization ---

if __name__ == '__main__':
    # Ensure the database file exists and initialize if not
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)