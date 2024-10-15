from flask import Flask, request, redirect, url_for, render_template_string, abort
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
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route('/')
def index():
    db = get_db()
    products = db.execute('SELECT * FROM products').fetchall()
    return render_template_string('''
        <h1>Product Management</h1>
        {% for product in products %}
            <p>{{ product['name'] }} - {{ product['description'] }} - ${{ product['price'] }}
            [<a href="{{ url_for('edit_product', product_id=product['id']) }}">Edit</a>]
            [<a href="{{ url_for('delete_product', product_id=product['id']) }}">Delete</a>]</p>
        {% endfor %}
        <a href="{{ url_for('add_product') }}">Add New Product</a>
        ''', products=products)

def check_admin(user_id):
    db = get_db()
    user = db.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,)).fetchone()
    return user and user['is_admin'] == 1

@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if not check_admin(1):  # Assuming user_id '1' for demonstration; replace with actual user session management
        abort(403)
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        db = get_db()
        db.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
        db.commit()
        return redirect(url_for('index'))
    return render_template_string('''
        <h1>Add New Product</h1>
        <form method="post">
            Name: <input type="text" name="name"><br>
            Description: <input type="text" name="description"><br>
            Price: <input type="text" name="price"><br>
            <input type="submit" value="Add Product">
        </form>
        <a href="{{ url_for('index') }}">Back</a>
        ''')

@app.route('/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if not check_admin(1):
        abort(403)
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        db.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?', (name, description, price, product_id))
        db.commit()
        return redirect(url_for('index'))
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    return render_template_string('''
        <h1>Edit Product</h1>
        <form method="post">
            Name: <input type="text" name="name" value="{{ product['name'] }}"><br>
            Description: <input type="text" name="description" value="{{ product['description'] }}"><br>
            Price: <input type="text" name="price" value="{{ product['price'] }}"><br>
            <input type="submit" value="Update Product">
        </form>
        <a href="{{ url_for('index') }}">Back</a>
        ''', product=product)

@app.route('/delete/<int:product_id>')
def delete_product(product_id):
    if not check_admin(1):
        abort(403)
    db = get_db()
    db.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()
    return redirect(url_for('index'))

# Schema setup for SQLite database
schema_sql = """
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS products;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    is_admin INTEGER NOT NULL
);
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL
);
INSERT INTO users (username, is_admin) VALUES ('admin', 1), ('user', 0);
"""

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)
