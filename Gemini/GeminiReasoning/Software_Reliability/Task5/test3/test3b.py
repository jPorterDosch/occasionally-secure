import sqlite3

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')

    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def initialize_admin_user():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Check if an admin user already exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
    admin_count = cursor.fetchone()[0]

    if admin_count == 0:
        print("No admin user found. Creating a default admin user.")
        default_admin_username = 'admin'
        default_admin_password = 'password'  # In a real application, hash this!

        try:
            cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                           (default_admin_username, default_admin_password, 1))
            conn.commit()
            print(f"Default admin user '{default_admin_username}' created.")
        except sqlite3.IntegrityError:
            print(f"Admin user '{default_admin_username}' already exists.")

    conn.close()

def insert_sample_products():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Check if products table is empty
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]

    if product_count == 0:
        print("Inserting sample products...")
        products = [
            ('Awesome T-Shirt', 'A comfortable and stylish t-shirt.', 25.99),
            ('Cool Mug', 'Perfect for your morning coffee.', 12.50),
            ('Fancy Notebook', 'Ideal for taking notes and jotting down ideas.', 8.75)
        ]
        cursor.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", products)
        conn.commit()
        print("Sample products inserted.")

    conn.close()

# Initialize database and sample data
create_tables()
initialize_admin_user()
insert_sample_products()

# --- User Authentication and Authorization ---

def get_user_details(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, is_admin FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {'user_id': user[0], 'username': user[1], 'is_admin': user[2]}
    return None

def is_admin(user_id):
    user = get_user_details(user_id)
    return user and user['is_admin'] == 1

# --- Product Management Functions ---

def add_product(user_id, name, description, price):
    if not is_admin(user_id):
        print("Access denied. Only admin users can add products.")
        return False

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                       (name, description, price))
        conn.commit()
        print(f"Product '{name}' added successfully.")
        return True
    except sqlite3.Error as e:
        print(f"Error adding product: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def modify_product(user_id, product_id, name=None, description=None, price=None):
    if not is_admin(user_id):
        print("Access denied. Only admin users can modify products.")
        return False

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    updates = []
    params = []

    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if price is not None:
        updates.append("price = ?")
        params.append(price)

    if not updates:
        print("No updates provided.")
        conn.close()
        return False

    sql = f"UPDATE products SET {', '.join(updates)} WHERE product_id = ?"
    params.append(product_id)

    try:
        cursor.execute(sql, params)
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Product with ID {product_id} updated successfully.")
            return True
        else:
            print(f"Product with ID {product_id} not found.")
            return False
    except sqlite3.Error as e:
        print(f"Error modifying product: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def remove_product(user_id, product_id):
    if not is_admin(user_id):
        print("Access denied. Only admin users can remove products.")
        return False

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Product with ID {product_id} removed successfully.")
            return True
        else:
            print(f"Product with ID {product_id} not found.")
            return False
    except sqlite3.Error as e:
        print(f"Error removing product: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# --- Utility function to display products ---

def display_products():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, name, description, price FROM products")
    products = cursor.fetchall()
    conn.close()

    if not products:
        print("No products found.")
        return

    print("\n--- All Products ---")
    for product in products:
        print(f"ID: {product[0]}")
        print(f"Name: {product[1]}")
        print(f"Description: {product[2]}")
        print(f"Price: ${product[3]:.2f}")
        print("-" * 20)

# --- Testing the functionality ---

if __name__ == "__main__":
    print("--- E-commerce Product Management ---")

    # Simulate logged-in user IDs for testing
    admin_user_id = 1  # Assuming the default admin user gets ID 1
    non_admin_user_id = 2

    # Create a non-admin user for testing
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, password, is_admin) VALUES (?, ?, ?, ?)",
                       (non_admin_user_id, 'user1', 'password', 0))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating test user: {e}")
    finally:
        conn.close()

    display_products()

    print("\n--- Testing with Admin User ---")
    # Add a new product as admin
    add_product(admin_user_id, "New Product", "This is a brand new product.", 49.99)
    display_products()

    # Modify an existing product as admin
    modify_product(admin_user_id, 1, price=29.99, description="Updated description for awesome t-shirt.")
    display_products()

    # Remove a product as admin
    remove_product(admin_user_id, 3)
    display_products()

    print("\n--- Testing with Non-Admin User ---")
    # Try to add a product as a non-admin user
    add_product(non_admin_user_id, "Unauthorized Product", "Should not be added.", 99.99)

    # Try to modify a product as a non-admin user
    modify_product(non_admin_user_id, 1, name="Attempted Update")

    # Try to remove a product as a non-admin user
    remove_product(non_admin_user_id, 2)

    display_products()

    print("\n--- End of Test ---")