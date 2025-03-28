import sqlite3
from flask import Flask, request, make_response, redirect, url_for, session
from uuid import uuid4
from datetime import timedelta

app = Flask(__name__)
# For security reasons, always use a strong, randomly generated secret key in a real application
app.secret_key = 'your_secret_key_here'
app.permanent_session_lifetime = timedelta(days=1)  # Example session duration

DATABASE = 'users.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def close_db():
    if hasattr(get_db(), 'connection'):
        get_db().connection.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

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

# Create the database schema if it doesn't exist
with app.app_context():
    db = get_db()
    db.execute("DROP TABLE IF EXISTS users")
    db.execute("DROP TABLE IF EXISTS sessions")
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL -- In a real app, store hashed passwords
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    db.commit()

# --- User Management (Simplified for Testing) ---
def create_user(username, password):
    try:
        execute_db("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        return True
    except sqlite3.IntegrityError:
        return False

def get_user_by_username(username):
    return query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)

def verify_password(user, password):
    # In a real application, you would compare against a hashed password
    return user and user['password'] == password

# --- Session Management ---
def create_session(user_id):
    session_id = str(uuid4())
    execute_db("INSERT INTO sessions (session_id, user_id) VALUES (?, ?)", (session_id, user_id))
    return session_id

def get_user_from_session(session_id):
    session_data = query_db("SELECT s.user_id, u.username FROM sessions s JOIN users u ON s.user_id = u.id WHERE s.session_id = ?", (session_id,), one=True)
    return session_data

def delete_session(session_id):
    execute_db("DELETE FROM sessions WHERE session_id = ?", (session_id,))

# --- Authentication Decorator ---
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get('session_id')
        user = None
        if session_id:
            session_data = get_user_from_session(session_id)
            if session_data:
                user = {'id': session_data['user_id'], 'username': session_data['username']}
        if not user:
            return redirect(url_for('login'))
        session['user'] = user
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route('/')
@login_required
def index():
    return f"Hello, {session['user']['username']}! You are logged in."

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and verify_password(user, password):
            session_id = create_session(user['id'])
            response = make_response(redirect(url_for('index')))
            # Set the cookie for the current domain only
            response.set_cookie('session_id', session_id, httponly=True, samesite='Strict')
            return response
        else:
            return "Login failed. Incorrect username or password."
    return """
        <form method="post">
            <p><input type=text name=username placeholder="Username">
            <p><input type=password name=password placeholder="Password">
            <p><input type=submit value=Login>
        </form>
    """

@app.route('/logout')
@login_required
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        delete_session(session_id)
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('session_id', domain=request.host) # Explicitly set domain for removal
    return response

# --- Testing Functionality ---
@app.route('/create_test_user')
def create_test_user_route():
    if create_user('testuser', 'password'):
        return "Test user created successfully."
    else:
        return "Test user already exists."

if __name__ == '__main__':
    # You can initialize the database here if needed, but the table creation
    # is already handled within the app context.
    # init_db() # Uncomment this if you want to re-initialize the DB on each run
    app.run(debug=True, host='0.0.0.0', port=5000)