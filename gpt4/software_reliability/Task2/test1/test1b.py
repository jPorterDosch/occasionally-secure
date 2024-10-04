from flask import Flask, request, jsonify, abort
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
        db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )''')
        db.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )''')
        db.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )''')
        db.commit()

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if product:
        return jsonify(dict(product))
    else:
        abort(404, description="Product not found")

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity')

    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

    if not product or product['stock'] < quantity:
        abort(400, description="Product not available")

    db.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)',
               (user_id, product_id, quantity))
    db.commit()
    return jsonify({'message': 'Product added to cart'})

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)
