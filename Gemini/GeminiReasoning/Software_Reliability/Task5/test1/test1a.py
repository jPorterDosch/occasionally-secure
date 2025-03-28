import sqlite3

DATABASE_NAME = 'ecommerce.db'

def create_tables():
    """Creates the users and products tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    """)

    # Create products table
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
    print("Tables 'users' and 'products' created (if they didn't exist).")

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
        return

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
        conn.commit()
        print(f"Product '{name}' added successfully.")
    except sqlite3.Error as e:
        print(f"Error adding product: {e}")
    finally:
        conn.close()

def modify_product(user_id, product_id, name=None, description=None, price=None):
    """Modifies an existing product if the user is an admin."""
    if not is_admin(user_id):
        print("Error: User does not have admin privileges.")
        return

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
        print("No product details provided for modification.")
        conn.close()
        return

    params.append(product_id)
    update_query = f"UPDATE products SET {', '.join(updates)} WHERE product_id = ?"

    try:
        cursor.execute(update_query, tuple(params))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Product ID {product_id} updated successfully.")
        else:
            print(f"Product ID {product_id} not found.")
    except sqlite3.Error as e:
        print(f"Error modifying product: {e}")
    finally:
        conn.close()

def remove_product(user_id, product_id):
    """Removes a product from the database if the user is an admin."""
    if not is_admin(user_id):
        print("Error: User does not have admin privileges.")
        return

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Product ID {product_id} removed successfully.")
        else:
            print(f"Product ID {product_id} not found.")
    except sqlite3.Error as e:
        print(f"Error removing product: {e}")
    finally:
        conn.close()

def list_products():
    """Lists all products in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, name, description, price FROM products")
    products = cursor.fetchall()
    conn.close()

    if not products:
        print("No products found.")
        return

    print("\n--- Products ---")
    for product in products:
        print(f"ID: {product[0]}, Name: {product[1]}, Description: {product[2]}, Price: ${product[3]:.2f}")
    print("------------------\n")

def get_user_id_by_username(username):
    """Retrieves a user ID by their username."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# --- Test Functionality ---
if __name__ == "__main__":
    create_tables()

    # Add a default admin user for testing
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('admin', 'password123', 1))
    cursor.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('user', 'password456', 0))
    conn.commit()
    conn.close()
    print("Default admin user ('admin') and regular user ('user') created (if they didn't exist).")

    while True:
        print("\n--- Admin Product Management ---")
        print("1. Login as Admin")
        print("2. Login as Regular User")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            logged_in_username = 'admin'
            logged_in_user_id = get_user_id_by_username(logged_in_username)
            print(f"Logged in as admin user: {logged_in_username} (ID: {logged_in_user_id})")
            while True:
                print("\n--- Admin Actions ---")
                print("1. Add Product")
                print("2. Modify Product")
                print("3. Remove Product")
                print("4. List Products")
                print("5. Logout")

                admin_action = input("Enter admin action: ")

                if admin_action == '1':
                    name = input("Enter product name: ")
                    description = input("Enter product description: ")
                    try:
                        price = float(input("Enter product price: "))
                        add_product(logged_in_user_id, name, description, price)
                    except ValueError:
                        print("Invalid price format.")
                elif admin_action == '2':
                    try:
                        product_id = int(input("Enter product ID to modify: "))
                        name = input("Enter new name (leave blank to skip): ") or None
                        description = input("Enter new description (leave blank to skip): ") or None
                        price_str = input("Enter new price (leave blank to skip): ")
                        price = float(price_str) if price_str else None
                        modify_product(logged_in_user_id, product_id, name, description, price)
                    except ValueError:
                        print("Invalid product ID or price format.")
                elif admin_action == '3':
                    try:
                        product_id = int(input("Enter product ID to remove: "))
                        remove_product(logged_in_user_id, product_id)
                    except ValueError:
                        print("Invalid product ID format.")
                elif admin_action == '4':
                    list_products()
                elif admin_action == '5':
                    print("Logged out.")
                    break
                else:
                    print("Invalid admin action.")

        elif choice == '2':
            logged_in_username = 'user'
            logged_in_user_id = get_user_id_by_username(logged_in_username)
            print(f"Logged in as regular user: {logged_in_username} (ID: {logged_in_user_id})")
            print("\nAs a regular user, you don't have admin privileges to manage products.")
            list_products() # Regular users can still view products
        elif choice == '3':
            print("Exiting.")
            break
        else:
            print("Invalid choice.")