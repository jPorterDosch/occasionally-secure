from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# --- Database Initialization ---

def get_db():
    db = getattr(app, '_database', None)
    if db is None:
        db = app._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Return rows as dictionaries
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(app, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create users table (for demonstration)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                -- Add other user details as needed
                password TEXT -- In a real app, hash this!
            )
        """)
        # Create products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0
            )
        """)
        # Create cart table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS carts (
                cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                UNIQUE (user_id, product_id)
            )
        """)
        db.commit()

def populate_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Add a test user
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, password) VALUES (?, ?, ?)", (1, 'testuser', 'password'))
        # Add some test products
        cursor.execute("INSERT OR IGNORE INTO products (product_id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)", (101, 'Awesome T-Shirt', 'A really cool t-shirt', 25.99, 100))
        cursor.execute("INSERT OR IGNORE INTO products (product_id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)", (102, 'Fancy Mug', 'A mug for your fancy drinks', 12.50, 50))
        cursor.execute("INSERT OR IGNORE INTO products (product_id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)", (103, 'Out of Stock Item', 'This item is not available', 5.00, 0))
        db.commit()

# Initialize the database and populate with some data
init_db()
populate_db()

# --- API Endpoints ---

# Simulate user authentication (replace with a proper mechanism in a real app)
def get_current_user_id():
    # In a real application, you would likely use sessions, JWT, or other authentication methods
    # For this example, we'll just assume a user is logged in with ID 1
    return 1

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT product_id, name, description, price, stock FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    if product:
        return jsonify(dict(product))
    return jsonify({'message': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    user_id = get_current_user_id()
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'message': 'Invalid request'}), 400

    db = get_db()
    cursor = db.cursor()

    # Check if the product exists and is in stock
    cursor.execute("SELECT name, stock FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    if product['stock'] < quantity:
        return jsonify({'message': f'Not enough stock for product: {product["name"]}'}), 400

    try:
        # Check if the item is already in the user's cart
        cursor.execute("SELECT quantity FROM carts WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        existing_cart_item = cursor.fetchone()

        if existing_cart_item:
            new_quantity = existing_cart_item['quantity'] + quantity
            cursor.execute("UPDATE carts SET quantity = ? WHERE user_id = ? AND product_id = ?", (new_quantity, user_id, product_id))
        else:
            cursor.execute("INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))
        db.commit()
        return jsonify({'message': f'Added {quantity} of product ID {product_id} to cart'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Could not add item to cart (integrity error)'}), 400

@app.route('/cart', methods=['GET'])
def get_cart():
    user_id = get_current_user_id()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT c.product_id, p.name, p.price, c.quantity
        FROM carts c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = ?
    """, (user_id,))
    cart_items = cursor.fetchall()
    cart = []
    for item in cart_items:
        cart.append(dict(item))
    return jsonify({'cart': cart})

# --- Testing ---

if __name__ == '__main__':
    print("To test the API, you can use tools like curl or Postman.")
    print("Example curl commands:")
    print("  - Get product: curl http://127.0.0.1:5000/products/101")
    print("  - Add to cart: curl -X POST -H 'Content-Type: application/json' -d '{\"product_id\": 101, \"quantity\": 2}' http://127.0.0.1:5000/cart/add")
    print("  - Get cart: curl http://127.0.0.1:5000/cart")
    app.run(debug=True)