import sqlite3
import secrets
from functools import wraps

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # User table with admin rights
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, -- In a real application, use proper hashing
            is_admin INTEGER DEFAULT 0
        )
    ''')

    # Product table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')

    # Insert a default admin user and a non-admin user for testing
    cursor.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('admin', 'password123', 1))
    cursor.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('user', 'password456', 0))

    # Insert some sample products
    cursor.execute("INSERT OR IGNORE INTO products (name, description, price) VALUES (?, ?, ?)", ('Awesome T-Shirt', 'A comfortable and stylish t-shirt.', 25.99))
    cursor.execute("INSERT OR IGNORE INTO products (name, description, price) VALUES (?, ?, ?)", ('Cool Mug', 'A mug for your favorite beverages.', 12.50))

    conn.commit()
    conn.close()

create_tables()

# --- Authentication and Authorization (Simplified for this example) ---
# In a real application, you would have a more robust authentication system.

# Simulate a logged-in user
current_user = None

def login_user(username):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, is_admin FROM users WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        global current_user
        current_user = {'id': user_data[0], 'is_admin': user_data[1]}
        return True
    return False

def logout_user():
    global current_user
    current_user = None

def is_admin_user():
    return current_user and current_user['is_admin'] == 1

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_admin_user():
            return "Error: Admin privileges required."
        return func(*args, **kwargs)
    return wrapper

# --- CSRF Protection ---
_csrf_token = None

def generate_csrf_token():
    global _csrf_token
    _csrf_token = secrets.token_hex(16)
    return _csrf_token

def get_csrf_token():
    return _csrf_token

def verify_csrf_token(token):
    return token is not None and token == _csrf_token

# --- Product Management Functions ---

@admin_required
def add_product(name, description, price):
    if not name or price is None:
        return "Error: Product name and price are required."
    try:
        price = float(price)
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
        conn.commit()
        conn.close()
        return f"Product '{name}' added successfully with ID: {cursor.lastrowid}"
    except ValueError:
        return "Error: Invalid price format."

@admin_required
def modify_product(product_id, name=None, description=None, price=None, csrf_token=None):
    if not verify_csrf_token(csrf_token):
        return "Error: CSRF token is invalid."
    if not product_id:
        return "Error: Product ID is required."
    updates = []
    params = []
    if name:
        updates.append("name = ?")
        params.append(name)
    if description is not None:  # Allow setting description to None (empty)
        updates.append("description = ?")
        params.append(description)
    if price is not None:
        try:
            updates.append("price = ?")
            params.append(float(price))
        except ValueError:
            return "Error: Invalid price format."

    if not updates:
        return "No updates provided."

    sql = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
    params.append(product_id)

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    conn.close()
    if cursor.rowcount > 0:
        return f"Product with ID {product_id} updated successfully."
    else:
        return f"Error: Product with ID {product_id} not found."

@admin_required
def remove_product(product_id, csrf_token=None):
    if not verify_csrf_token(csrf_token):
        return "Error: CSRF token is invalid."
    if not product_id:
        return "Error: Product ID is required."
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount > 0:
        return f"Product with ID {product_id} removed successfully."
    else:
        return f"Error: Product with ID {product_id} not found."

def get_all_products():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, price FROM products")
    products = cursor.fetchall()
    conn.close()
    return products

def get_product_by_id(product_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, price FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

# --- Testing the Functionality ---

if __name__ == "__main__":
    print("--- Testing Admin Product Management ---")

    # Simulate login as an admin user
    print("\nLogging in as admin...")
    login_user('admin')
    print(f"Current user (admin): {current_user}")

    # Generate a CSRF token for admin actions
    csrf_token = generate_csrf_token()
    print(f"Generated CSRF Token: {csrf_token}")

    # Test adding a product
    print("\nAdding a new product...")
    add_result = add_product("New Gadget", "A brand new gadget with amazing features.", 99.99)
    print(add_result)

    # Test modifying a product
    print("\nModifying the newly added product...")
    # Get the ID of the last added product (you might want a more robust way to identify products in a real app)
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT last_insert_rowid()")
    new_product_id = cursor.fetchone()[0]
    conn.close()
    modify_result = modify_product(new_product_id, name="Updated Gadget", price=109.99, csrf_token=csrf_token)
    print(modify_result)

    # Test removing a product
    print("\nRemoving the updated product...")
    remove_result = remove_product(new_product_id, csrf_token=csrf_token)
    print(remove_result)

    # Simulate login as a non-admin user
    print("\nLogging in as a regular user...")
    logout_user()
    login_user('user')
    print(f"Current user (non-admin): {current_user}")

    # Try to add a product as a non-admin (should fail)
    print("\nTrying to add a product as a non-admin...")
    add_result_non_admin = add_product("Another Product", "This should fail.", 10.00)
    print(add_result_non_admin)

    # Try to modify a product as a non-admin (should fail)
    print("\nTrying to modify a product as a non-admin...")
    modify_result_non_admin = modify_product(1, name="Should Not Update", csrf_token=generate_csrf_token())
    print(modify_result_non_admin)

    # Try to remove a product as a non-admin (should fail)
    print("\nTrying to remove a product as a non-admin...")
    remove_result_non_admin = remove_product(2, csrf_token=generate_csrf_token())
    print(remove_result_non_admin)

    # List all products
    print("\nAll Products:")
    all_products = get_all_products()
    for product in all_products:
        print(product)

    # Get a specific product by ID
    print("\nGet Product by ID (ID 1):")
    product = get_product_by_id(1)
    print(product)

    # Logout
    logout_user()
    print("\nLogged out.")