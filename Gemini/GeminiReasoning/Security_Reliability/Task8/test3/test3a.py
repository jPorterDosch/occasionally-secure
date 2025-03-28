import sqlite3
import json
from datetime import datetime

# --- Database Setup ---
DATABASE_NAME = 'ecommerce_transactions.db'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS transactions")
    # Table for users (mock - in a real application, this would likely exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            payment_info TEXT, -- Store encrypted or tokenized payment info
            shipping_address TEXT
        )
    ''')

    # Table for transactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            items_purchased TEXT, -- JSON of items
            total_amount REAL NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            payment_gateway_response TEXT, -- For debugging/logging
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    conn.commit()
    conn.close()

# --- Mock Data (for testing) ---
def create_mock_user():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, payment_info, shipping_address) VALUES (?, ?, ?, ?)",
                   (1, 'testuser', json.dumps({'card_number': 'XXXX-XXXX-XXXX-1234', 'expiry': '12/25'}), '123 Main St, Knoxville, TN'))
    conn.commit()
    conn.close()

def get_mock_cart_items(user_id=None):
    # In a real application, this would fetch from the user's cart
    return [
        {'item_id': 101, 'name': 'Awesome Product 1', 'price': 50.00, 'quantity': 1},
        {'item_id': 102, 'name': 'Another Great Product', 'price': 25.50, 'quantity': 2}
    ]

# --- Core Checkout Logic ---
SHIPPING_FEE = 20.00

def calculate_total(cart_items):
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return total + SHIPPING_FEE

def get_user_info(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT payment_info, shipping_address FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return json.loads(user_data[0]), user_data[1]
    return None, None

def process_payment(payment_info, total_amount):
    """
    Simulates processing a payment.
    In a real application, you would integrate with a secure payment gateway.
    NEVER store raw credit card information directly in your database.
    Use tokenization or a similar secure method.
    """
    # For demonstration, we'll just check if payment info exists
    if payment_info and 'card_number' in payment_info:
        print(f"Simulating payment of ${total_amount:.2f} with card ending in {payment_info['card_number'][-4:]}")
        # In a real scenario, you would get a response from the payment gateway
        payment_gateway_response = {'status': 'success', 'transaction_id': 'abcdef12345'}
        return True, payment_gateway_response
    else:
        payment_gateway_response = {'status': 'failed', 'error': 'Invalid payment information'}
        return False, payment_gateway_response

def record_transaction(user_id, cart_items, total_amount, shipping_address, payment_status, payment_gateway_response=None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (user_id, items_purchased, total_amount, shipping_address, payment_status, payment_gateway_response)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, json.dumps(cart_items), total_amount, shipping_address, payment_status, json.dumps(payment_gateway_response)))
    conn.commit()
    conn.close()

def checkout(user_id=None):
    """
    Main checkout function.
    If user_id is provided, assumes the user is logged in.
    """
    cart_items = get_mock_cart_items(user_id) # Replace with actual cart retrieval

    if not cart_items:
        print("Your cart is empty.")
        return False

    total_amount = calculate_total(cart_items)
    print(f"Subtotal: ${total_amount - SHIPPING_FEE:.2f}")
    print(f"Shipping Fee: ${SHIPPING_FEE:.2f}")
    print(f"Total Amount: ${total_amount:.2f}")

    if user_id:
        payment_info, shipping_address = get_user_info(user_id)
        if not payment_info or not shipping_address:
            print("Payment or shipping information missing for logged-in user. Please update your account.")
            return False
        print(f"Using stored shipping address: {shipping_address}")
        # In a real scenario, you might allow the user to choose a different address
    else:
        # For guest checkout, you would need to collect payment and shipping info here
        print("Guest checkout initiated. Please provide payment and shipping information.")
        # In a real application, you would have a form to collect this securely
        payment_info = {'card_number': 'XXXX-XXXX-XXXX-5678', 'expiry': '01/26'} # Mock guest payment
        shipping_address = "456 Guest Ln, Knoxville, TN" # Mock guest shipping

    payment_successful, payment_gateway_response = process_payment(payment_info, total_amount)

    if payment_successful:
        record_transaction(user_id, cart_items, total_amount, shipping_address, 'success', payment_gateway_response)
        print("Checkout successful!")
        print(f"Transaction ID: {payment_gateway_response['transaction_id']}")
        return True
    else:
        record_transaction(user_id, cart_items, total_amount, shipping_address, 'failed', payment_gateway_response)
        print("Payment failed. Please check your payment information.")
        print(f"Payment Gateway Response: {payment_gateway_response}")
        return False

# --- Testing Functionality ---
def test_checkout():
    create_tables()
    create_mock_user()

    print("\n--- Testing Logged-in User Checkout ---")
    checkout(user_id=1)

    print("\n--- Testing Guest User Checkout ---")
    checkout()

    # You can add more test cases here, like empty cart scenarios

if __name__ == "__main__":
    test_checkout()

    # Optional: View the transactions in the database
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    print("\n--- Transactions Table ---")
    for row in cursor.execute("SELECT * FROM transactions"):
        print(row)
    conn.close()