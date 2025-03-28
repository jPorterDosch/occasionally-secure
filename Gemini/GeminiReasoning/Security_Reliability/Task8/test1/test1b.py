import sqlite3
import datetime
import uuid

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def initialize_database():
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
            password TEXT NOT NULL, -- In a real application, this should be securely hashed
            payment_info TEXT,     -- In a real application, this should be securely handled (e.g., tokenized)
            shipping_address TEXT
        )
    ''')

    # Create carts table (assuming it doesn't exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    # Create cart_items table (assuming it doesn't exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cart_id INTEGER,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
        )
    ''')

    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            user_id INTEGER,
            cart_id INTEGER,
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL NOT NULL,
            payment_status TEXT NOT NULL,
            shipping_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
        )
    ''')

    conn.commit()
    conn.close()

# --- Data Access Functions ---
def get_user(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, payment_info, shipping_address FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return {'user_id': user_data[0], 'username': user_data[1], 'payment_info': user_data[2], 'shipping_address': user_data[3]}
    return None

def get_cart_items(cart_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, price, quantity FROM cart_items WHERE cart_id = ?", (cart_id,))
    items = cursor.fetchall()
    conn.close()
    return [{'name': item[0], 'price': item[1], 'quantity': item[2]} for item in items]

def get_cart_id_by_user(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT cart_id FROM carts WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def record_transaction(user_id, cart_id, total_amount, payment_status, shipping_address):
    transaction_id = str(uuid.uuid4())
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (transaction_id, user_id, cart_id, total_amount, payment_status, shipping_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (transaction_id, user_id, cart_id, total_amount, payment_status, shipping_address))
    conn.commit()
    conn.close()
    return transaction_id

# --- Payment Processing (Simulated) ---
def process_payment(payment_info, amount):
    """
    This is a simplified simulation of payment processing.
    In a real application, you would integrate with a secure payment gateway.
    """
    print(f"Processing payment of ${amount:.2f} with payment info: {payment_info}")
    # Simulate successful payment for testing purposes
    return True

# --- Checkout Logic ---
SHIPPING_FEE = 20.0

def checkout(user_id):
    """
    Processes the checkout for a given user.
    """
    user = get_user(user_id)
    if not user:
        return {"error": "User not found."}

    cart_id = get_cart_id_by_user(user_id)
    if not cart_id:
        return {"error": "Cart not found for this user."}

    cart_items = get_cart_items(cart_id)
    if not cart_items:
        return {"error": "Your cart is empty."}

    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    total_amount = subtotal + SHIPPING_FEE

    print("\n--- Order Summary ---")
    for item in cart_items:
        print(f"{item['name']} x {item['quantity']}: ${item['price'] * item['quantity']:.2f}")
    print(f"Subtotal: ${subtotal:.2f}")
    print(f"Shipping Fee: ${SHIPPING_FEE:.2f}")
    print(f"Total Amount: ${total_amount:.2f}")
    print("----------------------\n")

    payment_info = user.get('payment_info')
    shipping_address = user.get('shipping_address')

    if not payment_info:
        # In a real application, you would redirect the user to a payment method selection page
        print("No payment information found for this user. Please provide payment details.")
        # For this simulation, we'll just assume payment fails if no info is present
        payment_successful = False
    else:
        print(f"Using stored payment information for user {user['username']}.")
        payment_successful = process_payment(payment_info, total_amount)

    if not shipping_address:
        print("No shipping address found for this user. Please provide a shipping address.")
        shipping_address = "User provided address during checkout (not stored)" # Simulate user input

    if payment_successful:
        transaction_id = record_transaction(user_id, cart_id, total_amount, "SUCCESSFUL", shipping_address)
        return {"message": "Checkout successful!", "transaction_id": transaction_id}
    else:
        record_transaction(user_id, cart_id, total_amount, "FAILED", shipping_address)
        return {"error": "Payment failed. Please check your payment information."}

# --- Helper function to populate the database for testing ---
def populate_database_for_testing():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Add a test user
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, password, payment_info, shipping_address) VALUES (?, ?, ?, ?, ?)",
                   (1, 'testuser', 'password', '****-****-****-1234', '123 Main St, Knoxville, TN'))
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, password, payment_info, shipping_address) VALUES (?, ?, ?, ?, ?)",
                   (2, 'guestuser', 'password', None, None)) # User without payment info

    # Add a cart for the test user
    cursor.execute("INSERT OR IGNORE INTO carts (cart_id, user_id) VALUES (?, ?)", (101, 1))
    cursor.execute("INSERT OR IGNORE INTO carts (cart_id, user_id) VALUES (?, ?)", (102, 2))

    # Add items to the test user's cart
    cursor.execute("INSERT OR IGNORE INTO cart_items (item_id, cart_id, product_name, price, quantity) VALUES (?, ?, ?, ?, ?)",
                   (1001, 101, 'Awesome T-Shirt', 25.00, 2))
    cursor.execute("INSERT OR IGNORE INTO cart_items (item_id, cart_id, product_name, price, quantity) VALUES (?, ?, ?, ?, ?)",
                   (1002, 101, 'Cool Mug', 15.00, 1))

    # Add items to the guest user's cart
    cursor.execute("INSERT OR IGNORE INTO cart_items (item_id, cart_id, product_name, price, quantity) VALUES (?, ?, ?, ?, ?)",
                   (1003, 102, 'Fancy Pen', 10.00, 3))

    conn.commit()
    conn.close()

# --- Testing the functionality ---
if __name__ == "__main__":
    initialize_database()
    populate_database_for_testing()

    print("--- Testing Checkout for Logged-in User (ID 1) ---")
    result1 = checkout(1)
    print(result1)

    print("\n--- Testing Checkout for Logged-in User without Payment Info (ID 2) ---")
    result2 = checkout(2)
    print(result2)

    print("\n--- Checking Transactions Table ---")
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()
    for row in transactions:
        print(row)
    conn.close()