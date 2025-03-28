import sqlite3
import uuid
from functools import wraps
from html import escape

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, -- In a real app, store hashed passwords
            is_admin INTEGER DEFAULT 0
        )
    """)

    # Create products table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    """)

    # Create csrf_tokens table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS csrf_tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add a default admin user if no users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('admin', 'password123', 1))  # Replace with proper user creation in real app
        print("Default admin user created: username='admin', password='password123'")

    conn.commit()
    conn.close()

initialize_database()

# --- User Authentication and Authorization (Simplified) ---
# In a real application, you would have a more robust authentication system

class User:
    def __init__(self, user_id, username, is_admin):
        self.id = user_id
        self.username = username
        self.is_admin = is_admin

# Simulate a logged-in user (replace with your actual session management)
current_user = None

def set_logged_in_user(user_id):
    global current_user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, is_admin FROM users WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        current_user = User(user_data['id'], user_data['username'], user_data['is_admin'])
    else:
        current_user = None

def is_admin_user():
    return current_user and current_user.is_admin

# --- Admin Privilege Check Decorator ---
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_admin_user():
            return {"error": "Unauthorized: Admin privileges required."}
        return func(*args, **kwargs)
    return wrapper

# --- CSRF Protection ---
def generate_csrf_token(user_id):
    token = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO csrf_tokens (token, user_id) VALUES (?, ?)", (token, user_id))
    conn.commit()
    conn.close()
    return token

def verify_csrf_token(token, user_id):
    if not token:
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT token FROM csrf_tokens WHERE token = ? AND user_id = ?", (token, user_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def remove_csrf_token(token):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM csrf_tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()

# --- Product Management Functions ---
@admin_required
def add_product(name, description, price, csrf_token):
    if not verify_csrf_token(csrf_token, current_user.id):
        return {"error": "CSRF token is invalid."}

    if not name or not isinstance(name, str):
        return {"error": "Product name cannot be empty."}
    if not isinstance(price, (int, float)) or price <= 0:
        return {"error": "Product price must be a positive number."}
    if description and not isinstance(description, str):
        return {"error": "Product description must be a string."}

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    remove_csrf_token(csrf_token)
    return {"message": f"Product '{name}' added successfully with ID: {product_id}"}

@admin_required
def modify_product(product_id, name, description, price, csrf_token):
    if not verify_csrf_token(csrf_token, current_user.id):
        return {"error": "CSRF token is invalid."}

    if not product_id or not isinstance(product_id, int) or product_id <= 0:
        return {"error": "Invalid product ID."}
    if not name or not isinstance(name, str):
        return {"error": "Product name cannot be empty."}
    if not isinstance(price, (int, float)) or price <= 0:
        return {"error": "Product price must be a positive number."}
    if description and not isinstance(description, str):
        return {"error": "Product description must be a string."}

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?", (name, description, price, product_id))
    if cursor.rowcount == 0:
        conn.close()
        remove_csrf_token(csrf_token)
        return {"error": f"Product with ID {product_id} not found."}
    conn.commit()
    conn.close()
    remove_csrf_token(csrf_token)
    return {"message": f"Product with ID {product_id} updated successfully."}

@admin_required
def remove_product(product_id, csrf_token):
    if not verify_csrf_token(csrf_token, current_user.id):
        return {"error": "CSRF token is invalid."}

    if not product_id or not isinstance(product_id, int) or product_id <= 0:
        return {"error": "Invalid product ID."}

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    if cursor.rowcount == 0:
        conn.close()
        remove_csrf_token(csrf_token)
        return {"error": f"Product with ID {product_id} not found."}
    conn.commit()
    conn.close()
    remove_csrf_token(csrf_token)
    return {"message": f"Product with ID {product_id} removed successfully."}

# --- Helper function to fetch a product (for testing) ---
def get_product_by_id(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, price FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

# --- Testing the Functionality ---
if __name__ == "__main__":
    # Simulate user login
    print("--- Simulating User Login ---")
    set_logged_in_user(1)  # Assuming user ID 1 is the admin

    if is_admin_user():
        print(f"Logged in as admin: {current_user.username}")

        # --- Testing Add Product ---
        print("\n--- Testing Add Product ---")
        csrf_token_add = generate_csrf_token(current_user.id)
        add_result = add_product("New Product", "Description of the new product.", 25.99, csrf_token_add)
        print(f"Add Product Result: {add_result}")
        if "ID" in add_result.get("message", ""):
            new_product_id = int(add_result["message"].split("ID: ")[1])
            product = get_product_by_id(new_product_id)
            print(f"Retrieved New Product: {product}")

        # --- Testing Modify Product ---
        if new_product_id:
            print("\n--- Testing Modify Product ---")
            csrf_token_modify = generate_csrf_token(current_user.id)
            modify_result = modify_product(new_product_id, "Updated Product Name", "<script>alert('XSS')</script> Updated description.", 39.99, csrf_token_modify)
            print(f"Modify Product Result: {modify_result}")
            updated_product = get_product_by_id(new_product_id)
            print(f"Retrieved Updated Product (Note: Description is not sanitized here, that's done on display): {updated_product}")

        # --- Testing Remove Product ---
        if new_product_id:
            print("\n--- Testing Remove Product ---")
            csrf_token_remove = generate_csrf_token(current_user.id)
            remove_result = remove_product(new_product_id, csrf_token_remove)
            print(f"Remove Product Result: {remove_result}")
            deleted_product = get_product_by_id(new_product_id)
            print(f"Retrieved Deleted Product (should be None): {deleted_product}")

    else:
        print("Not logged in as an admin.")

    # Simulate a non-admin user
    print("\n--- Simulating Non-Admin User Login ---")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('testuser', 'password', 0))
    non_admin_user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    set_logged_in_user(non_admin_user_id)
    print(f"Logged in as non-admin: {current_user.username}")

    print("\n--- Testing Admin-Only Functions as Non-Admin ---")
    csrf_token_non_admin = generate_csrf_token(current_user.id)
    non_admin_add_result = add_product("Non-Admin Product", "Should fail", 10.00, csrf_token_non_admin)
    print(f"Non-Admin Add Product Result: {non_admin_add_result}")

    # --- Demonstrating XSS Prevention (on display, not in DB) ---
    print("\n--- Demonstrating XSS Prevention ---")
    malicious_description = "<script>alert('This is an XSS attack!')</script> Product with malicious description."
    safe_description = escape(malicious_description)
    print(f"Original Malicious Description: {malicious_description}")
    print(f"Sanitized Description for Display: {safe_description}")

    print("\n--- CSRF Token Generation for Forms ---")
    if current_user:
        new_csrf_token = generate_csrf_token(current_user.id)
        print(f"Generated CSRF token for user {current_user.id}: {new_csrf_token}")
        # In your HTML forms, you would include this token as a hidden field.
        # When the form is submitted, you would retrieve the token and pass it
        # to the add_product, modify_product, or remove_product functions.