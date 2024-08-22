from flask import Flask, render_template, request, redirect, url_for, session  # Import session directly
import sqlite3
import unittest  # Import for unit tests

# Configure database
DATABASE = 'products.db'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_strong_secret_key'  # Replace with a strong secret key

def create_tables():
    conn = sqlite3.connect(DATABASE)
    print("Creating tables...")
    # ... table creation statements (consider using f-strings for clarity) ...
    conn.commit()
    conn.close()

def get_current_user():
    if 'username' in session:
        username = session['username']
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE username = ?", (username,))
        is_admin = cursor.fetchone()[0]
        conn.close()
        return username, is_admin
    return None, False

@app.shell_context_processor
def inject_tables():
    """Injects tables creation function to shell context for manual table creation"""
    def create_tables():
        """Creates tables in the database"""
        conn = sqlite3.connect(DATABASE)
        print("Creating tables...")
        conn.execute("DROP TABLE IF EXISTS users")
        conn.execute("DROP TABLE IF EXISTS products")
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              password TEXT NOT NULL,
              is_admin INTEGER NOT NULL DEFAULT 0
           )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS products (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              description TEXT,
              price REAL NOT NULL
           )''')
        conn.commit()
        conn.close()
    return {'create_tables': create_tables}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Implement logic to verify username and password against user database
        # Replace with your authentication logic (consider hashing passwords)
        if username == 'admin' and password == 'admin_password':  # Example logic (insecure!)
            session['username'] = username  # Store username in session
            return redirect(url_for('products'))
        else:
            error = 'Invalid credentials'
    else:
        error = None
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    return redirect(url_for('login'))

@app.route('/products')
def products():
    current_user, is_admin = get_current_user()
    if not is_admin:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    current_user, is_admin = get_current_user()
    if not is_admin:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
        conn.commit()
        conn.close()
        return redirect(url_for('products'))
    return render_template('add_product.html')

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    current_user, is_admin = get_current_user()
    if not is_admin:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    if not product:
        return render_template('error.html', message="Product not found!")
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?", (name, description, price, product_id))
        conn.commit()
        conn.close()
        return redirect(url_for('products'))
    return render_template('edit_product.html', product=product)

# Unit tests using Flask's built-in test client
class TestProductManagement(unittest.TestCase):
    def create_app(self):
        app.config['TESTING'] = True  # Enable testing mode
        return app  # **Fix:** Return the app instance

    def test_login_success(self):
        with self.app.test_client() as client:
            data = {'username': 'admin', 'password': 'admin_password'}  # Replace with secure credentials
            response = client.post('/login', data=data)
            self.assertEqual(response.status_code, 302)  # Check for redirect on successful login

    # ... other unit tests ...

    def test_edit_product_success(self):
        with self.app.test_client() as client:
            # Simulate login (consider using a helper function)
            data = {'username': 'admin', 'password': 'admin_password'}
            client.post('/login', data=data)

            # Simulate product creation (consider mocking or using a fixture)
            product_data = {'name': 'Test Product', 'description': 'A test description', 'price': 10.99}
            response = client.post('/add_product', data=product_data)
            self.assertEqual(response.status_code, 302)  # Check for redirect on successful creation

            # Get the newly created product ID
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM products ORDER BY id DESC LIMIT 1")
            product_id = cursor.fetchone()[0]
            conn.close()

            # Simulate editing the product
            edit_data = {'name': 'Updated Product', 'description': 'Updated description', 'price': 12.34}
            response = client.post(f'/edit_product/{product_id}', data=edit_data)
            self.assertEqual(response.status_code, 302)  # Check for redirect on successful edit

            # Verify product details are updated
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            edited_product = cursor.fetchone()
            conn.close()

            self.assertEqual(edited_product['name'], edit_data['name'])
            self.assertEqual(edited_product['description'], edit_data['description'])
            self.assertEqual(edited_product['price'], edit_data['price'])

    def test_edit_product_nonexistent(self):
        with self.app.test_client() as client:
            # Simulate login (consider using a helper function)
            data = {'username': 'admin', 'password': 'admin_password'}
            client.post('/login', data=data)

            # Attempt to edit a non-existent product
            nonexistent_id = 100  # Adjust based on your test setup
            response = client.post(f'/edit_product/{nonexistent_id}', data={'name': 'Nonexistent'})
            self.assertEqual(response.status_code, 200)  # Expect error template to be rendered
            self.assertIn(b"Product not found!", response.data)

if __name__ == '__main__':
    unittest.main()
