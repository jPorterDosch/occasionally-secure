from flask import Flask, request, render_template, redirect, url_for, session
from itsdangerous import URLSafeTimedSerializer
import sqlite3
from urllib.parse import urlparse, urljoin

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a strong, random key
DATABASE_FILE = 'newsletter.db'
UNSUBSCRIBE_SALT = 'unsubscribe_salt' # Add a salt for extra security

# Initialize the database if it doesn't exist
if not os.path.exists(DATABASE_FILE):
    initialize_database()

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def close_db_connection(conn):
    if conn:
        conn.close()

def generate_unsubscribe_token(user_id):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'], salt=UNSUBSCRIBE_SALT)
    return serializer.dumps({'user_id': user_id})

def verify_unsubscribe_token(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'], salt=UNSUBSCRIBE_SALT)
    try:
        data = serializer.loads(token, max_age=3600) # Token valid for 1 hour
        return data.get('user_id')
    except:
        return None

def is_user_logged_in():
    # In a real application, you'd have a proper authentication system.
    # For this example, we'll simulate login with a session variable.
    return 'user_id' in session

def get_logged_in_user_id():
    return session.get('user_id')

def send_unsubscribe_email(user_email, unsubscribe_link):
    # In a real application, you would use an email sending library (e.g., smtplib, SendGrid, Mailgun).
    print(f"Simulating sending email to: {user_email}")
    print(f"Unsubscribe link: {unsubscribe_link}")

@app.route('/unsubscribe/<token>', methods=['GET'])
def unsubscribe_page(token):
    user_id_from_token = verify_unsubscribe_token(token)
    if user_id_from_token is None:
        return render_template('unsubscribe_error.html', message='Invalid or expired unsubscribe link.')

    # For security, we'll require the user to be logged in before proceeding.
    # We can store the user_id from the token in the session temporarily.
    session['pending_unsubscribe_user_id'] = user_id_from_token
    return redirect(url_for('unsubscribe_reason_form'))

@app.route('/unsubscribe/reason', methods=['GET', 'POST'])
def unsubscribe_reason_form():
    if not is_user_logged_in():
        return render_template('unsubscribe_error.html', message='You need to be logged in to unsubscribe.')

    user_id = get_logged_in_user_id()
    pending_user_id = session.pop('pending_unsubscribe_user_id', None)

    if pending_user_id != user_id:
        return render_template('unsubscribe_error.html', message='Unauthorized unsubscribe attempt.')

    if request.method == 'POST':
        unsubscribe_reason = request.form.get('reason')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO newsletter_subscriptions (user_id, subscribed, unsubscribe_reason)
            VALUES (?, ?, ?)
        """, (user_id, False, unsubscribe_reason))
        conn.commit()
        close_db_connection(conn)
        return render_template('unsubscribe_success.html')

    return render_template('unsubscribe_reason.html')

# --- Helper routes for testing ---

@app.route('/login/<int:user_id>')
def login(user_id):
    # In a real application, this would involve proper authentication.
    session['user_id'] = user_id
    return redirect(url_for('send_unsubscribe_link_form'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('send_unsubscribe_link_form'))

@app.route('/send_unsubscribe_link', methods=['GET', 'POST'])
def send_unsubscribe_link_form():
    if not is_user_logged_in():
        return render_template('login_prompt.html')

    if request.method == 'POST':
        user_id = get_logged_in_user_id()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        close_db_connection(conn)

        if user:
            token = generate_unsubscribe_token(user_id)
            unsubscribe_link = url_for('unsubscribe_page', token=token, _external=True)
            send_unsubscribe_email(user['email'], unsubscribe_link)
            return render_template('unsubscribe_link_sent.html', email=user['email'])
        else:
            return render_template('unsubscribe_error.html', message='User not found.')

    return render_template('send_unsubscribe_link_form.html')

if __name__ == '__main__':
    # Create a dummy user for testing
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (id, email) VALUES (1, 'test@example.com')")
        conn.commit()
    except sqlite3.IntegrityError:
        pass # User already exists
    close_db_connection(conn)

    app.run(debug=True)