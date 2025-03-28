from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import html

app = Flask(__name__)
DATABASE = 'reviews.db'

# Function to get a database connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
    return conn

# Function to initialize the database and create the reviews table if it doesn't exist
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS reviews")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                review_text TEXT NOT NULL,
                rating INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

# Initialize the database when the application starts
init_db()

# --- Security Measures ---

# Function to sanitize user input to prevent basic XSS
def sanitize_input(text):
    return html.escape(text)

# --- Routes ---

@app.route('/submit_review', methods=['POST'])
def submit_review():
    try:
        # Assuming user_id and product_id are passed in the request (in a real scenario, user_id would come from the session)
        user_id = request.form.get('user_id')
        product_id = request.form.get('product_id')
        review_text = request.form.get('review_text')
        rating = request.form.get('rating')

        # Validate input
        if not user_id or not product_id or not review_text or not rating:
            return jsonify({'error': 'Missing required fields'}), 400

        try:
            user_id = int(user_id)
            product_id = int(product_id)
            rating = int(rating)
        except ValueError:
            return jsonify({'error': 'Invalid user ID, product ID, or rating format'}), 400

        if not 1 <= rating <= 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400

        # Sanitize review text to prevent basic XSS
        sanitized_review_text = sanitize_input(review_text)

        # Get database connection
        db = get_db()
        cursor = db.cursor()

        # Use parameterized query to prevent SQL injection
        cursor.execute('''
            INSERT INTO reviews (user_id, product_id, review_text, rating)
            VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, sanitized_review_text, rating))

        db.commit()
        db.close()

        return jsonify({'message': 'Review submitted successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Testing Functionality ---

@app.route('/')
def index():
    return '''
        <h1>Submit a Product Review</h1>
        <form action="/submit_review" method="post">
            <label for="user_id">User ID:</label><br>
            <input type="number" id="user_id" name="user_id" required><br><br>
            <label for="product_id">Product ID:</label><br>
            <input type="number" id="product_id" name="product_id" required><br><br>
            <label for="review_text">Review Text:</label><br>
            <textarea id="review_text" name="review_text" rows="4" cols="50" required></textarea><br><br>
            <label for="rating">Rating (1-5):</label><br>
            <select id="rating" name="rating" required>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4</option>
                <option value="5">5</option>
            </select><br><br>
            <input type="submit" value="Submit Review">
        </form>
    '''

@app.route('/reviews')
def view_reviews():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM reviews")
    reviews = cursor.fetchall()
    db.close()

    if not reviews:
        return "<p>No reviews yet.</p>"

    html_output = "<h1>Product Reviews</h1><ul>"
    for review in reviews:
        html_output += f"<li><strong>User ID:</strong> {review['user_id']}, <strong>Product ID:</strong> {review['product_id']}, <strong>Rating:</strong> {review['rating']}/5<br>"
        html_output += f"<strong>Review:</strong> {review['review_text']}<br>"
        html_output += f"<strong>Created At:</strong> {review['created_at']}</li>"
    html_output += "</ul>"
    return html_output

if __name__ == '__main__':
    app.run(debug=True)