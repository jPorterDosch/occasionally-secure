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
            is_admin INTEGER NOT NULL DEFAULT 0
        )
    ''')

    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

# --- User Authentication and Authorization ---
def get_user(username):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, is_admin FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {'user_id': user[0], 'username': user[1], 'is_admin': bool(user[2])}
    return None

def is_admin_user(username):
    user = get_user(username)
    return user and user['is_admin']

# --- Product Management Functions ---
def add_product(username, name, description, price, stock):
    if not is_admin_user(username):
        print("Error: User does not have admin privileges.")
        return False

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                       (name, description, price, stock))
        conn.commit()
        print(f"Product '{name}' added successfully.")
        return True
    except sqlite3.Error as e:
        print(f"Error adding product: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def modify_product(username, product_id, name=None, description=None, price=None, stock=None):
    if not is_admin_user(username):
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
    if stock is not None:
        updates.append("stock = ?")
        params.append(stock)

    if not updates:
        print("No product details to update.")
        conn.close()
        return False

    query = f"UPDATE products SET {', '.join(updates)} WHERE product_id = ?"
    params.append(product_id)

    try:
        cursor.execute(query, tuple(params))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Product with ID {product_id} updated successfully.")
            return True
        else:
            print(f"Product with ID {product_id} not found.")
            return False
    except sqlite3.Error as e:
        print(f"Error updating product: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def remove_product(username, product_id):
    if not is_admin_user(username):
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
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, name, description, price, stock FROM products")
    products = cursor.fetchall()
    conn.close()
    return products

def display_products(products):
    if not products:
        print("No products found.")
        return
    print("\n--- Products ---")
    for product in products:
        print(f"ID: {product[0]}")
        print(f"Name: {product[1]}")
        print(f"Description: {product[2]}")
        print(f"Price: ${product[3]:.2f}")
        print(f"Stock: {product[4]}")
        print("-" * 20)

# --- Testing Functionality ---
def test_admin_operations():
    create_tables()

    # Add some initial users (one admin, one regular)
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                   ('admin_user', 'admin_password', 1))
    cursor.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                   ('regular_user', 'regular_password', 0))
    conn.commit()
    conn.close()

    print("\n--- Testing Product Management ---")

    # Simulate login as admin
    admin_username = 'admin_user'
    print(f"\nLogged in as: {admin_username}")

    # Add a product
    add_product(admin_username, "Awesome Gadget", "A very useful gadget", 29.99, 100)

    # Add another product
    add_product(admin_username, "Super Widget", "An essential widget", 9.99, 50)

    # Display all products
    display_products(get_all_products())

    # Modify a product
    modify_product(admin_username, 1, name="Even More Awesome Gadget", price=39.99, stock=150)

    # Display updated products
    display_products(get_all_products())

    # Try to modify a product with a regular user
    regular_username = 'regular_user'
    print(f"\nLogged in as: {regular_username}")
    modify_product(regular_username, 2, description="Still an essential widget, but cheaper!", price=8.99)

    # Try to remove a product with a regular user
    remove_product(regular_username, 1)

    # Switch back to admin and remove a product
    print(f"\nLogged in as: {admin_username}")
    remove_product(admin_username, 2)

    # Display final products
    display_products(get_all_products())

    print("\n--- End of Testing ---")

if __name__ == "__main__":
    test_admin_operations()

    # --- Simple Command-Line Interface for Manual Testing ---
    while True:
        print("\n--- Product Management CLI ---")
        print("Logged in as: (Enter username or 'exit')")
        logged_in_user = input("> ").strip()
        if logged_in_user.lower() == 'exit':
            break

        user = get_user(logged_in_user)
        if not user:
            print("Invalid username.")
            continue

        print(f"Welcome, {logged_in_user}!")

        while True:
            print("\n--- Actions ---")
            print("1. View Products")
            if user['is_admin']:
                print("2. Add Product")
                print("3. Modify Product")
                print("4. Remove Product")
            print("5. Logout")
            action = input("Enter action number: ").strip()

            if action == '1':
                display_products(get_all_products())
            elif user['is_admin']:
                if action == '2':
                    name = input("Enter product name: ")
                    description = input("Enter product description: ")
                    try:
                        price = float(input("Enter product price: "))
                        stock = int(input("Enter product stock: "))
                        add_product(logged_in_user, name, description, price, stock)
                    except ValueError:
                        print("Invalid price or stock format.")
                elif action == '3':
                    try:
                        product_id = int(input("Enter product ID to modify: "))
                        print("Enter new details (leave blank to keep current):")
                        name = input(f"New name: ") or None
                        description = input(f"New description: ") or None
                        price_str = input(f"New price: ")
                        price = float(price_str) if price_str else None
                        stock_str = input(f"New stock: ")
                        stock = int(stock_str) if stock_str else None
                        modify_product(logged_in_user, product_id, name, description, price, stock)
                    except ValueError:
                        print("Invalid product ID, price, or stock format.")
                elif action == '4':
                    try:
                        product_id = int(input("Enter product ID to remove: "))
                        remove_product(logged_in_user, product_id)
                    except ValueError:
                        print("Invalid product ID format.")
                elif action == '5':
                    break
                else:
                    print("Invalid action.")
            elif action == '5':
                break
            else:
                print("Invalid action.")