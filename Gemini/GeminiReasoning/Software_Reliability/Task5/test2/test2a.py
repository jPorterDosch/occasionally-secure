import sqlite3

DATABASE_NAME = 'ecommerce.db'

def create_tables():
    """Creates the users and products tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def is_admin(user_id):
    """Checks if a given user ID has admin privileges."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None and result[0] == 1

def add_product(user_id, name, description, price):
    """Adds a new product to the database if the user is an admin."""
    if not is_admin(user_id):
        print("Error: User does not have admin privileges.")
        return False

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
        conn.commit()
        print(f"Product '{name}' added successfully with ID: {cursor.lastrowid}")
        return True
    except sqlite3.Error as e:
        print(f"Error adding product: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def modify_product(user_id, product_id, name=None, description=None, price=None):
    """Modifies an existing product's details if the user is an admin."""
    if not is_admin(user_id):
        print("Error: User does not have admin privileges.")
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
        print("No product details provided to modify.")
        conn.close()
        return False

    query = f"UPDATE products SET {', '.join(updates)} WHERE product_id = ?"
    params.append(product_id)

    try:
        cursor.execute(query, params)
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
    """Removes a product from the database if the user is an admin."""
    if not is_admin(user_id):
        print("Error: User does not have admin privileges.")
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

def get_all_products():
    """Retrieves all products from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, name, description, price FROM products")
    products = cursor.fetchall()
    conn.close()
    return products

def display_products(products):
    """Displays a list of products."""
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

def setup_test_data():
    """Sets up some initial users and products for testing."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Add an admin user
    cursor.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('admin', 'password', 1))
    # Add a regular user
    cursor.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('user', 'password', 0))

    # Add some initial products
    cursor.execute("INSERT OR IGNORE INTO products (name, description, price) VALUES (?, ?, ?)", ('Laptop', 'Powerful laptop for work', 1200.00))
    cursor.execute("INSERT OR IGNORE INTO products (name, description, price) VALUES (?, ?, ?)", ('Mouse', 'Wireless ergonomic mouse', 25.00))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    setup_test_data()

    # --- Simulate User Login ---
    # In a real application, you would have a proper authentication system.
    # For testing, let's assume we have a logged-in user ID.
    admin_user_id = 1  # Assuming user with ID 1 is the admin
    regular_user_id = 2 # Assuming user with ID 2 is a regular user

    print("\n--- Testing Admin Functionality ---")
    print(f"\nLogged in as admin user (ID: {admin_user_id})")

    # Add a new product
    add_product(admin_user_id, 'Keyboard', 'Mechanical gaming keyboard', 75.00)

    # Modify an existing product
    modify_product(admin_user_id, 1, price=1250.00, description='High-performance laptop for professionals')

    # View all products
    all_products = get_all_products()
    display_products(all_products)

    # Remove a product
    remove_product(admin_user_id, 2)

    # View all products after removal
    all_products = get_all_products()
    display_products(all_products)

    print("\n--- Testing Regular User (Non-Admin) ---")
    print(f"\nLogged in as regular user (ID: {regular_user_id})")

    # Try to add a product as a regular user
    add_product(regular_user_id, 'Monitor', '27-inch 4K monitor', 300.00)

    # Try to modify a product as a regular user
    modify_product(regular_user_id, 3, price=320.00)

    # Try to remove a product as a regular user
    remove_product(regular_user_id, 3)

    # View all products (should be the same as after admin actions)
    all_products = get_all_products()
    display_products(all_products)