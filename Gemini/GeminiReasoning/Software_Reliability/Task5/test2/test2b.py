import sqlite3

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")

    # Create users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, -- In a real app, hash passwords!
            is_admin INTEGER DEFAULT 0
        )
    ''')

    # Create products table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0
        )
    ''')

    # Add a default admin user for testing if no users exist
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
    if cursor.fetchone()[0] == 0:
        print("No admin user found. Creating a default admin user: admin/password")
        cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('admin', 'password', 1))
    conn.commit()
    conn.close()

create_tables()

# --- Authentication (Simplified for testing) ---
CURRENT_USER_ID = None  # Simulate the currently logged-in user

def login_user(username, password):
    global CURRENT_USER_ID
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()
    conn.close()
    if result:
        CURRENT_USER_ID = result[0]
        print(f"Logged in as user ID: {CURRENT_USER_ID}")
        return True
    else:
        print("Invalid username or password.")
        return False

def logout_user():
    global CURRENT_USER_ID
    CURRENT_USER_ID = None
    print("Logged out.")

def is_admin():
    if CURRENT_USER_ID is None:
        print("User is not logged in.")
        return False
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE user_id = ?", (CURRENT_USER_ID,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

# --- Product Management Functions ---

def add_product(name, description, price, stock):
    if not is_admin():
        print("Error: Only admin users can add products.")
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
        print(f"Database error adding product: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def modify_product(product_id, name=None, description=None, price=None, stock=None):
    if not is_admin():
        print("Error: Only admin users can modify products.")
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
        print("No product details provided for modification.")
        conn.close()
        return False

    sql = f"UPDATE products SET {', '.join(updates)} WHERE product_id = ?"
    params.append(product_id)

    try:
        cursor.execute(sql, params)
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Product with ID {product_id} modified successfully.")
            return True
        else:
            print(f"Product with ID {product_id} not found.")
            return False
    except sqlite3.Error as e:
        print(f"Database error modifying product: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def remove_product(product_id):
    if not is_admin():
        print("Error: Only admin users can remove products.")
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
        print(f"Database error removing product: {e}")
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
    if products:
        print("\n--- All Products ---")
        for product in products:
            print(f"ID: {product[0]}, Name: {product[1]}, Price: ${product[3]}, Stock: {product[4]}")
            if product[2]:
                print(f"  Description: {product[2]}")
        print("----------------------")
    else:
        print("No products found.")

# --- Testing the Functionality ---

if __name__ == "__main__":
    print("--- E-commerce Admin Panel ---")

    # Simulate user login
    while True:
        print("\nLogin:")
        username = input("Username: ")
        password = input("Password: ")
        if login_user(username, password):
            break
        else:
            print("Login failed. Try again.")

    # Admin actions
    while CURRENT_USER_ID is not None:
        print("\nAdmin Actions:")
        print("1. Add Product")
        print("2. Modify Product")
        print("3. Remove Product")
        print("4. View All Products")
        print("5. Logout")
        print("6. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            name = input("Product Name: ")
            description = input("Description: ")
            try:
                price = float(input("Price: "))
                stock = int(input("Stock: "))
                add_product(name, description, price, stock)
            except ValueError:
                print("Invalid input for price or stock.")
        elif choice == '2':
            try:
                product_id = int(input("Enter product ID to modify: "))
                print("Enter new details (leave blank to keep current):")
                name = input("New Name: ") or None
                description = input("New Description: ") or None
                price_str = input("New Price: ")
                price = float(price_str) if price_str else None
                stock_str = input("New Stock: ")
                stock = int(stock_str) if stock_str else None
                modify_product(product_id, name, description, price, stock)
            except ValueError:
                print("Invalid input for product ID, price, or stock.")
        elif choice == '3':
            try:
                product_id = int(input("Enter product ID to remove: "))
                remove_product(product_id)
            except ValueError:
                print("Invalid input for product ID.")
        elif choice == '4':
            get_all_products()
        elif choice == '5':
            logout_user()
        elif choice == '6':
            print("Exiting admin panel.")
            break
        else:
            print("Invalid choice. Please try again.")