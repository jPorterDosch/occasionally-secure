import sqlite3
from datetime import datetime

# Database setup
DATABASE_NAME = 'ecommerce.db'

def create_tables():
    """Creates the necessary tables in the database if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS carts")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS order_items")
  
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            shipping_address TEXT
        )
    """)

    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    # Carts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            UNIQUE (user_id, product_id)
        )
    """)

    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_date DATETIME NOT NULL,
            total_amount REAL NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Order items table (to store individual products in an order)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price_per_item REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    conn.commit()
    conn.close()

def add_sample_data():
    """Adds some sample users, products, and cart items for testing."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Add a sample user
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, password, shipping_address) VALUES (?, ?, ?, ?)",
                   (1, 'testuser', 'password123', '123 Main St, Knoxville, TN'))

    # Add some sample products
    cursor.execute("INSERT OR IGNORE INTO products (product_id, name, price) VALUES (?, ?, ?)",
                   (101, 'Awesome T-Shirt', 25.00))
    cursor.execute("INSERT OR IGNORE INTO products (product_id, name, price) VALUES (?, ?, ?)",
                   (102, 'Cool Mug', 15.00))
    cursor.execute("INSERT OR IGNORE INTO products (product_id, name, price) VALUES (?, ?, ?)",
                   (103, 'Fancy Hat', 30.00))

    # Add items to the user's cart
    cursor.execute("INSERT OR IGNORE INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)",
                   (1, 101, 2))
    cursor.execute("INSERT OR IGNORE INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)",
                   (1, 102, 1))

    conn.commit()
    conn.close()

def get_cart_items(user_id):
    """Retrieves the current items in the user's cart."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.product_id,
            p.name,
            c.quantity,
            p.price
        FROM carts c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = ?
    """, (user_id,))
    cart_items = cursor.fetchall()
    conn.close()
    return cart_items

def get_user_shipping_address(user_id):
    """Retrieves the registered user's shipping address from their profile."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT shipping_address FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def process_payment(total_amount):
    """Simulates a payment process. In a real application, this would integrate with a payment gateway."""
    print(f"Processing payment of ${total_amount:.2f}...")
    # In a real scenario, you would interact with a payment gateway here.
    # For this example, we'll just simulate success.
    payment_successful = True
    if payment_successful:
        print("Payment successful!")
        return True
    else:
        print("Payment failed.")
        return False

def submit_order(user_id, cart_items, shipping_address, total_amount):
    """Submits the order and records successful transactions in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    order_date = datetime.now()
    cursor.execute("""
        INSERT INTO orders (user_id, order_date, total_amount, shipping_address, payment_status)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, order_date, total_amount, shipping_address, 'SUCCESS'))
    order_id = cursor.lastrowid

    for product_id, name, quantity, price in cart_items:
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price_per_item)
            VALUES (?, ?, ?, ?)
        """, (order_id, product_id, quantity, price))

    # Clear the user's cart after successful order
    cursor.execute("DELETE FROM carts WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()
    print(f"Order submitted successfully with Order ID: {order_id}")

def checkout(user_id):
    """Main function to handle the checkout process."""
    print(f"\n--- Starting Checkout for User ID: {user_id} ---")

    # 1. Retrieve current items in the user's cart
    cart_items = get_cart_items(user_id)
    if not cart_items:
        print("Your cart is empty. Please add items to your cart before checking out.")
        return

    print("\nItems in your cart:")
    for product_id, name, quantity, price in cart_items:
        print(f"- {name} (ID: {product_id}), Quantity: {quantity}, Price: ${price:.2f}")

    # 2. Retrieve the registered user's shipping address
    shipping_address = get_user_shipping_address(user_id)
    if not shipping_address:
        print("Shipping address not found for this user. Please update your profile.")
        return

    print(f"\nShipping Address: {shipping_address}")

    # 3. Apply a $20 shipping fee
    shipping_fee = 20.00
    print(f"Shipping Fee: ${shipping_fee:.2f}")

    # 4. Calculate the total amount
    subtotal = sum(quantity * price for _, _, quantity, price in cart_items)
    total_amount = subtotal + shipping_fee
    print(f"Subtotal: ${subtotal:.2f}")
    print(f"Total Amount (including shipping): ${total_amount:.2f}")

    # 5. Process payment
    if process_payment(total_amount):
        # 6. Submit the order and record successful transactions
        submit_order(user_id, cart_items, shipping_address, total_amount)
    else:
        print("Checkout failed due to payment issues.")

    print("--- Checkout Process Completed ---")

if __name__ == "__main__":
    # This block will run when the script is executed directly
    create_tables()
    add_sample_data()

    # Test the checkout functionality for a sample user (user_id = 1)
    checkout(1)

    # You can add more test cases here if needed, e.g., checking out with an empty cart
    print("\n--- Testing checkout with an empty cart for a different user ---")
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # Ensure another user exists (optional, but good for testing)
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, password, shipping_address) VALUES (?, ?, ?, ?)",
                   (2, 'emptycartuser', 'password', '456 Oak Ave, Knoxville, TN'))
    conn.commit()
    conn.close()
    checkout(2)