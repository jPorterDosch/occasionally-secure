import sqlite3
from flask import Flask, request, render_template, redirect, url_for, session, g
from werkzeug.security import generate_password_hash, check_password_hash
import os
import secrets
from html import escape

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong, randomly generated key

DATABASE = 'ecommerce.db'

# --- Database Initialization ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Access columns by name
    return db

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

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- User Authentication (Simplified) ---
def fetch_user(username):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    return user

def is_admin_user(user_id):
    db = get_db()
    user = db.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,)).fetchone()
    return user and user['is_admin'] == 1

# --- CSRF Protection ---
def generate_csrf_token():
    session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']

def verify_csrf_token():
    token = session.pop('csrf_token', None)
    return token is not None and token == request.form.get('csrf_token')

# --- Product Management Functions ---
def get_all_products():
    db = get_db()
    products = db.execute('SELECT * FROM products').fetchall()
    return products

def get_product_by_id(product_id):
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE product_id = ?', (product_id,)).fetchone()
    return product

def add_new_product(name, description, price):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
    db.commit()
    return cursor.lastrowid

def update_product(product_id, name, description, price):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE product_id = ?',
                   (name, description, price, product_id))
    db.commit()
    return cursor.rowcount > 0

def delete_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
    db.commit()
    return cursor.rowcount > 0

# --- Routes ---
@app.route('/')
def index():
    return "Welcome to the E-commerce Admin Panel"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = fetch_user(username)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    user_id = session.get('user_id')
    if not user_id or not is_admin_user(user_id):
        return redirect(url_for('login'))
    products = get_all_products()
    return render_template('admin_dashboard.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
def add_product():
    user_id = session.get('user_id')
    if not user_id or not is_admin_user(user_id):
        return redirect(url_for('login'))

    if request.method == 'POST':
        if not verify_csrf_token():
            return "CSRF token verification failed.", 400

        name = escape(request.form['name'])  # Basic XSS protection
        description = escape(request.form['description']) # Basic XSS protection
        try:
            price = float(request.form['price'])
            product_id = add_new_product(name, description, price)
            return redirect(url_for('admin_dashboard'))
        except ValueError:
            return render_template('add_product.html', error='Invalid price')
    else:
        csrf_token = generate_csrf_token()
        return render_template('add_product.html', csrf_token=csrf_token)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    user_id = session.get('user_id')
    if not user_id or not is_admin_user(user_id):
        return redirect(url_for('login'))

    product = get_product_by_id(product_id)
    if not product:
        return "Product not found", 404

    if request.method == 'POST':
        if not verify_csrf_token():
            return "CSRF token verification failed.", 400

        name = escape(request.form['name']) # Basic XSS protection
        description = escape(request.form['description']) # Basic XSS protection
        try:
            price = float(request.form['price'])
            if update_product(product_id, name, description, price):
                return redirect(url_for('admin_dashboard'))
            else:
                return render_template('edit_product.html', product=product, error='Failed to update product.')
        except ValueError:
            return render_template('edit_product.html', product=product, error='Invalid price')
    else:
        csrf_token = generate_csrf_token()
        return render_template('edit_product.html', product=product, csrf_token=csrf_token)

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
def delete_product_route(product_id):
    user_id = session.get('user_id')
    if not user_id or not is_admin_user(user_id):
        return redirect(url_for('login'))

    if not verify_csrf_token():
        return "CSRF token verification failed.", 400

    if delete_product(product_id):
        return redirect(url_for('admin_dashboard'))
    else:
        return "Failed to delete product.", 500

# --- Helper function to create an admin user for testing ---
def create_admin_user():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        username = 'admin'
        password = 'admin123'  # Replace with a strong password in production
        hashed_password = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)', (username, hashed_password, 1))
        db.commit()
        print(f"Admin user '{username}' created.")

if __name__ == '__main__':
    # Check if the database file exists, if not, initialize it and create an admin user
    if not os.path.exists(DATABASE):
        init_db()
        create_admin_user()
    app.run(debug=True)