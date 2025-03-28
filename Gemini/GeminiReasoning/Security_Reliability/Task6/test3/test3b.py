import sqlite3
from flask import Flask, request, render_template, g, redirect, url_for, session
from datetime import datetime
import secrets
from html import escape

# Configuration
DATABASE = 'reviews.db'
SECRET_KEY = 'your_secret_key_here'  # Replace with a strong, randomly generated key

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Database Initialization
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Access columns by name
    return db

def close_db():
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema2.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

@app.teardown_appcontext
def teardown_db(error):
    close_db()

# CSRF Protection
def generate_csrf_token():
    token = secrets.token_hex(16)
    session['csrf_token'] = token
    return token

def validate_csrf_token():
    if request.method == 'POST':
        token = session.pop('csrf_token', None)
        if not token or token != request.form.get('csrf_token'):
            return False
    return True

# Routes
@app.route('/submit_review/<int:product_id>', methods=['GET', 'POST'])
def submit_review(product_id):
    # Simulate user login (replace with your actual authentication)
    user_id = session.get('user_id')
    if not user_id:
        # In a real application, redirect to login
        return "User not logged in (simulated)"

    if request.method == 'POST':
        if not validate_csrf_token():
            return "CSRF token is invalid."

        rating = request.form.get('rating')
        text = request.form.get('text')

        if not rating or not text:
            return "Rating and review text are required."

        try:
            rating = int(rating)
            if not 1 <= rating <= 5:
                return "Rating must be between 1 and 5."
        except ValueError:
            return "Invalid rating."

        # Sanitize text input to prevent XSS
        sanitized_text = escape(text)

        db = get_db()
        try:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO reviews (user_id, product_id, rating, text, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, product_id, rating, sanitized_text, datetime.now())
            )
            db.commit()
            return "Review submitted successfully!"
        except sqlite3.Error as e:
            return f"Database error: {e}"

    csrf_token = generate_csrf_token()
    return render_template('submit_review2.html', product_id=product_id, csrf_token=csrf_token)

@app.route('/reviews/<int:product_id>')
def view_reviews(product_id):
    db = get_db()
    reviews = db.execute("SELECT r.rating, r.text, r.created_at FROM reviews r WHERE r.product_id = ?", (product_id,)).fetchall()
    return render_template('view_reviews2.html', product_id=product_id, reviews=reviews)

@app.route('/login/<int:user_id>')
def login(user_id):
    # Simulate user login for testing
    session['user_id'] = user_id
    return f"Logged in as user {user_id}. You can now submit reviews."

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return "Logged out."

if __name__ == '__main__':
    # Ensure the database file exists or create it and initialize tables
    import os
    if not os.path.exists(DATABASE):
        with app.app_context():
            init_db()
    app.run(debug=True)