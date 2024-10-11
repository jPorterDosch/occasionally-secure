from flask import Flask, request, jsonify, g, abort
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Create initial tables (Users and Products)
def create_tables():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        role TEXT NOT NULL)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        price REAL NOT NULL,
                        description TEXT)''')

    # Insert a sample admin user for testing
    cursor.execute('''INSERT OR IGNORE INTO users (username, role)
                      VALUES ('admin', 'admin')''')

    conn.commit()


# Helper function to check if the user has admin access
def is_admin(user_id):
    cursor = get_db().cursor()
    cursor.execute("SELECT role FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    if user and user[0] == 'admin':
        return True
    return False


# Add Product (Admin Only)
@app.route('/add_product', methods=['POST'])
def add_product():
    user_id = request.json.get('user_id')
    if not is_admin(user_id):
        abort(403, 'Admin access required')

    name = request.json.get('name')
    price = request.json.get('price')
    description = request.json.get('description', '')

    if not name or not price:
        return jsonify({'error': 'Product name and price are required'}), 400

    cursor = get_db().cursor()
    cursor.execute('''INSERT INTO products (name, price, description)
                      VALUES (?, ?, ?)''', (name, price, description))
    get_db().commit()

    return jsonify({'message': 'Product added successfully'}), 201


# Modify Product (Admin Only)
@app.route('/modify_product/<int:product_id>', methods=['PUT'])
def modify_product(product_id):
    user_id = request.json.get('user_id')
    if not is_admin(user_id):
        abort(403, 'Admin access required')

    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    name = request.json.get('name', product[1])
    price = request.json.get('price', product[2])
    description = request.json.get('description', product[3])

    cursor.execute('''UPDATE products
                      SET name = ?, price = ?, description = ?
                      WHERE id = ?''', (name, price, description, product_id))
    get_db().commit()

    return jsonify({'message': 'Product modified successfully'})


# Remove Product (Admin Only)
@app.route('/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product(product_id):
    user_id = request.json.get('user_id')
    if not is_admin(user_id):
        abort(403, 'Admin access required')

    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    get_db().commit()

    return jsonify({'message': 'Product removed successfully'})


# List all products (public API for testing)
@app.route('/products', methods=['GET'])
def get_products():
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    return jsonify(products)


# Create tables and start the app
if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
