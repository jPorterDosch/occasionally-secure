from flask import Flask, request, jsonify, g, abort
import sqlite3

# Flask app initialization
app = Flask(__name__)

DATABASE = 'ecommerce.db'

# Connect to the database
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Close database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Initialize the database (Users and Products)
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                admin BOOLEAN NOT NULL
            )
        ''')

        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            )
        ''')

        # Insert dummy admin user and product data
        cursor.execute('INSERT INTO users (username, admin) VALUES ("admin_user", 1)')
        cursor.execute('INSERT INTO products (name, description, price) VALUES ("Product1", "First product", 100.0)')

        db.commit()

# Check if the user has admin privileges
def is_admin(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT admin FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    return user and user[0] == 1

# Add product function (Admin only)
@app.route('/add_product', methods=['POST'])
def add_product():
    user_id = request.json.get('user_id')
    name = request.json.get('name')
    description = request.json.get('description', '')
    price = request.json.get('price')

    if not is_admin(user_id):
        abort(403, description="Access denied: Admin privileges required")

    if not name or not price:
        return jsonify({"error": "Product name and price are required"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
    db.commit()

    return jsonify({"message": "Product added successfully"}), 201

# Remove product function (Admin only)
@app.route('/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product(product_id):
    user_id = request.json.get('user_id')

    if not is_admin(user_id):
        abort(403, description="Access denied: Admin privileges required")

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()

    return jsonify({"message": "Product removed successfully"}), 200

# Modify product function (Admin only)
@app.route('/modify_product/<int:product_id>', methods=['PUT'])
def modify_product(product_id):
    user_id = request.json.get('user_id')
    name = request.json.get('name')
    description = request.json.get('description', '')
    price = request.json.get('price')

    if not is_admin(user_id):
        abort(403, description="Access denied: Admin privileges required")

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    cursor.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?', (name, description, price, product_id))
    db.commit()

    return jsonify({"message": "Product updated successfully"}), 200

# Utility function to display all products
@app.route('/products', methods=['GET'])
def list_products():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()

    return jsonify(products)

# Utility function to add new users (for testing)
@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.json.get('username')
    admin = request.json.get('admin', False)

    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO users (username, admin) VALUES (?, ?)', (username, admin))
    db.commit()

    return jsonify({"message": "User added successfully"}), 201

# Run the app and create the DB if needed
if __name__ == '__main__':
    init_db()  # Initialize database
    app.run(debug=True)
