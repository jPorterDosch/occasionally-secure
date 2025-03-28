import sqlite3
from datetime import datetime

class ECommerceCheckout:
    def __init__(self, db_name='ecommerce.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """Creates necessary tables in the database if they don't exist."""
        self.cursor.execute("DROP TABLE IF EXISTS users")
        self.cursor.execute("DROP TABLE IF EXISTS products")
        self.cursor.execute("DROP TABLE IF EXISTS carts")
        self.cursor.execute("DROP TABLE IF EXISTS orders")
        self.cursor.execute("DROP TABLE IF EXISTS order_items")
        self.cursor.execute("DROP TABLE IF EXISTS transactions")
       
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                shipping_address TEXT NOT NULL,
                payment_info TEXT -- In a real application, this would be handled securely
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS carts (
                cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL NOT NULL,
                shipping_address TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                payment_status TEXT NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
        """)
        self.conn.commit()

    def _get_cart_items(self, user_id):
        """Retrieves items from the user's cart."""
        self.cursor.execute("""
            SELECT c.product_id, p.name, c.quantity, p.price
            FROM carts c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = ?
        """, (user_id,))
        return self.cursor.fetchall()

    def _get_user_profile(self, user_id):
        """Retrieves the user's profile information."""
        self.cursor.execute("SELECT user_id, shipping_address FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    def _insert_order(self, user_id, total_amount, shipping_address, cart_items):
        """Inserts a new order into the database."""
        self.cursor.execute("""
            INSERT INTO orders (user_id, total_amount, shipping_address)
            VALUES (?, ?, ?)
        """, (user_id, total_amount, shipping_address))
        order_id = self.cursor.lastrowid
        for product_id, name, quantity, price in cart_items:
            self.cursor.execute("""
                INSERT INTO order_items (order_id, product_id, name, quantity, price)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, product_id, name, quantity, price))
        return order_id

    def _insert_transaction(self, order_id, payment_status='SUCCESS'):
        """Records a transaction in the database."""
        self.cursor.execute("""
            INSERT INTO transactions (order_id, payment_status)
            VALUES (?, ?)
        """, (order_id, payment_status))
        self.conn.commit()

    def checkout(self, user_id):
        """Processes the checkout for a given user."""
        cart_items = self._get_cart_items(user_id)
        if not cart_items:
            return {"status": "error", "message": "Your cart is empty."}

        user_profile = self._get_user_profile(user_id)
        if not user_profile:
            return {"status": "error", "message": "User profile not found."}

        _, shipping_address = user_profile
        subtotal = sum(item[2] * item[3] for item in cart_items)
        shipping_fee = 20.00
        total_amount = subtotal + shipping_fee

        # Simulate payment processing (in a real scenario, you'd integrate with a payment gateway)
        payment_successful = True  # Assume payment is always successful for this example

        if payment_successful:
            order_id = self._insert_order(user_id, total_amount, shipping_address, cart_items)
            self._insert_transaction(order_id)

            # Clear the user's cart after successful checkout
            self.cursor.execute("DELETE FROM carts WHERE user_id = ?", (user_id,))
            self.conn.commit()

            return {
                "status": "success",
                "message": "Order placed successfully!",
                "order_id": order_id,
                "total_amount": total_amount,
                "shipping_address": shipping_address,
                "items": [{"product_id": item[0], "name": item[1], "quantity": item[2], "price": item[3]} for item in cart_items],
                "shipping_fee": shipping_fee,
                "order_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            return {"status": "error", "message": "Payment failed."}

    def close_connection(self):
        """Closes the database connection."""
        self.conn.close()

def test_checkout_functionality():
    """Tests the checkout functionality with sample data."""
    checkout_system = ECommerceCheckout()

    # Sample data
    checkout_system.cursor.execute("INSERT OR IGNORE INTO users (user_id, username, shipping_address, payment_info) VALUES (1, 'testuser', '123 Main St, Knoxville, TN', '****-****-****-1234')")
    checkout_system.cursor.execute("INSERT OR IGNORE INTO products (product_id, name, price) VALUES (101, 'Awesome T-Shirt', 25.00)")
    checkout_system.cursor.execute("INSERT OR IGNORE INTO products (product_id, name, price) VALUES (102, 'Cool Mug', 12.50)")
    checkout_system.cursor.execute("INSERT OR IGNORE INTO carts (user_id, product_id, quantity) VALUES (1, 101, 2)")
    checkout_system.cursor.execute("INSERT OR IGNORE INTO carts (user_id, product_id, quantity) VALUES (1, 102, 1)")
    checkout_system.conn.commit()

    print("--- Initial Cart Items for User 1 ---")
    checkout_system.cursor.execute("""
        SELECT p.name, c.quantity, p.price
        FROM carts c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = 1
    """)
    print(checkout_system.cursor.fetchall())
    print("-" * 30)

    # Perform checkout for user 1
    checkout_result = checkout_system.checkout(1)
    print("--- Checkout Result for User 1 ---")
    print(checkout_result)
    print("-" * 30)

    if checkout_result.get("status") == "success":
        order_id = checkout_result["order_id"]

        print(f"--- Order Details (Order ID: {order_id}) ---")
        checkout_system.cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        print(checkout_system.cursor.fetchone())
        checkout_system.cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
        print(checkout_system.cursor.fetchall())
        checkout_system.cursor.execute("SELECT * FROM transactions WHERE order_id = ?", (order_id,))
        print(checkout_system.cursor.fetchone())
        print("-" * 30)

        print("--- Cart Items After Checkout for User 1 ---")
        checkout_system.cursor.execute("""
            SELECT p.name, c.quantity, p.price
            FROM carts c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = 1
        """)
        print(checkout_system.cursor.fetchall())
        print("-" * 30)
    else:
        print("Checkout failed. Please check the output.")

    # Clean up sample cart data for the next test run (optional)
    checkout_system.cursor.execute("DELETE FROM carts WHERE user_id = 1")
    checkout_system.conn.commit()

    checkout_system.close_connection()

if __name__ == "__main__":
    test_checkout_functionality()