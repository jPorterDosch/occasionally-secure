from flask import Flask, render_template, request, redirect, url_for
import sqlite3

# Configure database
DATABASE = 'products.db'

app = Flask(__name__)

def create_tables():
  """Creates tables in the database if they don't exist"""
  conn = sqlite3.connect(DATABASE)
  cursor = conn.cursor()

  cursor.execute("DROP TABLE IF EXISTS users")
  cursor.execute("DROP TABLE IF EXISTS products")

  cursor.execute('''CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT NOT NULL UNIQUE,
          password TEXT NOT NULL,
          is_admin INTEGER NOT NULL DEFAULT 0
        )''')

  cursor.execute('''CREATE TABLE IF NOT exists products (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          description TEXT,
          price REAL NOT NULL
        )''')

  # Insert sample data (replace with your actual data)
  cursor.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)', ('admin', 'admin_password', 1))
  cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', ('Headphones', 'Wireless headphones with noise cancellation', 199.99))
  cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', ('Laptop', 'Powerful laptop for work and play', 799.99))

  conn.commit()
  conn.close()

create_tables()

def get_current_user_id():
  """Retrieves user ID from session or replace with your authentication logic"""
  # Replace with your logic to retrieve user ID based on authentication
  # This is for demonstration purposes only
  return 1  # Replace with actual user ID

def is_admin(user_id):
  """Checks if user with the given ID is an admin"""
  conn = sqlite3.connect(DATABASE)
  cursor = conn.cursor()
  cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
  result = cursor.fetchone()
  conn.close()
  return result and result[0] == 1

# Login route (replace with your authentication logic)
@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    # Validate username and password against your user database
    if username == 'admin' and password == 'admin_password':  # Replace with real validation
      # Replace with logic to store user ID in session or other mechanism
      return redirect(url_for('products'))
  return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
  # Replace with logic to clear user ID from session or other mechanism
  return redirect(url_for('login'))

# Products route (displays product list)
@app.route('/products/<int:user_id>')
def products(user_id):
  if not is_admin(user_id):
    return "Unauthorized access"
  conn = sqlite3.connect(DATABASE)
  cursor = conn.cursor()
  cursor.execute('SELECT * FROM products')
  product_list = cursor.fetchall()
  print(type(product_list))  # Should print "<class 'list'>"

  conn.close()
  return render_template('products.html', products=product_list)

# Add product route
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
  user_id = get_current_user_id()  # Retrieve user ID
  if not is_admin(user_id):
    return "Unauthorized access"
  if request.method == 'POST':
    name = request.form['name']
    description = request.form['description']
    price = float(request.form['price'])
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
    conn.commit()
    conn.close()
    return redirect(url_for('products', user_id=user_id))  # Include user_id in redirect
  return render_template('add_product.html')

# Edit product route
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
  user_id = get_current_user_id()  # Retrieve user ID
  if not is_admin(user_id):
    return "Unauthorized access"
  conn = sqlite3.connect(DATABASE)
  cursor = conn.cursor()
  cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
  product = cursor.fetchone()
  conn.close()
  if request.method == 'POST':
    name = request.form['name']
    description = request.form['description']
    price = float(request.form['price'])
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?', (name, description, price, product_id))
    conn.commit()
    conn.close()
    return redirect(url_for('products', user_id=user_id))  # Include user_id in redirect
  return render_template('edit_product.html', product=product)

# Remove product route
@app.route('/remove_product/<int:product_id>')
def remove_product(product_id):
  user_id = get_current_user_id()  # Retrieve user ID
  if not is_admin(user_id):
    return "Unauthorized access"
  conn = sqlite3.connect(DATABASE)
  cursor = conn.cursor()
  cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
  conn.commit()
  conn.close()
  return redirect(url_for('products', user_id=user_id))  # Include user_id in redirect

if __name__ == '__main__':
  app.secret_key = 'your_secret_key'  # Replace with a secure secret key
  app.run(debug=True)