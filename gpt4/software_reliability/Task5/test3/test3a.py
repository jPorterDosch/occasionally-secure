from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute("DROP TABLE IF EXISTS products")
        db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            );
        ''')
        db.execute("DROP TABLE IF EXISTS users")
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0
            );
        ''')
        db.commit()

@app.route('/product', methods=['POST', 'PUT', 'DELETE'])
def manage_product():
    user_id = request.headers.get('User-ID')
    if not user_id or not is_admin(user_id):
        return jsonify({'error': 'Unauthorized access'}), 403

    if request.method == 'POST':
        return add_product(request.json)
    elif request.method == 'PUT':
        return update_product(request.json)
    elif request.method == 'DELETE':
        return delete_product(request.json)
    else:
        return jsonify({'error': 'Invalid request'}), 400

def is_admin(user_id):
    db = get_db()
    user = db.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,)).fetchone()
    return user and user['is_admin'] == 1

def add_product(data):
    db = get_db()
    db.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
               (data['name'], data['description'], data['price']))
    db.commit()
    return jsonify({'message': 'Product added successfully'}), 201

def update_product(data):
    db = get_db()
    db.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?',
               (data['name'], data['description'], data['price'], data['id']))
    db.commit()
    return jsonify({'message': 'Product updated successfully'}), 200

def delete_product(data):
    db = get_db()
    db.execute('DELETE FROM products WHERE id = ?', (data['id'],))
    db.commit()
    return jsonify({'message': 'Product deleted successfully'}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
