import sqlite3
from flask import Flask, request, render_template, redirect, url_for, session, g
from functools import wraps
import os
from html import escape
import secrets

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key

DATABASE = 'ecommerce.db'

# --- Database Initialization ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Access columns by name
    return db

def close_db():
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema2.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

@app.teardown_appcontext
def teardown_db(error):
    close_db()

# --- Authentication and Authorization ---
def login_user(user_id):
    session['user_id'] = user_id

def logout_user():
    session.pop('user_id', None)

def get_current_user():
    user_id = session.get('user_id')
    if user_id is None:
        return None
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return user

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user is None or not user['is_admin']:
            return render_template('unauthorized.html')
        return f(*args, **kwargs)
    return decorated_function

# --- CSRF Protection ---
def generate_csrf_token():
    token = secrets.token_hex(16)
    session['csrf_token'] = token
    return token

def verify_csrf_token(token):
    if not token:
        return False
    return token == session.pop('csrf_token', None)

@app.before_request
def before_request():
    if request.method == 'POST':
        if not verify_csrf_token(request.form.get('csrf_token')):
            return render_template('csrf_error.html')

# --- Product Management Routes ---
@app.route('/admin/products')
@require_admin
def list_products():
    db = get_db()
    products = db.execute('SELECT * FROM products').fetchall()
    return render_template('admin/list_products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@require_admin
def add_product():
    if request.method == 'POST':
        name = escape(request.form['name'])
        description = escape(request.form['description'])
        price = float(request.form['price'])
        db = get_db()
        db.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                   (name, description, price))
        db.commit()
        return redirect(url_for('list_products'))
    return render_template('admin/add_product.html', csrf_token=generate_csrf_token())

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@require_admin
def edit_product(product_id):
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if product is None:
        return "Product not found.", 404

    if request.method == 'POST':
        name = escape(request.form['name'])
        description = escape(request.form['description'])
        price = float(request.form['price'])
        db.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?',
                   (name, description, price, product_id))
        db.commit()
        return redirect(url_for('list_products'))
    return render_template('admin/edit_product.html', product=product, csrf_token=generate_csrf_token())

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@require_admin
def delete_product(product_id):
    db = get_db()
    db.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()
    return redirect(url_for('list_products'))

# --- Example Login/Logout (for testing admin access) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  # In a real app, hash and verify
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        if user:
            login_user(user['id'])
            return redirect(url_for('list_products'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Basic Home Page (for non-admin users) ---
@app.route('/')
def index():
    return "Welcome to the e-commerce site!"

# --- Error Handling Templates ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html'), 403

@app.route('/csrf_error')
def csrf_error():
    return render_template('csrf_error.html'), 400

if __name__ == '__main__':
    # Ensure the database file exists or create it and initialize
    if not os.path.exists(DATABASE):
        init_db()
        with app.app_context():
            db = get_db()
            # Create an example admin user for testing
            db.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('admin', 'password', 1))
            # Create a non-admin user for testing
            db.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('user', 'password', 0))
            db.commit()
            print("Created initial users.")

    app.run(debug=True)