from flask import Flask, request, render_template, g, session, redirect, url_for
import sqlite3
import os
import secrets
from html import escape

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # For session management and CSRF

DATABASE = 'reviews.db'

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
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

@app.before_request
def before_request():
    g.db = get_db()
    g.user_id = 1  # In a real application, this would come from the session

@app.teardown_appcontext
def teardown_appcontext(error):
    close_db()

def generate_csrf_token():
    token = secrets.token_hex(16)
    session['csrf_token'] = token
    return token

def is_valid_csrf_token(token):
    return 'csrf_token' in session and session['csrf_token'] == token

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_reviews(product_id):
    if request.method == 'POST':
        if not is_valid_csrf_token(request.form.get('csrf_token')):
            return "CSRF token is invalid!", 400

        rating = request.form.get('rating')
        review_text = request.form.get('review_text')

        if not rating or not review_text:
            return "Rating and review text are required.", 400
        try:
            rating = int(rating)
            if not 1 <= rating <= 5:
                return "Rating must be between 1 and 5.", 400
        except ValueError:
            return "Invalid rating format.", 400

        # Sanitize the review text to prevent basic XSS
        sanitized_review_text = escape(review_text)

        try:
            cursor = g.db.cursor()
            cursor.execute(
                "INSERT INTO reviews (user_id, product_id, rating, text, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                (g.user_id, product_id, rating, sanitized_review_text)
            )
            g.db.commit()
            return "Review submitted successfully!"
        except sqlite3.Error as e:
            return f"Database error: {e}", 500

    # For GET request, just render the form (and potentially display existing reviews)
    csrf_token = generate_csrf_token()
    return render_template('product_review_form.html', product_id=product_id, csrf_token=csrf_token)

@app.route('/test_form/<int:product_id>')
def test_form(product_id):
    csrf_token = generate_csrf_token()
    return render_template('product_review_form.html', product_id=product_id, csrf_token=csrf_token)

if __name__ == '__main__':
    # Check if the database file exists, if not, initialize it
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)