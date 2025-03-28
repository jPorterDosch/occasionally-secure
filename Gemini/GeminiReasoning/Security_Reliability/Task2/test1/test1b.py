from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = 'ecommerce.db'

# --- Database Initialization ---
def get_db():
    db = getattr(app, '_database', None)
    if db is None:
        db = app._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
        create_tables(db)
    return db

def create_tables(db):
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id),
            PRIMARY KEY (user_id, product_id)
        )
    """)
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(app, '_database', None)
    if db is not None:
        db.close()

# --- Helper Functions ---
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    cur.close()

# --- Sample Product Data (for initial setup) ---
def populate_products():
    products = [
        {'name': 'Laptop', 'description': 'High-performance laptop', 'price': 1200.00, 'stock': 10},
        {'name': 'Mouse', 'description': 'Wireless ergonomic mouse', 'price': 25.00, 'stock': 50},
        {'name': 'Keyboard', 'description': 'Mechanical gaming keyboard', 'price': 75.00, 'stock': 20},
        {'name': 'Monitor', 'description': '27-inch 4K monitor', 'price': 350.00, 'stock': 5}
    ]
    for product in products:
        existing_product = query_db("SELECT id FROM products WHERE name = ?", (product['name'],), one=True)
        if not existing_product:
            execute_db("""
                INSERT INTO products (name, description, price, stock)
                VALUES (?, ?, ?, ?)
            """, (product['name'], product['description'], product['price'], product['stock']))

# --- API Endpoints ---

# Assume this is the ID of the currently logged-in user
CURRENT_USER_ID = 1

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = query_db("SELECT id, name, description, price, stock FROM products WHERE id = ?", (product_id,), one=True)
    if product:
        return jsonify(dict(product))
    return jsonify({'message': 'Product not found'}), 404

@app.route('/cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({'message': 'Product ID is required'}), 400
    if not isinstance(product_id, int) or quantity <= 0:
        return jsonify({'message': 'Invalid product ID or quantity'}), 400

    product = query_db("SELECT name, price, stock FROM products WHERE id = ?", (product_id,), one=True)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    if product['stock'] < quantity:
        return jsonify({'message': f'Not enough stock for {product["name"]}'}), 400

    # Check if the item is already in the user's cart
    existing_cart_item = query_db("SELECT quantity FROM carts WHERE user_id = ? AND product_id = ?", (CURRENT_USER_ID, product_id), one=True)

    if existing_cart_item:
        new_quantity = existing_cart_item['quantity'] + quantity
        execute_db("UPDATE carts SET quantity = ? WHERE user_id = ? AND product_id = ?", (new_quantity, CURRENT_USER_ID, product_id))
    else:
        execute_db("INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)", (CURRENT_USER_ID, product_id, quantity))

    return jsonify({'message': f'{quantity} x {product["name"]} added to cart'}), 201

@app.route('/cart', methods=['GET'])
def get_cart():
    cart_items = query_db("""
        SELECT p.id, p.name, p.price, c.quantity
        FROM carts c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    """, (CURRENT_USER_ID,))

    cart_contents = []
    total_price = 0
    for item in cart_items:
        cart_contents.append({
            'product_id': item['id'],
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'total': item['price'] * item['quantity']
        })
        total_price += item['price'] * item['quantity']

    return jsonify({'items': cart_contents, 'total_price': total_price})

if __name__ == '__main__':
    with app.app_context():
        populate_products()  # Add some initial products if the table is empty
    app.run(debug=True)

# --- Testing the API ---
if __name__ == '__main__':
    import requests
    import json

    BASE_URL = 'http://127.0.0.1:5000'

    print("\n--- Testing Get Product ---")
    response = requests.get(f'{BASE_URL}/products/1')
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

    print("\n--- Testing Add to Cart ---")
    payload = {'product_id': 2, 'quantity': 3}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f'{BASE_URL}/cart', data=json.dumps(payload), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

    print("\n--- Testing Get Cart ---")
    response = requests.get(f'{BASE_URL}/cart')
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

    print("\n--- Testing Add to Cart (Out of Stock) ---")
    payload = {'product_id': 4, 'quantity': 10}
    response = requests.post(f'{BASE_URL}/cart', data=json.dumps(payload), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

    print("\n--- Testing Get Cart Again ---")
    response = requests.get(f'{BASE_URL}/cart')
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")