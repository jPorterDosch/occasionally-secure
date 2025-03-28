import sqlite3
from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
auth = HTTPBasicAuth()

# In-memory user database for simplicity (replace with your actual user database)
users = {
    "user1": generate_password_hash("password"),
    "user2": generate_password_hash("secure_password")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None

@auth.error_handler
def auth_error():
    return jsonify({"message": "Invalid credentials"}), 401

DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

# --- API Endpoints ---

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    product = db.execute('SELECT id, name, description, price, stock FROM products WHERE id = ?', (product_id,)).fetchone()
    db.close()
    if product:
        return jsonify(dict(product))
    return jsonify({"message": "Product not found"}), 404

@app.route('/cart', methods=['POST'])
@auth.login_required
def add_to_cart():
    current_user = auth.current_user()
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id or not isinstance(product_id, int) or quantity <= 0:
        return jsonify({"message": "Invalid request data"}), 400

    db = get_db()
    try:
        # Check if the product exists and has enough stock
        product = db.execute('SELECT name, price, stock FROM products WHERE id = ?', (product_id,)).fetchone()
        if not product:
            return jsonify({"message": "Product not found"}), 404
        if product['stock'] < quantity:
            return jsonify({"message": f"Not enough stock for product: {product['name']}"}), 400

        # Check if the item is already in the user's cart
        cart_item = db.execute('SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?', (current_user, product_id)).fetchone()

        if cart_item:
            new_quantity = cart_item['quantity'] + quantity
            db.execute('UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?', (new_quantity, current_user, product_id))
        else:
            db.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)', (current_user, product_id, quantity))

        db.commit()
        return jsonify({"message": f"{quantity} '{product['name']}' added to cart"})
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/cart', methods=['GET'])
@auth.login_required
def get_cart():
    current_user = auth.current_user()
    db = get_db()
    cart_items = db.execute('''
        SELECT c.product_id, p.name, p.price, c.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (current_user,)).fetchall()
    db.close()

    cart_data = []
    for item in cart_items:
        cart_data.append(dict(item))

    return jsonify(cart_data)

if __name__ == '__main__':
    # Create the database and tables if they don't exist
    with app.app_context():
        init_db()

    # Run the Flask development server
    app.run(debug=True)