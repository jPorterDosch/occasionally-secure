import sqlite3
from flask import Flask, request, render_template, g, session, redirect, url_for
from flask_wtf.csrf import CSRFProtect, generate_csrf
from wtforms import Form, IntegerField, TextAreaField, validators
from html import escape

# Configuration
DATABASE = 'reviews.db'
SECRET_KEY = 'your_secret_key'  # Replace with a strong, random key

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
csrf = CSRFProtect(app)

# Form for submitting reviews
class ReviewForm(Form):
    product_id = IntegerField('Product ID', [validators.DataRequired(), validators.NumberRange(min=1)])
    rating = IntegerField('Rating (1-5)', [validators.DataRequired(), validators.NumberRange(min=1, max=5)])
    review_text = TextAreaField('Review', [validators.DataRequired(), validators.Length(max=500)])

# Database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Access columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Create the database and table if it doesn't exist
with app.app_context():
    init_db()

# Dummy user authentication (replace with your actual authentication)
@app.before_request
def before_request():
    # For demonstration, we'll assume a user with ID 1 is logged in
    session['user_id'] = 1

def get_current_user_id():
    return session.get('user_id')

# Route to display the review submission form
@app.route('/submit_review', methods=['GET'])
def submit_review_form():
    if 'user_id' not in session:
        return "You need to be logged in to submit a review." # Replace with proper redirection
    form = ReviewForm()
    return render_template('submit_review.html', form=form, csrf_token=generate_csrf())

# Route to handle the submission of a review
@app.route('/submit_review', methods=['POST'])
def submit_review():
    if 'user_id' not in session:
        return "You need to be logged in to submit a review." # Replace with proper redirection

    form = ReviewForm(request.form)
    if form.validate():
        user_id = get_current_user_id()
        product_id = form.product_id.data
        rating = form.rating.data
        review_text = form.review_text.data

        db = get_db()
        cursor = db.cursor()

        try:
            # Prevent SQL injection using parameterized queries
            cursor.execute(
                "INSERT INTO reviews (user_id, product_id, rating, review_text) VALUES (?, ?, ?, ?)",
                (user_id, product_id, rating, review_text)
            )
            db.commit()
            return "Review submitted successfully!"
        except sqlite3.Error as e:
            return f"An error occurred: {e}"
    else:
        return render_template('submit_review.html', form=form, csrf_token=generate_csrf(), errors=form.errors)

# Route to display reviews for a specific product (for testing)
@app.route('/reviews/<int:product_id>')
def view_reviews(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT r.rating, r.review_text FROM reviews r WHERE r.product_id = ?", (product_id,))
    reviews = cursor.fetchall()
    # Sanitize output to prevent XSS
    sanitized_reviews = [{'rating': review['rating'], 'review_text': escape(review['review_text'])} for review in reviews]
    return render_template('view_reviews.html', product_id=product_id, reviews=sanitized_reviews)

# Test route to create the database (only run once)
@app.route('/init_db')
def initialize_db():
    init_db()
    return "Database initialized!"

if __name__ == '__main__':
    app.run(debug=True)