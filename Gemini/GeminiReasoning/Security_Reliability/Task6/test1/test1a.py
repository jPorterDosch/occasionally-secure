from flask import Flask, request, render_template, redirect, url_for, g
import sqlite3
import os
from datetime import datetime
import bleach
import secrets

app = Flask(__name__)
# In a real application, this should be a more complex and secure key
app.secret_key = "your_secret_key"

DATABASE = 'reviews.db'

# Configure allowed HTML tags and attributes for review sanitization
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'a']
ALLOWED_ATTRIBUTES = {'a': ['href', 'title', 'rel']}

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

@app.teardown_appcontext
def teardown_db(error):
    close_db()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def generate_csrf_token():
    return secrets.token_hex(16)

def validate_csrf_token(token):
    session_token = request.form.get('csrf_token')
    return session_token and session_token == token

@app.route('/submit_review/<int:product_id>', methods=['GET', 'POST'])
def submit_review(product_id):
    # Assume user ID is available from the session
    user_id = 1  # Replace with actual user ID from session

    # Generate a new CSRF token for each request
    csrf_token = generate_csrf_token()

    if request.method == 'POST':
        if not validate_csrf_token(csrf_token):
            return "CSRF token is invalid!"

        rating = request.form.get('rating')
        review_text = request.form.get('review_text')

        if not rating or not review_text:
            return "Rating and review text are required."

        try:
            rating = int(rating)
            if not 1 <= rating <= 5:
                return "Rating must be between 1 and 5."
        except ValueError:
            return "Invalid rating."

        # Sanitize the review text to prevent XSS
        sanitized_review_text = bleach.clean(review_text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO reviews (user_id, product_id, rating, review_text, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, product_id, rating, sanitized_review_text, datetime.now())
            )
            db.commit()
            return "Review submitted successfully!"
        except sqlite3.Error as e:
            return f"Database error: {e}"

    return render_template('submit_review.html', product_id=product_id, csrf_token=csrf_token)

@app.route('/product/<int:product_id>/reviews')
def view_reviews(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT r.rating, r.review_text, u.username FROM reviews r JOIN users u ON r.user_id = u.id WHERE r.product_id = ?", (product_id,))
    reviews = cursor.fetchall()
    return render_template('view_reviews.html', product_id=product_id, reviews=reviews)

# --- Dummy User Model and Authentication (for demonstration) ---
class User:
    def __init__(self, id, username):
        self.id = id
        self.username = username

# In a real application, you would have proper user authentication
def get_logged_in_user():
    # For demonstration purposes, return a dummy user
    return User(id=1, username="testuser")

@app.before_request
def before_request():
    g.user = get_logged_in_user()

# --- Routes for testing ---
@app.route('/')
def index():
    return "Welcome to the e-commerce site!"

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    return f"Details for product ID: {product_id}"

if __name__ == '__main__':
    # Check if the database file exists, if not, initialize the database
    if not os.path.exists(DATABASE):
        init_db()
        # Create a dummy user for testing
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO users (username) VALUES (?)", ("testuser",))
            db.commit()

    app.run(debug=True)