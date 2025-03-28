from flask import Flask, request, jsonify
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

DATABASE = 'ecommerce.db'

# --- Database Initialization and Sample Data ---

def get_db():
    db = getattr(app, '_database', None)
    if db is None:
        db = app._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Access columns by name
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

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0
            )
        ''')

        # Create carts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                UNIQUE (user_id, product_id)
            )
        ''')

        # Insert sample users (for testing)
        cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
                       ('user1', generate_password_hash('password1')))
        cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
                       ('user2', generate_password_hash('password2')))

        # Insert sample products (for testing)
        cursor.execute("INSERT OR IGNORE INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                       ('Awesome T-Shirt', 'A comfortable and stylish t-shirt.', 25.99, 100))
        cursor.execute("INSERT OR IGNORE INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                       ('Cool Mug', 'A mug to keep your drinks hot or cold.', 12.50, 50))
        cursor.execute("INSERT OR IGNORE INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                       ('Fancy Notebook', 'A high-quality notebook for your notes.', 15.00, 25))

        db.commit()

# --- Authentication ---

def authenticate():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return None, None
    return auth.username, auth.password

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        username, password = authenticate()
        if not username or not password:
            return jsonify({'message': 'Authentication required'}), 401

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user or not check_password_hash(user['password'], password):
            return jsonify({'message': 'Invalid credentials'}), 401
        return f(user['id'], *args, **kwargs)
    return decorated

# --- API Endpoints ---

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, description, price, stock FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()

    if product:
        return jsonify(dict(product)), 200
    return jsonify({'message': 'Product not found'}), 404

@app.route('/cart', methods=['POST'])
@requires_auth
def add_to_cart(user_id):
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({'message': 'Missing product_id'}), 400
    if not isinstance(product_id, int) or quantity <= 0:
        return jsonify({'message': 'Invalid product_id or quantity'}), 400

    db = get_db()
    cursor = db.cursor()

    # Check if the product exists and is in stock
    cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    if product['stock'] < quantity:
        return jsonify({'message': 'Product is out of stock or not enough stock'}), 400

    try:
        # Add item to cart or update quantity if it already exists
        cursor.execute('''
            INSERT INTO carts (user_id, product_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, product_id) DO UPDATE SET quantity = quantity + ?
        ''', (user_id, product_id, quantity, quantity))
        db.commit()
        return jsonify({'message': 'Product added to cart successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Invalid product ID'}), 400

@app.route('/cart', methods=['GET'])
@requires_auth
def get_cart(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT c.product_id, p.name, p.price, c.quantity
        FROM carts c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (user_id,))
    cart_items = cursor.fetchall()
    cart = []
    for item in cart_items:
        cart.append(dict(item))
    return jsonify(cart), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True)