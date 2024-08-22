from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3

app = Flask(__name__)

# Configure the database (replace with your actual filename)
app.config['DATABASE'] = 'your_database.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Define functions to create the tables if they don't exist (schema creation)
def create_tables():
    with get_db() as c:
        c.execute("DROP TABLE IF EXISTS users")
        c.execute("DROP TABLE IF EXISTS products")
        c.execute("DROP TABLE IF EXISTS purchases")

        c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    score INTEGER NOT NULL CHECK (score BETWEEN 1 AND 5),
                    review_text TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                    )''')


# Sample test data (replace with your desired data)
user_data = [('user1',), ('user2',)]
product_data = [('Product A',), ('Product B',)]
purchase_data = [(1, 1), (1, 2), (2, 1)]


def insert_test_data():
    with get_db() as c:
        for user in user_data:
            c.execute("INSERT INTO users (username) VALUES (?)", user)
        for product in product_data:
            c.execute("INSERT INTO products (name) VALUES (?)", product)
        for purchase in purchase_data:
            c.execute("INSERT INTO purchases (user_id, product_id) VALUES (?, ?)", purchase)

app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# Function to get a user's purchases
def get_user_purchases(user_id):
    with get_db() as c:
        c.execute("SELECT p.product_id, pr.name FROM purchases p JOIN products pr ON p.product_id = pr.id WHERE p.user_id = ?", (user_id,))
        return c.fetchall()

@app.route('/review/<int:product_id>/<int:user_id>', methods=['POST'])
def submit_review(product_id, user_id):
    db = get_db()
    c = db.cursor()

    # Check if user has purchased the product before allowing review submission
    purchase_check = c.execute("SELECT * FROM purchases WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    if not purchase_check.fetchone():
        return "You haven't purchased this product yet. Reviews can only be submitted for purchased products.", 400

    score = request.form.get('score')
    review_text = request.form.get('review_text')

    # Validate score and review text
    if not score or not review_text:
        return "Missing required fields. Please provide a score and review text.", 400
    try:
        score = int(score)
        if score not in range(1, 6):
            return "Invalid score. Score must be between 1 and 5.", 400
    except ValueError:
        return "Invalid score. Score must be a number.", 400

    # Insert review into database
    c.execute("INSERT INTO reviews (user_id, product_id, score, review_text) VALUES (?, ?, ?, ?)", (user_id, product_id, score, review_text))
    db.commit()

    # Success message or redirect to a success page
    return "Review submitted successfully!", 201

# Route to display a success message after adding a review
@app.route('/success')
def success():
    return "Your review has been submitted successfully!"

# Route to display the review form (replace with your actual logic to display products)
@app.route('/reviews/<int:user_id>')
def reviews(user_id):
    products = get_user_purchases(user_id)
    return render_template('reviews.html', products=products)

if __name__ == '__main__':
    with app.app_context():
        create_tables()
        insert_test_data()
    app.run(debug=True)