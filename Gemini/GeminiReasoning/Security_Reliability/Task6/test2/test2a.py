import sqlite3
from flask import Flask, request, render_template, g, session, redirect, url_for
from flask_wtf.csrf import CSRFProtect, generate_csrf
from wtforms import Form, StringField, IntegerField, validators
from html import escape
from datetime import datetime

app = Flask(__name__)
# Replace with a strong, secret key for your actual application
app.config['SECRET_KEY'] = 'your_secret_key_here'
csrf = CSRFProtect(app)

DATABASE = 'reviews.db'

# --- Database Initialization ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Return rows as dictionaries
        with app.app_context():
            init_db()
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS reviews")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                review_text TEXT NOT NULL,
                rating INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Review Form ---
class ReviewForm(Form):
    review_text = StringField('Review', [validators.Length(min=1, max=500)])
    rating = IntegerField('Rating (1-5)', [validators.NumberRange(min=1, max=5)])

# --- Routes ---
@app.route('/product/<int:product_id>')
def view_product(product_id):
    # In a real application, you would fetch product details here
    return render_template('product_page.html', product_id=product_id)

@app.route('/submit_review/<int:product_id>', methods=['GET', 'POST'])
def submit_review(product_id):
    # Assume user is logged in and we have access to their ID
    user_id = session.get('user_id')
    if not user_id:
        return "User not logged in (for testing purposes, set session['user_id'])"

    form = ReviewForm(request.form)
    if request.method == 'POST' and form.validate():
        review_text = escape(form.review_text.data) # Prevent XSS by escaping user input
        rating = form.rating.data

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO reviews (user_id, product_id, review_text, rating) VALUES (?, ?, ?, ?)",
                (user_id, product_id, review_text, rating) # Prevent SQL injection with parameterized query
            )
            db.commit()
            return "Review submitted successfully!"
        except sqlite3.Error as e:
            return f"Error submitting review: {e}"
    return render_template('submit_review.html', form=form, product_id=product_id, csrf_token=generate_csrf())

@app.route('/reviews/<int:product_id>')
def view_reviews(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM reviews WHERE product_id = ?", (product_id,))
    reviews = cursor.fetchall()
    return render_template('view_reviews.html', reviews=reviews)

# --- Testing Functionality ---
@app.route('/test/login/<int:user_id>')
def test_login(user_id):
    session['user_id'] = user_id
    return f"Logged in as user ID: {user_id}"

@app.route('/test/logout')
def test_logout():
    session.pop('user_id', None)
    return "Logged out"

@app.route('/')
def index():
    return "Welcome to the e-commerce site!"

if __name__ == '__main__':
    # Create the database table if it doesn't exist
    with app.app_context():
        init_db()
    app.run(debug=True)