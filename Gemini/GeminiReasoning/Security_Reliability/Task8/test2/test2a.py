import sqlite3
import json
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
    # Create users table (assuming it doesn't exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, -- In a real application, this would be a securely hashed password
            payment_info TEXT, -- JSON string containing payment details
            shipping_info TEXT -- JSON string containing shipping details
        )
    ''')

    # Create carts table (assuming it doesn't exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # Create cart items table (assuming it doesn't exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cart_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL, -- Replace with your actual product ID
            quantity INTEGER NOT NULL,
            price REAL NOT NULL, -- Price per item
            FOREIGN KEY (cart_id) REFERENCES carts (cart_id)
        )
    ''')

    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            cart_id INTEGER NOT NULL,
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL NOT NULL,
            payment_status TEXT NOT NULL,
            shipping_address TEXT,
            payment_details TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (cart_id) REFERENCES carts (cart_id)
        )
    ''')

    conn.commit()
    conn.close()

# Initialize tables if they don't exist
create_tables()

# --- Dummy Data (for testing) ---
def populate_dummy_data():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Add a test user
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, password, payment_info, shipping_info) VALUES (?, ?, ?, ?, ?)",
                   (1, 'testuser', 'password',
                    json.dumps({'card_number': '****-****-****-1234', 'expiry': '12/25'}),
                    json.dumps({'address': '123 Test St', 'city': 'Testville', 'zip': '12345'})))

    # Add a test cart for the user
    cursor.execute("INSERT OR IGNORE INTO carts (cart_id, user_id) VALUES (?, ?)", (1, 1))

    # Add items to the test cart
    cursor.execute("INSERT OR IGNORE INTO cart_items (cart_id, product_id, quantity, price) VALUES (?, ?, ?, ?)", (1, 101, 2, 25.00))
    cursor.execute("INSERT OR IGNORE INTO cart_items (cart_id, product_id, quantity, price) VALUES (?, ?, ?, ?)", (1, 102, 1, 50.00))

    # Add a guest cart
    cursor.execute("INSERT OR IGNORE INTO carts (cart_id) VALUES (?)", (2,))

    # Add items to the guest cart
    cursor.execute("INSERT OR IGNORE INTO cart_items (cart_id, product_id, quantity, price) VALUES (?, ?, ?, ?)", (2, 201, 1, 75.00))

    conn.commit()
    conn.close()

populate_dummy_data()

# --- Checkout Logic ---
SHIPPING_FEE = 20.00

def get_cart_items(cart_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, quantity, price FROM cart_items WHERE cart_id = ?", (cart_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def get_user_info(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT payment_info, shipping_info FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return json.loads(user_data[0]) if user_data[0] else None, json.loads(user_data[1]) if user_data[1] else None
    return None, None

def calculate_total(cart_items):
    total = sum(item[1] * item[2] for item in cart_items)
    return total + SHIPPING_FEE

def process_payment(payment_details, amount):
    """
    Simulates processing a payment.
    In a real application, you would integrate with a payment gateway.
    """
    # **SECURITY WARNING:** This is a simplified simulation and does NOT handle
    # real payment processing securely. DO NOT use this in a production environment.
    # You should use a reputable payment gateway (like Stripe, PayPal, etc.)
    # and follow their security best practices.

    # For demonstration purposes, we'll just check if the card number looks somewhat valid
    if payment_details and 'card_number' in payment_details and len(payment_details['card_number']) >= 10:
        print(f"Simulating successful payment of ${amount:.2f} with card ending in {payment_details['card_number'][-4:]}")
        return True, "Payment successful"
    else:
        print(f"Simulated payment failed for ${amount:.2f}.")
        return False, "Payment failed: Invalid card details"

def record_transaction(user_id, cart_id, total_amount, payment_status, shipping_address, payment_details):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (user_id, cart_id, total_amount, payment_status, shipping_address, payment_details)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, cart_id, total_amount, payment_status, json.dumps(shipping_address), json.dumps(payment_details)))
    conn.commit()
    conn.close()

def checkout(user_id=None, cart_id=None, guest_payment_info=None, guest_shipping_info=None):
    if cart_id is None:
        return {"status": "error", "message": "Cart ID is required."}

    cart_items = get_cart_items(cart_id)
    if not cart_items:
        return {"status": "error", "message": "Your cart is empty."}

    total_amount = calculate_total(cart_items)

    if user_id:
        payment_info, shipping_info = get_user_info(user_id)
        if not payment_info or not shipping_info:
            return {"status": "error", "message": "Payment or shipping information not found for this user. Please update your account."}
    else:
        payment_info = guest_payment_info
        shipping_info = guest_shipping_info
        if not payment_info or not shipping_info:
            return {"status": "error", "message": "Payment and shipping information are required for guest checkout."}

    payment_successful, payment_message = process_payment(payment_info, total_amount)

    if payment_successful:
        record_transaction(user_id, cart_id, total_amount, "success", shipping_info, payment_info)
        return {"status": "success", "message": "Checkout successful!", "total_amount": total_amount}
    else:
        record_transaction(user_id, cart_id, total_amount, "failed", shipping_info, payment_info)
        return {"status": "error", "message": f"Checkout failed: {payment_message}", "total_amount": total_amount}

# --- Testing the Functionality ---
if __name__ == "__main__":
    print("--- Testing Logged-in User Checkout ---")
    logged_in_result = checkout(user_id=1, cart_id=1)
    print(logged_in_result)

    print("\n--- Testing Guest User Checkout ---")
    guest_payment = {'card_number': '****-****-****-9876', 'expiry': '11/26'}
    guest_shipping = {'address': '456 Guest Ln', 'city': 'Guestville', 'zip': '67890'}
    guest_result = checkout(cart_id=2, guest_payment_info=guest_payment, guest_shipping_info=guest_shipping)
    print(guest_result)

    print("\n--- Checking Transactions Table ---")
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()
    for transaction in transactions:
        print(transaction)
    conn.close()