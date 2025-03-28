import sqlite3
from datetime import datetime

class ECommerceCheckout:
    def __init__(self, db_name='ecommerce.db'):
        self.db_name = db_name
        self._create_tables()

    def _create_tables(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS carts")
        cursor.execute("DROP TABLE IF EXISTS orders")
        cursor.execute("DROP TABLE IF EXISTS order_items")
        cursor.execute("DROP TABLE IF EXISTS transactions")
      
        # Users table (simplified for this example)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                shipping_address TEXT
            )
        """)

        # Products table (simplified)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        """)

        # User's cart table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS carts (
                cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)

        # Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL NOT NULL,
                shipping_address TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Order items table
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

        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
        """)

        conn.commit()
        conn.close()

    def add_user(self, username, shipping_address):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, shipping_address) VALUES (?, ?)", (username, shipping_address))
        conn.commit()
        conn.close()

    def add_product(self, name, price):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, price) VALUES (?, ?)", (name, price))
        conn.commit()
        conn.close()

    def add_to_cart(self, user_id, product_id, quantity):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Check if the item is already in the cart
        cursor.execute("SELECT quantity FROM carts WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        existing_item = cursor.fetchone()
        if existing_item:
            new_quantity = existing_item[0] + quantity
            cursor.execute("UPDATE carts SET quantity = ? WHERE user_id = ? AND product_id = ?", (new_quantity, user_id, product_id))
        else:
            cursor.execute("INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))
        conn.commit()
        conn.close()

    def get_cart_items(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.product_id, p.name, c.quantity, p.price
            FROM carts c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = ?
        """, (user_id,))
        items = cursor.fetchall()
        conn.close()
        return [{'product_id': item[0], 'name': item[1], 'quantity': item[2], 'price': item[3]} for item in items]

    def get_user_profile(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT shipping_address FROM users WHERE user_id = ?", (user_id,))
        profile = cursor.fetchone()
        conn.close()
        return {'shipping_address': profile[0]} if profile else None

    def process_checkout(self, user_id):
        cart_items = self.get_cart_items(user_id)
        if not cart_items:
            return {"status": "error", "message": "Your cart is empty."}

        user_profile = self.get_user_profile(user_id)
        if not user_profile or not user_profile.get('shipping_address'):
            return {"status": "error", "message": "Shipping address not found for this user."}

        shipping_address = user_profile['shipping_address']
        shipping_fee = 20.00
        total_amount = shipping_fee
        order_items_data = []

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        for item in cart_items:
            total_amount += item['quantity'] * item['price']
            order_items_data.append((item['product_id'], item['quantity'], item['price']))

        try:
            # Record the order
            cursor.execute(
                "INSERT INTO orders (user_id, total_amount, shipping_address) VALUES (?, ?, ?)",
                (user_id, total_amount, shipping_address)
            )
            order_id = cursor.lastrowid

            # Record the order items
            for product_id, quantity, price_per_item in order_items_data:
                cursor.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, price_per_item) VALUES (?, ?, ?, ?)",
                    (order_id, product_id, quantity, price_per_item)
                )

            # Record the successful transaction
            cursor.execute(
                "INSERT INTO transactions (order_id, status) VALUES (?, ?)",
                (order_id, 'success')
            )

            # Clear the user's cart
            cursor.execute("DELETE FROM carts WHERE user_id = ?", (user_id,))

            conn.commit()
            conn.close()
            return {"status": "success", "message": f"Order placed successfully. Order ID: {order_id}", "total_amount": total_amount}

        except sqlite3.Error as e:
            conn.rollback()
            conn.close()
            return {"status": "error", "message": f"Error processing order: {e}"}

def test_checkout_functionality():
    checkout_system = ECommerceCheckout()

    # Add a test user
    checkout_system.add_user("testuser", "123 Main St, Knoxville, TN")
    user_id = 1  # Assuming the first user added gets ID 1

    # Add some test products
    checkout_system.add_product("Laptop", 1200.00)
    checkout_system.add_product("Mouse", 25.00)
    product_id_laptop = 1
    product_id_mouse = 2

    # Add items to the user's cart
    checkout_system.add_to_cart(user_id, product_id_laptop, 1)
    checkout_system.add_to_cart(user_id, product_id_mouse, 2)

    # Get the current cart items
    print("Current Cart Items:", checkout_system.get_cart_items(user_id))

    # Process the checkout
    checkout_result = checkout_system.process_checkout(user_id)
    print("Checkout Result:", checkout_result)

    # Verify the cart is now empty
    print("Cart Items After Checkout:", checkout_system.get_cart_items(user_id))

    # You can further query the database to verify the order and transaction records

if __name__ == "__main__":
    test_checkout_functionality()