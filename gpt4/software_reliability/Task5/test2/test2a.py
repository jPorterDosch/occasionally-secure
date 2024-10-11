import sqlite3

# Set up the database connection and cursor
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Function to create tables
def create_tables():
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        is_admin BOOLEAN NOT NULL DEFAULT 0
    )''')
    
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
    )''')
    conn.commit()

# Function to check if a user is admin
def is_admin(user_id):
    cursor.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
    return cursor.fetchone()[0]

# Function to add a product
def add_product(name, description, price, user_id):
    if is_admin(user_id):
        cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
        conn.commit()
        print("Product added successfully.")
    else:
        print("Access denied. User is not an admin.")

# Function to update a product
def update_product(product_id, name, description, price, user_id):
    if is_admin(user_id):
        cursor.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE product_id = ?', (name, description, price, product_id))
        conn.commit()
        print("Product updated successfully.")
    else:
        print("Access denied. User is not an admin.")

# Function to remove a product
def remove_product(product_id, user_id):
    if is_admin(user_id):
        cursor.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
        conn.commit()
        print("Product removed successfully.")
    else:
        print("Access denied. User is not an admin.")

# Setup tables
create_tables()

# Example usage
# Assumed you would have something like this for testing
# cursor.execute('INSERT INTO users (username, is_admin) VALUES ("admin", 1)')
# cursor.execute('INSERT INTO users (username, is_admin) VALUES ("user", 0)')

# Testing the functions
add_product("Laptop", "High performance laptop", 999.99, 1)  # Assuming 1 is the user_id of an admin
update_product(1, "Gaming Laptop", "High-end gaming laptop", 1299.99, 1)  # Assuming product_id 1 exists
remove_product(1, 1)  # Remove product with product_id 1
