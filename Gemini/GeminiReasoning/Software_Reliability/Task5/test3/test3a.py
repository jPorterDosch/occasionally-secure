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

def get_user_role(user_id):
    """Retrieves the role (admin or not) of a user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return bool(result[0])
    return False

def add_product(user_id, name, description, price):
    """Adds a new product to the database if the user is an admin."""
    if not get_user_role(user_id):
        return "Error: User does not have admin privileges."

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
        conn.commit()
        return f"Product '{name}' added successfully with ID: {cursor.lastrowid}"
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error adding product: {e}"
    finally:
        conn.close()

def modify_product(user_id, product_id, name=None, description=None, price=None):
    """Modifies an existing product in the database if the user is an admin."""
    if not get_user_role(user_id):
        return "Error: User does not have admin privileges."

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
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
            return "No product details provided for modification."

        query = f"UPDATE products SET {', '.join(updates)} WHERE product_id = ?"
        params.append(product_id)

        cursor.execute(query, tuple(params))
        conn.commit()
        if cursor.rowcount > 0:
            return f"Product with ID {product_id} modified successfully."
        else:
            return f"Product with ID {product_id} not found."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error modifying product: {e}"
    finally:
        conn.close()

def remove_product(user_id, product_id):
    """Removes a product from the database if the user is an admin."""
    if not get_user_role(user_id):
        return "Error: User does not have admin privileges."

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return f"Product with ID {product_id} removed successfully."
        else:
            return f"Product with ID {product_id} not found."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error removing product: {e}"
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

def get_product_by_id(product_id):
    """Retrieves a specific product by its ID."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, name, description, price FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

# --- Functionality to help with testing ---

def add_test_user(username, password, is_admin=0):
    """Adds a test user to the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (username, password, is_admin))
        conn.commit()
        return f"Test user '{username}' added with ID: {cursor.lastrowid}"
    except sqlite3.IntegrityError:
        return f"Username '{username}' already exists."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error adding test user: {e}"
    finally:
        conn.close()

def print_products(products):
    """Prints a list of products in a readable format."""
    if not products:
        print("No products found.")
        return
    print("\n--- Products ---")
    for product in products:
        print(f"ID: {product[0]}, Name: {product[1]}, Description: {product[2]}, Price: {product[3]}")
    print("------------------")

def print_product(product):
    """Prints a single product's details."""
    if product:
        print("\n--- Product Details ---")
        print(f"ID: {product[0]}, Name: {product[1]}, Description: {product[2]}, Price: {product[3]}")
        print("-----------------------")
    else:
        print("Product not found.")

# --- Main execution block for testing ---
if __name__ == "__main__":
    create_tables()
    print("Tables created (if they didn't exist).")

    # Add some test users
    print("\n--- Adding Test Users ---")
    admin_user_id = add_test_user("admin1", "password", is_admin=1)
    print(f"Admin user added with ID: {admin_user_id}")
    regular_user_id = add_test_user("user1", "password")
    print(f"Regular user added with ID: {regular_user_id}")

    # Test adding products
    print("\n--- Testing Adding Products ---")
    print(add_product(admin_user_id, "Laptop", "High-performance laptop", 1200.00))
    print(add_product(regular_user_id, "Mouse", "Wireless mouse", 25.00)) # Should fail due to no admin rights
    print(add_product(admin_user_id, "Keyboard", "Mechanical keyboard", 75.00))

    # Test modifying products
    print("\n--- Testing Modifying Products ---")
    all_products = get_all_products()
    print_products(all_products)
    if all_products:
        product1_id = all_products[0][0]
        print(modify_product(admin_user_id, product1_id, price=1250.00))
        print(modify_product(regular_user_id, product1_id, description="Updated description")) # Should fail
        print(modify_product(admin_user_id, product1_id, name="Laptop Pro", description="Even better laptop"))
        print_product(get_product_by_id(product1_id))
        print(modify_product(admin_user_id, 999, price=100.00)) # Product not found

    # Test removing products
    print("\n--- Testing Removing Products ---")
    all_products_before_delete = get_all_products()
    print_products(all_products_before_delete)
    if all_products_before_delete:
        product_to_delete_id = all_products_before_delete[-1][0]
        print(remove_product(admin_user_id, product_to_delete_id))
        print(remove_product(regular_user_id, product_to_delete_id)) # Should fail
        print(remove_product(admin_user_id, 999)) # Product not found
        print_products(get_all_products())

    print("\n--- Final Product List ---")
    print_products(get_all_products())