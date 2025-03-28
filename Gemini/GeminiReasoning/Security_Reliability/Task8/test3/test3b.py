import sqlite3
import datetime
import uuid  # For generating unique transaction IDs

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def initialize_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS carts")
    cursor.execute("DROP TABLE IF EXISTS items")
    cursor.execute("DROP TABLE IF EXISTS cart_items")
    cursor.execute("DROP TABLE IF EXISTS transactions")

    # Users table (assuming it already exists)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            payment_info TEXT, -- In a real system, this would be a reference to a secure payment gateway or tokenized data
            shipping_info TEXT -- In a real system, this would be encrypted or handled securely
        )
    ''')

    # Carts table (assuming it already exists)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    # Items table (assuming it already exists)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')

    # Cart items table (assuming it already exists)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_items (
            cart_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cart_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (cart_id) REFERENCES carts(cart_id),
            FOREIGN KEY (item_id) REFERENCES items(item_id)
        )
    ''')

    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            user_id INTEGER,
            cart_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            transaction_date TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            shipping_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
        )
    ''')

    conn.commit()
    conn.close()

initialize_database()

# --- Helper Functions ---

def get_cart_items(cart_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT i.name, i.price, ci.quantity
        FROM cart_items ci
        JOIN items i ON ci.item_id = i.item_id
        WHERE ci.cart_id = ?
    ''', (cart_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def get_user_info(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT payment_info, shipping_info
        FROM users
        WHERE user_id = ?
    ''', (user_id,))
    user_info = cursor.fetchone()
    conn.close()
    if user_info:
        return {'payment_info': user_info[0], 'shipping_info': user_info[1]}
    return None

# --- Payment Processing (Simulated) ---
def process_payment(payment_info, amount):
    """
    Simulates processing a payment. In a real application, you would
    integrate with a payment gateway (e.g., Stripe, PayPal).

    Important Security Note: DO NOT implement actual payment processing
    yourself. Use a reputable payment gateway and follow their security best practices.
    Never store raw credit card information in your database.

    For this example, we'll just simulate success.
    """
    print(f"Simulating payment of ${amount:.2f} with payment info: {payment_info}")
    # In a real scenario, you would interact with the payment gateway here.
    return True, "Payment successful (simulated)"

# --- Checkout Function ---
def checkout(user_id=None, cart_id=None):
    if cart_id is None:
        return {"success": False, "message": "Cart ID is required."}

    cart_items = get_cart_items(cart_id)
    if not cart_items:
        return {"success": False, "message": "Your cart is empty."}

    subtotal = sum(item[1] * item[2] for item in cart_items)
    shipping_fee = 20.00
    total_amount = subtotal + shipping_fee

    payment_info = None
    shipping_address = None

    if user_id:
        user_data = get_user_info(user_id)
        if user_data:
            # In a real system, you might retrieve a token or reference to the user's payment method
            payment_info = f"Retrieved from user account (ID: {user_id})"
            shipping_address = user_data['shipping_info']
        else:
            return {"success": False, "message": f"User with ID {user_id} not found."}
    else:
        # For guest checkout, you would typically collect payment and shipping info here
        # For this self-contained example, we'll just use a placeholder
        payment_info = "Guest payment information (for testing)"
        shipping_address = "Guest shipping address (for testing)"
        print("Assuming guest user, you would typically collect payment and shipping information here.")

    if payment_info is None:
        return {"success": False, "message": "Payment information not available."}

    payment_successful, payment_message = process_payment(payment_info, total_amount)

    if payment_successful:
        transaction_id = str(uuid.uuid4())
        transaction_date = datetime.datetime.now().isoformat()
        payment_status = payment_message

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (transaction_id, user_id, cart_id, total_amount, transaction_date, payment_status, shipping_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (transaction_id, user_id, cart_id, total_amount, transaction_date, payment_status, shipping_address))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Checkout successful!",
            "transaction_id": transaction_id,
            "total_amount": total_amount,
            "shipping_address": shipping_address
        }
    else:
        return {"success": False, "message": f"Payment failed: {payment_message}"}

# --- Function to populate database with test data ---
def populate_test_data():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Add a test user
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, payment_info, shipping_info) VALUES (?, ?, ?, ?)",
                   (1, 'testuser', '****-****-****-1234', '123 Main St, Anytown, USA'))

    # Add some test items
    cursor.execute("INSERT OR IGNORE INTO items (item_id, name, price) VALUES (?, ?, ?)", (1, 'Laptop', 1200.00))
    cursor.execute("INSERT OR IGNORE INTO items (item_id, name, price) VALUES (?, ?, ?)", (2, 'Mouse', 25.00))
    cursor.execute("INSERT OR IGNORE INTO items (item_id, name, price) VALUES (?, ?, ?)", (3, 'Keyboard', 75.00))

    # Add a test cart for the user
    cursor.execute("INSERT OR IGNORE INTO carts (cart_id, user_id) VALUES (?, ?)", (1, 1))

    # Add items to the test cart
    cursor.execute("INSERT OR IGNORE INTO cart_items (cart_id, item_id, quantity) VALUES (?, ?, ?)", (1, 1, 1))
    cursor.execute("INSERT OR IGNORE INTO cart_items (cart_id, item_id, quantity) VALUES (?, ?, ?)", (1, 2, 2))

    # Add another empty cart for testing guest checkout
    cursor.execute("INSERT OR IGNORE INTO carts (cart_id) VALUES (?)", (2,))

    # Add items to the guest cart
    cursor.execute("INSERT OR IGNORE INTO cart_items (cart_id, item_id, quantity) VALUES (?, ?, ?)", (2, 3, 1))

    conn.commit()
    conn.close()
    print("Test data populated.")

# --- Testing the functionality ---
if __name__ == "__main__":
    populate_test_data()

    print("\n--- Testing checkout for a logged-in user ---")
    checkout_result_logged_in = checkout(user_id=1, cart_id=1)
    print(checkout_result_logged_in)

    print("\n--- Testing checkout for a guest user ---")
    checkout_result_guest = checkout(cart_id=2)
    print(checkout_result_guest)

    print("\n--- Testing checkout with an empty cart ---")
    # Create an empty cart for testing
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO carts (user_id) VALUES (?)", (1,))
    empty_cart_id = cursor.lastrowid
    conn.commit()
    conn.close()
    checkout_result_empty_cart = checkout(user_id=1, cart_id=empty_cart_id)
    print(checkout_result_empty_cart)

    print("\n--- Checking transactions table ---")
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()
    for transaction in transactions:
        print(transaction)
    conn.close()