from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
import threading

# Configure the database connection (replace 'your_database.db' with your actual filename)
conn = sqlite3.connect('your_database.db')
c = conn.cursor()

# Define a function to create the tables if they don't exist
def create_tables():
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS user_purchases")
    c.execute("DROP TABLE IF EXISTS reviews")

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                UNIQUE(username)
             )''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
             )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                UNIQUE(user_id, product_id)
             )''')
    c.execute('''CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                review_text TEXT,
                review_score INTEGER NOT NULL CHECK (review_score BETWEEN 1 AND 5),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
             )''')
    c.execute('INSERT INTO users (username) VALUES (?)', ("user1",))
    c.execute('INSERT INTO products (name) VALUES (?)', ("Product A",))
    c.execute('INSERT INTO user_purchases (user_id, product_id) VALUES (?, ?)', (1, 1))
    conn.commit()

create_tables()  # Call the function to create tables

# Configure Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Not used in this approach, replace with a secure key for future use

# Function to get the database connection
def get_db():
    if not hasattr(g, 'db'):
        g.db = conn
    return g.db

@app.before_request
def before_request():
    get_db()
    print(f"Before request thread ID: {threading.get_ident()}")

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
        print(f"Teardown request thread ID: {threading.get_ident()}")

# **Fix in teardown_request:** Close the connection only if it exists within 'g'
@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

# Route to display the review form for a product
@app.route('/review/<int:product_id>/<int:user_id>')
def review_form(product_id, user_id):
    # Validate user ID (security measure)
    db = get_db()  # Get the connection from g.db
    cur = db.cursor()
    cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()
    if not user:
        return 'Invalid user ID.'

    # Check if user has purchased the product
    cur.execute('SELECT * FROM user_purchases WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    purchase = cur.fetchone()
    if not purchase:
        return 'You have not purchased this product yet.'

    return render_template('review_form.html', product_id=product_id)

# ... (other routes)

# Assuming you have templates like 'review_form.html' (replace with your actual template names)
# ... (Template code)

if __name__ == '__main__':
    app.run(debug=True)