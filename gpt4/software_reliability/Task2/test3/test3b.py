from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def db_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

def create_tables():
    conn = db_connection()
    cursor = conn.cursor()
    # Product Table: id, name, price, stock
    cursor.execute("DROP TABLE IF EXISTS product")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        );
    ''')
    # Cart Table: user_id, product_id, quantity
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (product_id) REFERENCES product (id)
        );
    ''')
    conn.commit()
    conn.close()

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM product WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    if product:
        return jsonify(product), 200
    else:
        return jsonify({'message': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    user_id = request.json['user_id']
    product_id = request.json['product_id']
    quantity = request.json.get('quantity', 1)

    conn = db_connection()
    cursor = conn.cursor()

    # Check product stock
    cursor.execute("SELECT stock FROM product WHERE id = ?", (product_id,))
    product_stock = cursor.fetchone()
    if product_stock and product_stock[0] >= quantity:
        # Update product stock
        new_stock = product_stock[0] - quantity
        cursor.execute("UPDATE product SET stock = ? WHERE id = ?", (new_stock, product_id))

        # Add to cart
        cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
                       (user_id, product_id, quantity))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Product added to cart'}), 200
    else:
        conn.close()
        return jsonify({'message': 'Not enough stock'}), 400

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)