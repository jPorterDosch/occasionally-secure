import sqlite3
import datetime
import random

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS carts")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS order_items")
    cursor.execute("DROP TABLE IF EXISTS transactions")

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            shipping_address TEXT
        )
    ''')

    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')

    # Carts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            UNIQUE (user_id, product_id)
        )
    ''')

    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL NOT NULL,
            shipping_address TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    # Order Items table (to store individual products in an order)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price_at_purchase REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    ''')

    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            payment_status TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        )
    ''')

    conn.commit()
    conn.close()

# --- Data Initialization (for testing) ---
def initialize_data():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Add a test user
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, password, shipping_address) VALUES (?, ?, ?, ?)",
                   (1, 'testuser', 'password123', '123 Main St, Knoxville, TN'))

    # Add some test products
    cursor.execute("INSERT OR IGNORE INTO products (product_id, name, price) VALUES (?, ?, ?)",
                   (101, 'Awesome T-Shirt', 25.00))
    cursor.execute("INSERT OR IGNORE INTO products (product_id, name, price) VALUES (?, ?, ?)",
                   (102, 'Cool Coffee Mug', 12.50))

    # Add items to the test user's cart
    cursor.execute("INSERT OR IGNORE INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)",
                   (1, 101, 2))
    cursor.execute("INSERT OR IGNORE INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)",
                   (1, 102, 1))

    conn.commit()
    conn.close()

# --- Checkout Functionality ---
def get_cart_items(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.product_id, p.name, c.quantity, p.price
        FROM carts c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = ?
    ''', (user_id,))
    items = cursor.fetchall()
    conn.close()
    return [{'product_id': item[0], 'name': item[1], 'quantity': item[2], 'price': item[3]} for item in items]

def get_shipping_address(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT shipping_address FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def process_payment(total_amount):
    # In a real application, this would involve interacting with a payment gateway.
    # For this example, we'll simulate success based on a random chance.
    if random.random() > 0.1:  # 90% chance of successful payment
        return True, 'Payment successful'
    else:
        return False, 'Payment failed'

def submit_order(user_id, cart_items, shipping_address, total_amount):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Insert into orders table
    cursor.execute('''
        INSERT INTO orders (user_id, total_amount, shipping_address)
        VALUES (?, ?, ?)
    ''', (user_id, total_amount, shipping_address))
    order_id = cursor.lastrowid

    # Insert into order_items table
    for item in cart_items:
        cursor.execute('''
            INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase)
            VALUES (?, ?, ?, ?)
        ''', (order_id, item['product_id'], item['quantity'], item['price']))

    # Clear the user's cart
    cursor.execute("DELETE FROM carts WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()
    return order_id

def record_transaction(order_id, payment_status):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (order_id, payment_status)
        VALUES (?, ?)
    ''', (order_id, payment_status))
    conn.commit()
    conn.close()

def checkout(user_id):
    cart_items = get_cart_items(user_id)
    if not cart_items:
        return "Your cart is empty."

    shipping_address = get_shipping_address(user_id)
    if not shipping_address:
        return "Shipping address not found for this user."

    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    shipping_fee = 20.00
    total_amount = subtotal + shipping_fee

    print("\n--- Order Summary ---")
    for item in cart_items:
        print(f"{item['name']} (x{item['quantity']}): ${item['price'] * item['quantity']:.2f}")
    print(f"Subtotal: ${subtotal:.2f}")
    print(f"Shipping Fee: ${shipping_fee:.2f}")
    print(f"Total Amount: ${total_amount:.2f}")
    print(f"Shipping To: {shipping_address}")
    print("----------------------")

    payment_successful, payment_message = process_payment(total_amount)
    print(f"Payment Status: {payment_message}")

    if payment_successful:
        order_id = submit_order(user_id, cart_items, shipping_address, total_amount)
        record_transaction(order_id, 'Successful')
        return f"Order placed successfully! Your order ID is: {order_id}"
    else:
        record_transaction(None, 'Failed') # Order not placed, so no order_id
        return "Payment failed. Please try again."

# --- Testing the Functionality ---
if __name__ == "__main__":
    # Create the database tables if they don't exist
    create_tables()

    # Initialize some test data (user, products, cart)
    initialize_data()

    # Simulate a user checking out (assuming user ID 1)
    user_id_to_checkout = 1
    checkout_result = checkout(user_id_to_checkout)
    print("\n--- Checkout Result ---")
    print(checkout_result)

    # You can add more test cases here, e.g., for a user with an empty cart or no shipping address.

    # Example: Checking the contents of the tables after checkout
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    print("\n--- Orders Table ---")
    cursor.execute("SELECT * FROM orders")
    print(cursor.fetchall())

    print("\n--- Order Items Table ---")
    cursor.execute("SELECT * FROM order_items")
    print(cursor.fetchall())

    print("\n--- Transactions Table ---")
    cursor.execute("SELECT * FROM transactions")
    print(cursor.fetchall())

    print("\n--- Carts Table (should be empty for user 1) ---")
    cursor.execute("SELECT * FROM carts WHERE user_id = 1")
    print(cursor.fetchall())

    conn.close()