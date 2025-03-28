from flask import Flask, render_template, request, redirect, url_for, g, flash
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from wtforms import ValidationError
from flask_wtf.csrf import CSRFProtect
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong, unique secret key
csrf = CSRFProtect(app)

DATABASE = 'ecommerce.db'

# --- Database Setup ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Access columns by name
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
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

# --- User Authentication (Simplified for this example) ---
# In a real application, you would have a more robust authentication system.

ADMIN_USER_ID = 1  # Example: User with ID 1 is an admin

def get_logged_in_user_id():
    # In a real application, this would come from the session.
    # For this example, we'll just return a fixed user ID.
    return ADMIN_USER_ID

def is_admin():
    user_id = get_logged_in_user_id()
    user = query_db('SELECT is_admin FROM users WHERE id = ?', (user_id,), one=True)
    return user and user['is_admin'] == 1

# --- Forms ---
class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Save Product')

class DeleteProductForm(FlaskForm):
    submit = SubmitField('Delete Product')

# --- Admin Routes ---
@app.before_request
def check_admin():
    if request.endpoint in ['admin_dashboard', 'add_product', 'edit_product', 'delete_product'] and not is_admin():
        flash('You do not have admin privileges.', 'danger')
        return redirect(url_for('index')) # Redirect to a non-admin page

@app.route('/')
def index():
    products = query_db('SELECT id, name, price FROM products')
    return render_template('index.html', products=products)

@app.route('/admin')
def admin_dashboard():
    products = query_db('SELECT id, name, price, stock FROM products')
    return render_template('admin_dashboard.html', products=products)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        price = form.price.data
        stock = form.stock.data
        execute_db('INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)',
                   (name, description, price, stock))
        flash(f'Product "{name}" added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('add_product.html', form=form)

@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = query_db('SELECT id, name, description, price, stock FROM products WHERE id = ?', (product_id,), one=True)
    if not product:
        flash('Product not found.', 'warning')
        return redirect(url_for('admin_dashboard'))

    form = ProductForm(obj=product) # Populate form with existing data

    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        price = form.price.data
        stock = form.stock.data
        execute_db('UPDATE products SET name = ?, description = ?, price = ?, stock = ? WHERE id = ?',
                   (name, description, price, stock, product_id))
        flash(f'Product "{name}" updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_product.html', form=form, product=product)

@app.route('/admin/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    form = DeleteProductForm()
    if form.validate_on_submit():
        product = query_db('SELECT name FROM products WHERE id = ?', (product_id,), one=True)
        if product:
            execute_db('DELETE FROM products WHERE id = ?', (product_id,))
            flash(f'Product "{product["name"]}" deleted successfully!', 'success')
        else:
            flash('Product not found.', 'warning')
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_dashboard')) # Redirect if form is not submitted

if __name__ == '__main__':
    # Ensure the database file exists or create it and initialize tables
    if not os.path.exists(DATABASE):
        with app.app_context():
            get_db()
            # Create an admin user for testing
            execute_db('INSERT INTO users (username, is_admin) VALUES (?, ?)', ('admin', 1))
            execute_db('INSERT INTO users (username, is_admin) VALUES (?, ?)', ('user', 0))
            execute_db('INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)',
                       ('Test Product 1', 'This is a test product.', 25.99, 100))
            execute_db('INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)',
                       ('Test Product 2', 'Another test product.', 49.50, 50))

    app.run(debug=True)