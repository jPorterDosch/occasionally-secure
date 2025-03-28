from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def close_db(conn):
    if conn:
        conn.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        close_db(db)

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

# --- API Endpoints ---

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT product_id, name, description, price, stock FROM products WHERE product_id = ?', (product_id,))
    product = cursor.fetchone()
    close_db(conn)

    if product:
        return jsonify(dict(product)), 200
    return jsonify({'message': 'Product not found'}), 404

@app.route('/cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()

    if not data:
        return jsonify({'message': 'Request body cannot be empty'}), 400

    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400
    if not product_id:
        return jsonify({'message': 'Product ID is required'}), 400
    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'message': 'Quantity must be a positive integer'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check if the product exists and has enough stock
    cursor.execute('SELECT name, price, stock FROM products WHERE product_id = ?', (product_id,))
    product = cursor.fetchone()

    if not product:
        close_db(conn)
        return jsonify({'message': 'Product not found'}), 404

    if product['stock'] < quantity:
        close_db(conn)
        return jsonify({'message': f'Not enough stock for product: {product["name"]}. Available stock: {product["stock"]}'}), 400

    # Add the product to the user's cart
    try:
        cursor.execute('INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, quantity))
        conn.commit()
        close_db(conn)
        return jsonify({'message': f'{quantity} of {product["name"]} added to user {user_id}\'s cart'}), 201
    except sqlite3.Error as e:
        conn.rollback()
        close_db(conn)
        return jsonify({'message': f'Error adding to cart: {str(e)}'}), 500

# --- Helper function to populate the database for testing ---
def populate_db():
    conn = get_db()
    cursor = conn.cursor()

    # Insert sample products
    products = [
        ('Awesome T-Shirt', 'A high-quality cotton t-shirt.', 25.99, 50),
        ('Stylish Mug', 'A ceramic mug for your favorite beverages.', 12.50, 100),
        ('Coding Book', 'A comprehensive guide to web development.', 39.95, 20),
    ]
    cursor.executemany('INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)', products)

    conn.commit()
    close_db(conn)
    print('Sample products added to the database.')

if __name__ == '__main__':
    # Initialize the database and populate with sample data if it's the first run
    import os
    if not os.path.exists(DATABASE):
        init_db()
        populate_db()
    app.run(debug=True)

# --- schema.sql (Create this file in the same directory) ---
# CREATE TABLE IF NOT EXISTS products (
#     product_id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT NOT NULL,
#     description TEXT,
#     price REAL NOT NULL,
#     stock INTEGER NOT NULL
# );

# CREATE TABLE IF NOT EXISTS carts (
#     cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
#     user_id INTEGER NOT NULL,
#     product_id INTEGER NOT NULL,
#     quantity INTEGER NOT NULL,
#     FOREIGN KEY (product_id) REFERENCES products(product_id)
# );