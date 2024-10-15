from flask import Flask, request, jsonify, abort
import sqlite3
from functools import wraps

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    tables = [
        '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT FALSE
        )''',
        '''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL
        )'''
    ]
    conn = get_db_connection()
    cursor = conn.cursor()
    for table in tables:
        cursor.execute(table)
    conn.commit()
    conn.close()

def check_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('user_id')
        if not user_id:
            abort(401, description="Authentication required")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result and result['is_admin']:
            return f(*args, **kwargs)
        abort(403, description="Admin access required")
    return decorated_function

@app.route('/product', methods=['POST'])
@check_admin
def add_product():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', 
                   (data['name'], data['description'], data['price']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Product added'}), 201

@app.route('/product/<int:product_id>', methods=['PUT'])
@check_admin
def update_product(product_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?',
                   (data['name'], data['description'], data['price'], product_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Product updated'})

@app.route('/product/<int:product_id>', methods=['DELETE'])
@check_admin
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Product deleted'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
