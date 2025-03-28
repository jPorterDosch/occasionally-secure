import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, make_response, redirect, url_for, abort

# Configuration
DATABASE = 'ecommerce.db'
SECRET_KEY = 'your_secret_key'  # Replace with a strong, random key
SESSION_DURATION = timedelta(hours=1)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

def get_db():
    """Connects to the application's SQLite database."""
    db = getattr(app, '_database', None)
    if db is None:
        db = app._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database again at the end of the request."""
    db = getattr(app, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database schema."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS sessions")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL -- In a real application, store hashed passwords
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expiry_timestamp DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        # Create a default user for testing
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'testuser'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('testuser', 'password123'))
        db.commit()

def generate_session_token():
    """Generates a unique session token."""
    return str(uuid.uuid4())

def set_session_cookie(response, session_token):
    """Sets the session cookie in the response."""
    response.set_cookie(
        'session_token',
        session_token,
        httponly=True,
        secure=False,  # Set to True in production over HTTPS
        samesite='Strict' # Recommended for security
    )

def clear_session_cookie(response):
    """Clears the session cookie."""
    response.delete_cookie('session_token')

def create_session(user_id):
    """Creates a new session in the database."""
    session_token = generate_session_token()
    expiry_timestamp = datetime.utcnow() + SESSION_DURATION
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO sessions (session_token, user_id, expiry_timestamp) VALUES (?, ?, ?)",
            (session_token, user_id, expiry_timestamp)
        )
        db.commit()
        return session_token
    except sqlite3.IntegrityError:
        return None

def get_user_from_session(session_token):
    """Validates the session token and returns the associated user ID if valid."""
    if not session_token:
        return None

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT user_id, expiry_timestamp FROM sessions WHERE session_token = ?",
        (session_token,)
    )
    session_data = cursor.fetchone()

    if session_data:
        expiry_timestamp = datetime.fromisoformat(session_data['expiry_timestamp'])
        if expiry_timestamp > datetime.utcnow():
            return session_data['user_id']
        else:
            # Session expired, remove it
            cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
            db.commit()
    return None

def login_required(view):
    """Decorator to protect routes that require authentication."""
    def wrapped_view(**kwargs):
        session_token = request.cookies.get('session_token')
        user_id = get_user_from_session(session_token)
        if user_id is None:
            return redirect(url_for('login'))
        request.user_id = user_id  # Make user ID available to the route
        return view(**kwargs)
    wrapped_view.__name__ = view.__name__
    return wrapped_view

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        if user:
            session_token = create_session(user['id'])
            if session_token:
                response = redirect(url_for('dashboard'))
                set_session_cookie(response, session_token)
                return response
            else:
                return "Error creating session.", 500
        else:
            return "Invalid username or password.", 401
    return '''
        <h2>Login</h2>
        <form method="post">
            <p><input type=text name=username placeholder="Username"></p>
            <p><input type=password name=password placeholder="Password"></p>
            <p><input type=submit value=Login></p>
        </form>
    '''

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (request.user_id,))
    user = cursor.fetchone()
    return f"<h1>Dashboard</h1><p>Welcome, {user['username']}!</p><p><a href='{url_for('logout')}'>Logout</a></p>"

@app.route('/logout')
@login_required
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
        db.commit()
    response = redirect(url_for('login'))
    clear_session_cookie(response)
    return response

@app.route('/public')
def public_page():
    return "This is a public page."

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)