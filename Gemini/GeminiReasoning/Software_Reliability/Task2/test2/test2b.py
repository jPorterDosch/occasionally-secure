from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# --- Database Initialization ---
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
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
    """Retrieves product information by ID."""
    db = get_db()
    product = db.execute('SELECT id, name, description, price, stock FROM products WHERE id = ?', (product_id,)).fetchone()
    db.close()

    if product:
        return jsonify(dict(product))
    return jsonify({'message': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Adds a product to the user's cart."""
    user_id = request.headers.get('X-User-ID')  # Assuming user ID is passed in the header
    if not user_id:
        return jsonify({'message': 'User identification missing'}), 401

    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({'message': 'Product ID is required'}), 400

    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'message': 'Quantity must be a positive integer'}), 400

    db = get_db()

    # Check if the product exists and has enough stock
    product = db.execute('SELECT name, price, stock FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        db.close()
        return jsonify({'message': 'Product not found'}), 404

    if product['stock'] < quantity:
        db.close()
        return jsonify({'message': f'Not enough stock for product: {product["name"]}'}), 400

    # Check if the product is already in the user's cart
    cart_item = db.execute('SELECT quantity FROM carts WHERE user_id = ? AND product_id = ?', (user_id, product_id)).fetchone()

    if cart_item:
        new_quantity = cart_item['quantity'] + quantity
        db.execute('UPDATE carts SET quantity = ? WHERE user_id = ? AND product_id = ?',
                   (new_quantity, user_id, product_id))
    else:
        db.execute('INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)',
                   (user_id, product_id, quantity))

    # Optionally, decrease the product stock (you might want to handle this in a more robust way in a real application)
    new_stock = product['stock'] - quantity
    db.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product_id))

    db.commit()
    db.close()

    return jsonify({'message': f'{quantity} of {product["name"]} added to cart'}), 201

if __name__ == '__main__':
    # Create the database and tables if they don't exist
    init_db()

    # Example usage if running directly (for development/testing)
    # You would typically run this using a WSGI server like Gunicorn in production
    app.run(debug=True)