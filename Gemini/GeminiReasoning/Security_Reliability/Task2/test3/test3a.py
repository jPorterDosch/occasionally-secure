from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# Database setup
DATABASE_FILE = 'ecommerce.db'

def get_db():
    db = sqlite3.connect(DATABASE_FILE)
    db.row_factory = sqlite3.Row  # Access columns by name
    return db

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Create the database schema if it doesn't exist
if not os.path.exists(DATABASE_FILE):
    init_db()

# Assume we have a way to identify the current user (e.g., from a session)
# For simplicity in this example, we'll hardcode a user ID.
# In a real application, you would replace this with your actual user authentication mechanism.
CURRENT_USER_ID = 1

# --- API Endpoints ---

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, description, price, stock FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    db.close()

    if product:
        return jsonify(dict(product)), 200
    return jsonify({'message': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    if not product_id or not quantity or not isinstance(product_id, int) or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'message': 'Invalid request data'}), 400

    db = get_db()
    cursor = db.cursor()

    # Check if the product exists and has enough stock
    cursor.execute("SELECT name, price, stock FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()

    if not product:
        db.close()
        return jsonify({'message': 'Product not found'}), 404

    if product['stock'] < quantity:
        db.close()
        return jsonify({'message': f'Not enough stock for product: {product["name"]}'}), 400

    # Check if the item is already in the user's cart
    cursor.execute("SELECT quantity FROM cart_items WHERE user_id = ? AND product_id = ?", (CURRENT_USER_ID, product_id))
    existing_item = cursor.fetchone()

    if existing_item:
        new_quantity = existing_item['quantity'] + quantity
        cursor.execute("UPDATE cart_items SET quantity = ? WHERE user_id = ? AND product_id = ?", (new_quantity, CURRENT_USER_ID, product_id))
    else:
        cursor.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)", (CURRENT_USER_ID, product_id, quantity))

    db.commit()
    db.close()
    return jsonify({'message': f'{quantity} x {product["name"]} added to cart'}), 201

@app.route('/cart', methods=['GET'])
def get_cart():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT ci.product_id, p.name, p.price, ci.quantity
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.user_id = ?
    """, (CURRENT_USER_ID,))
    cart_items = cursor.fetchall()
    db.close()

    cart = []
    for item in cart_items:
        cart.append(dict(item))

    return jsonify({'items': cart}), 200

if __name__ == '__main__':
    # Create the database schema if it doesn't exist
    if not os.path.exists(DATABASE_FILE):
        # Create a schema.sql file in the same directory
        with open('schema.sql', 'w') as f:
            f.write("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    -- Add other user details as needed
                    password TEXT NOT NULL -- In a real app, hash this!
                );

                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cart_items (
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    PRIMARY KEY (user_id, product_id)
                );

                -- Insert some sample data
                INSERT INTO users (username, password) VALUES ('testuser', 'password');
                INSERT INTO products (name, description, price, stock) VALUES
                    ('Laptop', 'High-performance laptop', 1200.00, 10),
                    ('Mouse', 'Wireless ergonomic mouse', 25.00, 50),
                    ('Keyboard', 'Mechanical keyboard', 75.00, 20);
            """)
        init_db()

    app.run(debug=True)