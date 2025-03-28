from flask import Flask, request, jsonify
import sqlite3
from sqlite3 import Error

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def create_connection():
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        return conn
    except Error as e:
        print(e)
    return conn

def create_tables():
    """Create the products and carts tables if they don't exist."""
    conn = create_connection()
    cursor = conn.cursor()

    # Create products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        );
    """)

    # Create carts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (product_id)
        );
    """)

    # Create users table (for simplicity, assuming it exists)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE
        );
    """)

    conn.commit()
    conn.close()

def populate_initial_data():
    """Populate the products and users tables with some initial data for testing."""
    conn = create_connection()
    cursor = conn.cursor()

    # Add some sample products
    products = [
        ('Awesome T-Shirt', 'A really awesome t-shirt', 25.99, 100),
        ('Cool Mug', 'A mug that keeps your drinks cool', 12.50, 50),
        ('Fancy Notebook', 'A notebook for all your fancy thoughts', 8.75, 200)
    ]
    cursor.executemany("INSERT OR IGNORE INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)", products)

    # Add a sample user
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (1, 'testuser'))

    conn.commit()
    conn.close()

def get_product(product_id):
    """Retrieve product information by product ID."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, name, description, price, stock FROM products WHERE product_id=?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    if product:
        return {
            'product_id': product[0],
            'name': product[1],
            'description': product[2],
            'price': product[3],
            'stock': product[4]
        }
    return None

def add_to_cart(user_id, product_id, quantity):
    """Add a product to the user's cart."""
    conn = create_connection()
    cursor = conn.cursor()

    # Check if the product exists and is in stock
    cursor.execute("SELECT stock FROM products WHERE product_id=?", (product_id,))
    product_stock = cursor.fetchone()
    if not product_stock:
        conn.close()
        return False, "Product not found."
    if product_stock[0] < quantity:
        conn.close()
        return False, "Not enough stock."

    # Check if the item is already in the user's cart
    cursor.execute("SELECT quantity FROM carts WHERE user_id=? AND product_id=?", (user_id, product_id))
    existing_cart_item = cursor.fetchone()

    if existing_cart_item:
        new_quantity = existing_cart_item[0] + quantity
        cursor.execute("UPDATE carts SET quantity=? WHERE user_id=? AND product_id=?", (new_quantity, user_id, product_id))
    else:
        cursor.execute("INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))

    # Decrease the product stock
    new_stock = product_stock[0] - quantity
    cursor.execute("UPDATE products SET stock=? WHERE product_id=?", (new_stock, product_id))

    conn.commit()
    conn.close()
    return True, "Product added to cart."

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product_api(product_id):
    """API endpoint to retrieve product information by product ID."""
    product = get_product(product_id)
    if product:
        return jsonify(product)
    return jsonify({'message': 'Product not found'}), 404

@app.route('/cart', methods=['POST'])
def add_to_cart_api():
    """API endpoint to add a product to the user's cart."""
    data = request.get_json()
    if not data or 'user_id' not in data or 'product_id' not in data or 'quantity' not in data:
        return jsonify({'message': 'Missing required parameters'}), 400

    user_id = data['user_id']
    product_id = data['product_id']
    quantity = data['quantity']

    success, message = add_to_cart(user_id, product_id, quantity)
    if success:
        return jsonify({'message': message}), 201
    else:
        return jsonify({'message': message}), 400

if __name__ == '__main__':
    create_tables()
    populate_initial_data()
    app.run(debug=True)