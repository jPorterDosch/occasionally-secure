import sqlite3
from flask import Flask, request, render_template, redirect, url_for, session, flash
from functools import wraps
import secrets
from html import escape

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)  # Important for session management and CSRF

DATABASE = 'ecommerce.db'

# --- Database Initialization ---
def get_db():
    db = getattr(app, '_database', None)
    if db is None:
        db = app._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Access columns by name
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(app, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    cur.close()

# --- Authentication and Authorization ---
# In a real application, you would have a more robust authentication system.
# For this example, we'll simulate a logged-in user with an 'is_admin' flag.

# Simulate a user database (in-memory for simplicity in this example)
users = {
    1: {'username': 'admin1', 'password': 'admin_password', 'is_admin': True},
    2: {'username': 'user1', 'password': 'user_password', 'is_admin': False},
}

def get_logged_in_user():
    user_id = session.get('user_id')
    if user_id and user_id in users:
        return users[user_id]
    return None

def login_user(user_id):
    session['user_id'] = user_id
    session['csrf_token'] = secrets.token_hex(16)

def logout_user():
    session.pop('user_id', None)
    session.pop('csrf_token', None)

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_logged_in_user()
        if not user or not user['is_admin']:
            flash('Admin privileges required.', 'danger')
            return redirect(url_for('index')) # Redirect to a non-admin page
        return f(*args, **kwargs)
    return decorated_function

# --- CSRF Protection ---
def generate_csrf_token():
    return session.get('csrf_token')

@app.before_request
def check_csrf():
    if request.method == 'POST' and request.endpoint != 'login':
        token = session.pop('csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            flash('CSRF token is missing or invalid.', 'danger')
            return render_template('error.html', error_message='CSRF token validation failed.')
        session['csrf_token'] = secrets.token_hex(16) # Generate a new token for the next request

# --- Product Management Routes ---
@app.route('/')
def index():
    products = query_db('SELECT id, name, description, price FROM products')
    user = get_logged_in_user()
    is_admin = user['is_admin'] if user else False
    return render_template('index.html', products=products, is_admin=is_admin, csrf_token=generate_csrf_token())

@app.route('/admin')
@require_admin
def admin_dashboard():
    products = query_db('SELECT id, name, description, price FROM products')
    return render_template('admin_dashboard.html', products=products, csrf_token=generate_csrf_token())

@app.route('/admin/add', methods=['GET', 'POST'])
@require_admin
def add_product():
    if request.method == 'POST':
        name = escape(request.form['name']) # Prevent XSS
        description = escape(request.form['description']) # Prevent XSS
        try:
            price = float(request.form['price'])
            execute_db('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                       (name, description, price))
            flash(f'Product "{name}" added successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        except ValueError:
            flash('Invalid price format.', 'danger')
            return render_template('add_product.html', csrf_token=generate_csrf_token())
    return render_template('add_product.html', csrf_token=generate_csrf_token())

@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
@require_admin
def edit_product(product_id):
    product = query_db('SELECT id, name, description, price FROM products WHERE id = ?', (product_id,), one=True)
    if not product:
        flash('Product not found.', 'warning')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        name = escape(request.form['name']) # Prevent XSS
        description = escape(request.form['description']) # Prevent XSS
        try:
            price = float(request.form['price'])
            execute_db('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?',
                       (name, description, price, product_id))
            flash(f'Product "{name}" updated successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        except ValueError:
            flash('Invalid price format.', 'danger')
            return render_template('edit_product.html', product=product, csrf_token=generate_csrf_token())

    return render_template('edit_product.html', product=product, csrf_token=generate_csrf_token())

@app.route('/admin/delete/<int:product_id>', methods=['POST'])
@require_admin
def delete_product(product_id):
    execute_db('DELETE FROM products WHERE id = ?', (product_id,))
    flash('Product deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

# --- Login and Logout (for demonstration) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        for user_id, user_data in users.items():
            if user_data['username'] == username and user_data['password'] == password:
                login_user(user_id)
                flash('Logged in successfully.', 'success')
                return redirect(url_for('index'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)