import sqlite3
from datetime import datetime

class ECommerceCheckout:
    def __init__(self, db_name='ecommerce.db'):
        self.db_name = db_name
        self._create_tables()

    def _connect_db(self):
        return sqlite3.connect(self.db_name)

    def _create_tables(self):
        conn = self._connect_db()
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS carts")
        cursor.execute("DROP TABLE IF EXISTS orders")
        cursor.execute("DROP TABLE IF EXISTS order_items")

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                shipping_address TEXT,
                payment_info TEXT -- In a real application, this would be handled securely
            )
        ''')

        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')

        # Create carts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carts (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                PRIMARY KEY (user_id, product_id)
            )
        ''')

        # Create orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                shipping_address TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Create order_items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        ''')

        conn.commit()
        conn.close()

    def _get_cart_items(self, user_id):
        conn = self._connect_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.product_id, p.name, c.quantity, p.price
            FROM carts c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = ?
        ''', (user_id,))
        cart_items = cursor.fetchall()
        conn.close()
        return cart_items

    def _get_user_shipping_address(self, user_id):
        conn = self._connect_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT shipping_address FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def _record_order(self, user_id, total_amount, shipping_address, cart_items):
        conn = self._connect_db()
        cursor = conn.cursor()
        order_date = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO orders (user_id, order_date, total_amount, shipping_address)
            VALUES (?, ?, ?, ?)
        ''', (user_id, order_date, total_amount, shipping_address))
        order_id = cursor.lastrowid

        for product_id, name, quantity, price in cart_items:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, product_id, quantity, price))

        # Clear the user's cart after successful checkout
        cursor.execute('''
            DELETE FROM carts WHERE user_id = ?
        ''', (user_id,))

        conn.commit()
        conn.close()
        return True, order_id

    def checkout(self, user_id):
        cart_items = self._get_cart_items(user_id)
        if not cart_items:
            return False, "Your cart is empty."

        shipping_address = self._get_user_shipping_address(user_id)
        if not shipping_address:
            return False, "Shipping address not found for this user."

        subtotal = sum(item[2] * item[3] for item in cart_items)
        shipping_fee = 20.00
        total_amount = subtotal + shipping_fee

        # Simulate payment processing (in a real application, this would involve a payment gateway)
        payment_successful = True  # Assume payment is always successful for this example

        if payment_successful:
            success, order_id = self._record_order(user_id, total_amount, shipping_address, cart_items)
            if success:
                return True, f"Order placed successfully! Order ID: {order_id}. Total amount: ${total_amount:.2f}"
            else:
                return False, "Failed to record the order."
        else:
            return False, "Payment failed."

# --- Functionality for testing ---
def populate_database(checkout_system):
    conn = checkout_system._connect_db()
    cursor = conn.cursor()

    # Add a test user
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, shipping_address, payment_info)
        VALUES (1, 'testuser', '123 Main St, Knoxville, TN', '****-****-****-1234')
    ''')

    # Add some test products
    cursor.execute('''
        INSERT OR IGNORE INTO products (product_id, name, price)
        VALUES (101, 'Awesome T-Shirt', 25.99)
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO products (product_id, name, price)
        VALUES (102, 'Cool Coffee Mug', 12.50)
    ''')

    # Add items to the test user's cart
    cursor.execute('''
        INSERT OR IGNORE INTO carts (user_id, product_id, quantity)
        VALUES (1, 101, 2)
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO carts (user_id, product_id, quantity)
        VALUES (1, 102, 1)
    ''')

    # Add another user with an empty cart
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, shipping_address, payment_info)
        VALUES (2, 'emptycartuser', '456 Oak Ave, Knoxville, TN', '****-****-****-5678')
    ''')

    # Add another user with no shipping address
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, shipping_address, payment_info)
        VALUES (3, 'noaddressuser', NULL, '****-****-****-9012')
    ''')

    conn.commit()
    conn.close()

def test_checkout_process():
    checkout_system = ECommerceCheckout()
    populate_database(checkout_system)

    print("--- Testing Checkout Process ---")

    # Test checkout for user with items in the cart
    user_id_with_cart = 1
    success, message = checkout_system.checkout(user_id_with_cart)
    if success:
        print(f"Test 1 (User with cart): Success! {message}")
    else:
        print(f"Test 1 (User with cart): Failed. {message}")

    # Test checkout for user with an empty cart
    user_id_empty_cart = 2
    success, message = checkout_system.checkout(user_id_empty_cart)
    if success:
        print(f"Test 2 (User with empty cart): Success! {message}")
    else:
        print(f"Test 2 (User with empty cart): Failed. {message}")

    # Test checkout for user with no shipping address
    user_id_no_address = 3
    success, message = checkout_system.checkout(user_id_no_address)
    if success:
        print(f"Test 3 (User with no address): Success! {message}")
    else:
        print(f"Test 3 (User with no address): Failed. {message}")

    print("\n--- Checking the database ---")
    conn = checkout_system._connect_db()
    cursor = conn.cursor()

    # Check the orders table
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    print("\nOrders Table:")
    for order in orders:
        print(order)

    # Check the order_items table
    cursor.execute("SELECT * FROM order_items")
    order_items = cursor.fetchall()
    print("\nOrder Items Table:")
    for item in order_items:
        print(item)

    # Check if the cart for user 1 is now empty
    cursor.execute("SELECT * FROM carts WHERE user_id = 1")
    remaining_cart_items = cursor.fetchall()
    print("\nCart for user 1 after checkout:", remaining_cart_items)

    conn.close()

if __name__ == "__main__":
    test_checkout_process()