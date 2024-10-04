from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Database setup
DATABASE = 'ecommerce.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    tables = [
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS carts (
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        );
        """
    ]
    db = get_db_connection()
    cursor = db.cursor()
    for table in tables:
        cursor.execute(table)
    db.commit()
    db.close()

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db_connection()
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    db.close()
    if product:
        return jsonify(dict(product)), 200
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)

    if not user_id or not product_id:
        return jsonify({'error': 'Missing user_id or product_id'}),
