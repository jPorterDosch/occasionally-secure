import sqlite3
import uuid
from datetime import datetime

class User:
    def __init__(self, user_id, username, shipping_address, payment_info):
        self.user_id = user_id
        self.username = username
        self.shipping_address = shipping_address
        self.payment_info = payment_info

class Product:
    def __init__(self, product_id, name, price):
        self.product_id = product_id
        self.name = name
        self.price = price

class CartItem:
    def __init__(self, product_id, quantity):
        self.product_id = product_id
        self.quantity = quantity

class Order:
    def __init__(self, order_id, user_id, order_date, total_amount, shipping_address, items, transaction_id, payment_status):
        self.order_id = order_id
        self.user_id = user_id
        self.order_date = order_date
        self.total_amount = total_amount
        self.shipping_address = shipping_address
        self.items = items
        self.transaction_id = transaction_id
        self.payment_status = payment_status

def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS carts")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS order_items")

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_info TEXT NOT NULL -- In a real application, this would be handled securely
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
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            PRIMARY KEY (user_id, product_id)
        )
    ''')

    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            order_date DATETIME NOT NULL,
            total_amount REAL NOT NULL,
            shipping_address TEXT NOT NULL,
            transaction_id TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    # Order items table (for storing individual items in an order)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            order_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            PRIMARY KEY (order_id, product_id)
        )
    ''')

    conn.commit()

def add_user(conn, username, shipping_address, payment_info):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, shipping_address, payment_info) VALUES (?, ?, ?)",
                   (username, shipping_address, payment_info))
    conn.commit()
    return cursor.lastrowid

def add_product(conn, name, price):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, price) VALUES (?, ?)", (name, price))
    conn.commit()
    return cursor.lastrowid

def add_to_cart(conn, user_id, product_id, quantity):
    cursor = conn.cursor()
    # Check if the item is already in the cart
    cursor.execute("SELECT quantity FROM carts WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    existing_item = cursor.fetchone()
    if existing_item:
        new_quantity = existing_item[0] + quantity
        cursor.execute("UPDATE carts SET quantity = ? WHERE user_id = ? AND product_id = ?",
                       (new_quantity, user_id, product_id))
    else:
        cursor.execute("INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)",
                       (user_id, product_id, quantity))
    conn.commit()

def get_cart_items(conn, user_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.product_id, p.name, p.price, c.quantity
        FROM carts c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = ?
    ''', (user_id,))
    items = []
    for row in cursor.fetchall():
        items.append({
            'product_id': row[0],
            'name': row[1],
            'price': row[2],
            'quantity': row[3]
        })
    return items

def get_user_profile(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, shipping_address FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2], None) # Payment info is not needed here
    return None

def process_payment(total_amount, payment_info):
    """
    Simulates payment processing. In a real application, this would involve
    integrating with a payment gateway.
    """
    print(f"Processing payment of ${total_amount:.2f} with payment info: {payment_info}")
    # For demonstration purposes, we'll just assume the payment is always successful
    return True, str(uuid.uuid4()) # Return payment status and transaction ID

def submit_order(conn, user, cart_items, total_amount, transaction_id, payment_status):
    cursor = conn.cursor()
    order_id = str(uuid.uuid4())
    order_date = datetime.now()

    cursor.execute('''
        INSERT INTO orders (order_id, user_id, order_date, total_amount, shipping_address, transaction_id, payment_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, user.user_id, order_date, total_amount, user.shipping_address, transaction_id, payment_status))

    for item in cart_items:
        cursor.execute('''
            INSERT INTO order_items (order_id, product_id, name, price, quantity)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, item['product_id'], item['name'], item['price'], item['quantity']))

    # Clear the user's cart after successful order submission
    cursor.execute("DELETE FROM carts WHERE user_id = ?", (user.user_id,))

    conn.commit()
    return order_id

def checkout(conn, user_id):
    user = get_user_profile(conn, user_id)
    if not user:
        return "Error: User not found."

    cart_items = get_cart_items(conn, user_id)
    if not cart_items:
        return "Your cart is empty."

    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    shipping_fee = 20.00
    total_amount = subtotal + shipping_fee

    # In a real application, you would retrieve payment info securely
    payment_successful, transaction_id = process_payment(total_amount, user.payment_info)

    if payment_successful:
        order_id = submit_order(conn, user, cart_items, total_amount, transaction_id, "SUCCESS")
        return f"Checkout successful! Your order ID is: {order_id}. Total amount: ${total_amount:.2f}"
    else:
        return "Payment failed. Please try again."

def test_checkout_process():
    # Create an in-memory SQLite database for testing
    conn = sqlite3.connect(':memory:')
    create_tables(conn)

    # Add a test user
    user_id = add_user(conn, "testuser", "123 Main St, Knoxville, TN", "Visa ****-****-****-1234")

    # Add some test products
    product_id_1 = add_product(conn, "Laptop", 1200.00)
    product_id_2 = add_product(conn, "Mouse", 25.00)

    # Add items to the user's cart
    add_to_cart(conn, user_id, product_id_1, 1)
    add_to_cart(conn, user_id, product_id_2, 2)

    # Perform the checkout
    checkout_result = checkout(conn, user_id)
    print(checkout_result)

    # Verify that the cart is now empty
    cart_items = get_cart_items(conn, user_id)
    print("Items in cart after checkout:", cart_items)

    # Optionally, you can query the orders table to verify the order was created
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,))
    orders = cursor.fetchall()
    print("Orders for user:", orders)

    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (orders[0][0],))
    order_items = cursor.fetchall()
    print("Order items:", order_items)

    conn.close()

if __name__ == "__main__":
    test_checkout_process()