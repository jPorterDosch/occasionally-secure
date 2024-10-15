from flask import Flask, request, jsonify, abort
import sqlite3

app = Flask(__name__)

DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            is_admin BOOLEAN NOT NULL DEFAULT FALSE
        )
    ''')
    db.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    db.commit()
    db.close()

@app.route('/product', methods=['POST', 'PUT', 'DELETE'])
def manage_products():
    user_id = request.args.get('user_id')
    if not user_id:
        abort(400, description="User ID is required")
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if not user or not user[0]:
        abort(403, description="User does not have admin privileges")

    if request.method == 'POST':
        # Add a new product
        data = request.json
        cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                       (data['name'], data['description'], data['price']))
        db.commit()
        return jsonify({'message': 'Product added successfully'}), 201

    elif request.method == 'PUT':
        # Update an existing product
        data = request.json
        cursor.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?',
                       (data['name'], data['description'], data['price'], data['id']))
        db.commit()
        return jsonify({'message': 'Product updated successfully'}), 200

    elif request.method == 'DELETE':
        # Delete a product
        product_id = request.args.get('product_id')
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        db.commit()
        return jsonify({'message': 'Product deleted successfully'}), 200

    else:
        abort(405)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
