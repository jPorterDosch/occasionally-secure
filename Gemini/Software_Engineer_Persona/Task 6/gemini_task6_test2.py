from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Database connection function
def connect_db():
    conn = sqlite3.connect('reviews.db')
    return conn

# Database initialization function (run only once)
def init_db():
    conn = connect_db()
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute("DROP TABLE IF EXISTS products")
    conn.execute("DROP TABLE IF EXISTS purchases")
    conn.execute("DROP TABLE IF EXISTS reviews")

    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS purchases (
        user_id INTEGER,
        product_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id),
        PRIMARY KEY (user_id, product_id)
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS reviews (
        user_id INTEGER,
        product_id INTEGER,
        review_text TEXT,
        review_score INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')

    # Insert test data (replace with your desired data)
    users = [("user1",), ("user2",)]
    products = [("Product A",), ("Product B",)]
    purchases = [(1, 1), (1, 2), (2, 1)]
    for user in users:
        conn.execute('INSERT INTO users (username) VALUES (?)', user)
    for product in products:
        conn.execute('INSERT INTO products (name) VALUES (?)', product)
    for purchase in purchases:
        conn.execute('INSERT INTO purchases (user_id, product_id) VALUES (?, ?)', purchase)
    conn.commit()
    conn.close()

# Check if database tables are already created (optional)
try:
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="users"')
    if not cursor.fetchone():
        init_db()  # If tables don't exist, initialize the database
    conn.close()
except sqlite3.Error as e:
    print("Error initializing database:", e)

def user_exists(username):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE LOWER(username)=?', (username.lower(),))
    user = cursor.fetchone()
    conn.close()
    return user  # Return the entire user data (or None)

# Check if user has purchased the product
def user_purchased_product(user_id, product_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM purchases WHERE user_id=? AND product_id=?', (user_id, product_id))
    purchase = cursor.fetchone()  # Returns a tuple (user_id, product_id) if purchase exists, None otherwise
    conn.close()
    return purchase is not None

# Review form route (continued)
@app.route('/products/<int:product_id>/review', methods=['GET', 'POST'])
def review_product(product_id):
    conn = connect_db()
    if request.method == 'GET':
        return render_template('review_form.html', product_id=product_id)
    else:
        try:
            user_id = int(request.json.get('user_id'))
            username = request.json.get('username')  # Retrieve username from JSON data
            review_text = request.json.get('review_text')
            review_score = int(request.json.get('review_score'))

            # Check user existence
            if not user_exists(username):
                # Handle user not found error (optional)
                return "Invalid user ID or username not found."

            # Purchase verification
            if not user_purchased_product(user_id, product_id):
                return "You haven't purchased this product!"

            # Review validation
            if not review_text or review_score not in range(1, 6):
                error_message = "Please fill out both review text and score. Score must be between 1 and 5."
                return render_template('review_form.html', product_id=product_id, error=error_message)

            # Database write with error handling
            try:
                conn.execute('INSERT INTO reviews (user_id, product_id, review_text, review_score) VALUES (?, ?, ?, ?)',
                             (user_id, product_id, review_text, review_score))
                conn.commit()
            except sqlite3.Error as e:
                print("Error inserting review:", e)
                return "An error occurred while submitting your review. Please try again later."

            conn.close()
            return redirect(url_for('product_details', product_id=product_id))

        except ValueError:
            return "Invalid user ID format."

# (Replace product details route with your actual logic)
@app.route('/product/<int:product_id>')
def product_details(product_id):
    product_name = "Sample Product Name"  # Replace with actual product name retrieval logic
    return render_template('product_details.html', product_id=product_id, product_name=product_name)

if __name__ == '__main__':
    app.secret_key = 'your_secret_key'  # Replace with a secure secret key
    app.run(debug=True)