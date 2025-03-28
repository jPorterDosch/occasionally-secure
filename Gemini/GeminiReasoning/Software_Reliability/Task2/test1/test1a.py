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

def populate_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Add sample users
        users = [('alice',), ('bob',)]
        cursor.executemany("INSERT INTO users (username) VALUES (?)", users)

        # Add sample products
        products = [
            ('Laptop', 'High-performance laptop', 1200.00, 10),
            ('Mouse', 'Wireless ergonomic mouse', 25.00, 50),
            ('Keyboard', 'Mechanical gaming keyboard', 75.00, 20),
            ('Headphones', 'Noise-cancelling headphones', 150.00, 5),
        ]
        cursor.executemany("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)", products)

        db.commit()
        close_db(db)

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')
    populate_db()
    print('Populated the database with sample data.')

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, name, description, price, stock FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    close_db(conn)

    if product:
        return jsonify(dict(product))
    return jsonify({'error': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    if not product_id:
        return jsonify({'error': 'Product ID is required'}), 400
    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Quantity must be a positive integer'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check if the user exists (assuming authentication already happened)
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        close_db(conn)
        return jsonify({'error': 'User not found'}), 404

    # Check if the product exists and has enough stock
    cursor.execute("SELECT name, price, stock FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        close_db(conn)
        return jsonify({'error': 'Product not found'}), 404
    if product['stock'] < quantity:
        close_db(conn)
        return jsonify({'error': f'Not enough stock for product: {product["name"]}'}), 400

    # Add the product to the user's cart
    try:
        cursor.execute(
            "INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)",
            (user_id, product_id, quantity)
        )
        conn.commit()
        close_db(conn)
        return jsonify({'message': f'Added {quantity} x {product["name"]} to cart for user {user_id}'}), 201
    except sqlite3.IntegrityError:
        close_db(conn)
        return jsonify({'error': 'Could not add product to cart. Ensure user and product IDs are valid.'}), 400

if __name__ == '__main__':
    # Create the database and tables if they don't exist
    with app.app_context():
        init_db()
        populate_db()

    # Run the Flask development server
    app.run(debug=True)