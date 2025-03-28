import sqlite3
import uuid
from datetime import datetime

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS carts")
    cursor.execute("DROP TABLE IF EXISTS cart_items")
    cursor.execute("DROP TABLE IF EXISTS transactions")

    # Users table (assuming it already exists)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            payment_info TEXT, -- In a real system, store a reference to a secure payment gateway or use tokenization
            shipping_address TEXT
        )
    """)

    # Carts table (assuming it already exists)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)

    # Cart items table (assuming it already exists)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cart_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (cart_id) REFERENCES carts (cart_id)
        )
    """)

    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            user_id INTEGER,
            cart_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            payment_status TEXT NOT NULL,
            shipping_address TEXT,
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (cart_id) REFERENCES carts (cart_id)
        )
    """)

    conn.commit()
    conn.close()

create_tables()

# --- Data Simulation (for testing) ---
def populate_test_data():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Add a test user
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, password, payment_info, shipping_address) VALUES (?, ?, ?, ?, ?)",
                   (1, 'testuser', 'password123', '****-****-****-1234', '123 Test St, Test City'))

    # Add a test cart for the user
    cursor.execute("INSERT OR IGNORE INTO carts (cart_id, user_id) VALUES (?, ?)", (1, 1))

    # Add items to the cart
    cursor.execute("INSERT OR IGNORE INTO cart_items (cart_id, product_name, price, quantity) VALUES (?, ?, ?, ?)",
                   (1, 'Test Product 1', 25.00, 1))
    cursor.execute("INSERT OR IGNORE INTO cart_items (cart_id, product_name, price, quantity) VALUES (?, ?, ?, ?)",
                   (1, 'Test Product 2', 15.50, 2))

    conn.commit()
    conn.close()

populate_test_data()

# --- Checkout Functionality ---
SHIPPING_FEE = 20.00

def get_cart_items(cart_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, price, quantity FROM cart_items WHERE cart_id=?", (cart_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def get_user_info(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT payment_info, shipping_address FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return {'payment_info': user_data[0], 'shipping_address': user_data[1]}
    return None

def process_payment(payment_info, amount):
    """
    Simulates processing a payment.
    In a real application, this would involve interaction with a payment gateway.
    For security, never store raw credit card information directly.
    Consider using tokenization provided by payment gateways.
    """
    print(f"Processing payment of ${amount:.2f} with payment info: {payment_info[-4:].rjust(len(payment_info), '*')}")
    # In a real scenario, you would integrate with a payment gateway here
    payment_successful = True  # Simulate successful payment
    return payment_successful

def record_transaction(user_id, cart_id, total_amount, shipping_address, payment_status):
    transaction_id = str(uuid.uuid4())
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (transaction_id, user_id, cart_id, total_amount, payment_status, shipping_address)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (transaction_id, user_id, cart_id, total_amount, payment_status, shipping_address))
    conn.commit()
    conn.close()
    return transaction_id

def checkout(user_id=None, cart_id=None, guest_payment_info=None, guest_shipping_address=None):
    if cart_id is None:
        return {"success": False, "message": "Cart ID is required."}

    cart_items = get_cart_items(cart_id)
    if not cart_items:
        return {"success": False, "message": "Your cart is empty."}

    subtotal = sum(item[1] * item[2] for item in cart_items)
    total_amount = subtotal + SHIPPING_FEE

    if user_id:
        user_info = get_user_info(user_id)
        if not user_info:
            return {"success": False, "message": "User not found."}
        payment_info = user_info['payment_info']
        shipping_address = user_info['shipping_address']
        print(f"Logged-in user found. Using stored payment and shipping information.")
    else:
        if not guest_payment_info or not guest_shipping_address:
            return {"success": False, "message": "Payment and shipping information are required for guest checkout."}
        payment_info = guest_payment_info
        shipping_address = guest_shipping_address
        print("Guest checkout initiated.")

    print(f"Items in cart:")
    for name, price, quantity in cart_items:
        print(f"- {quantity} x {name}: ${price:.2f}")
    print(f"Subtotal: ${subtotal:.2f}")
    print(f"Shipping Fee: ${SHIPPING_FEE:.2f}")
    print(f"Total Amount: ${total_amount:.2f}")

    payment_successful = process_payment(payment_info, total_amount)

    if payment_successful:
        transaction_id = record_transaction(user_id, cart_id, total_amount, shipping_address, "SUCCESSFUL")
        return {"success": True, "message": f"Checkout successful! Your transaction ID is: {transaction_id}", "transaction_id": transaction_id}
    else:
        record_transaction(user_id, cart_id, total_amount, shipping_address, "FAILED")
        return {"success": False, "message": "Payment failed. Please check your payment information."}

# --- Testing the Functionality ---
def test_checkout():
    print("\n--- Testing Logged-in User Checkout ---")
    # Assuming user with ID 1 and cart with ID 1 exists (created by populate_test_data)
    result_logged_in = checkout(user_id=1, cart_id=1)
    print(result_logged_in)

    print("\n--- Testing Guest User Checkout ---")
    # Assuming a guest user with a hypothetical cart ID 2
    # You would need to create a cart with ID 2 and add items to it for a real test
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO carts (cart_id) VALUES (?)", (2,))
    cursor.execute("INSERT OR IGNORE INTO cart_items (cart_id, product_name, price, quantity) VALUES (?, ?, ?, ?)",
                   (2, 'Guest Product', 10.00, 3))
    conn.commit()
    conn.close()

    result_guest = checkout(cart_id=2, guest_payment_info="5555-5555-5555-5555", guest_shipping_address="456 Guest Ln, Guest Town")
    print(result_guest)

if __name__ == "__main__":
    test_checkout()

    # You can also manually test with different scenarios:
    # result_empty_cart = checkout(user_id=1, cart_id=999) # Assuming cart 999 doesn't exist or is empty
    # print("\n--- Testing Empty Cart ---")
    # print(result_empty_cart)