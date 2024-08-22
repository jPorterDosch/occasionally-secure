import sqlite3
import unittest

# Database connection details (Modify as needed)
DB_NAME = "ecommerce_test.db"  # Use a separate database for testing

# Product table structure (Modify as needed)
PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  price REAL NOT NULL
);
"""

# User table structure (Modify as needed)
USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  address TEXT,
  card_info TEXT
);
"""

# Cart table structure (Modify as needed)
CART_TABLE = """
CREATE TABLE IF NOT EXISTS cart (
  user_id INTEGER REFERENCES users(id),
  product_id INTEGER REFERENCES products(id),
  quantity INTEGER NOT NULL,
  FOREIGN KEY (user_id, product_id) PRIMARY KEY (user_id, product_id)
);
"""

# Orders table structure (Modify as needed)
ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id),
  total_price REAL NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT DEFAULT 'pending',  -- Default order status
  FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

# Order details table structure (Modify as needed)
ORDER_DETAILS_TABLE = """
CREATE TABLE IF NOT EXISTS order_details (
  order_id INTEGER REFERENCES orders(id),
  product_id INTEGER REFERENCES products(id),
  quantity INTEGER NOT NULL,
  price REAL NOT NULL,
  FOREIGN KEY (order_id, product_id) PRIMARY KEY (order_id, product_id)
);
"""


# Function to connect to the database
def connect_db():
  conn = sqlite3.connect(DB_NAME)
  conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
  return conn


# Function to create tables (if they don't exist)
def create_tables():
  conn = connect_db()
  cur = conn.cursor()
  cur.execute("DROP TABLE IF EXISTS products")
  cur.execute("DROP TABLE IF EXISTS users")
  cur.execute("DROP TABLE IF EXISTS cart")
  cur.execute("DROP TABLE IF EXISTS orders")
  cur.execute("DROP TABLE IF EXISTS order_details")

  cur.execute(PRODUCTS_TABLE)
  cur.execute(USERS_TABLE)
  cur.execute(CART_TABLE)
  cur.execute(ORDERS_TABLE)
  cur.execute(ORDER_DETAILS_TABLE)

  conn.commit()
  conn.close()


# Function to get user's cart items
def get_cart_items(user_id):
  conn = connect_db()
  cur = conn.cursor()

  cur.execute(
      """
      SELECT p.name, p.price, c.quantity
      FROM cart c
      INNER JOIN products p ON c.product_id = p.id
      WHERE c.user_id = ?
      """,
      (user_id,),
  )
  items = cur.fetchall()

  conn.close()
  return items


# Function to get user's shipping address
def get_shipping_address(user_id):
  conn = connect_db()
  cur = conn.cursor()

  cur.execute("SELECT address FROM users WHERE id = ?", (user_id,))
  address = cur.fetchone()

  conn.close()
  return address[0] if address else None


# Function to get user's saved card information (if logged in)
def get_saved_card(user_id):
  conn = connect_db()
  cur = conn.cursor()

  # Implement your login check here (replace with actual logic)
  # This is a placeholder assuming a 'is_logged_in' variable
  if not is_logged_in:
    return None

  cur.execute("SELECT card_info FROM users WHERE id = ?", (user_id,))
  card_info = cur.fetchone()

  conn.close()
  return card_info[0] if card_info else None


# Function to calculate total price
def calculate_total(items):
  total = 0
  for item in items:
    total += item[1] * item[2]  # price * quantity
  total += 20  # Add $20 shipping fee
  return total


# Function to simulate successful payment
def simulate_payment(total_price, card_info):
  # Replace
  # Replace this with your actual payment processing logic
  # This example simulates successful payment based on presence of card info
  print(f"Simulating payment of ${total_price:.2f} using saved card")
  return card_info is not None  # Simulate success based on card info

# Function to create a new order
def create_order(user_id, total_price):
  conn = connect_db()
  cur = conn.cursor()

  cur.execute(
      "INSERT INTO orders (user_id, total_price, status) VALUES (?, ?, ?)",
      (user_id, total_price, "pending"),
  )
  order_id = cur.lastrowid

  conn.commit()
  conn.close()
  return order_id


# Function to save order details
def save_order_details(order_id, items):
  conn = connect_db()
  cur = conn.cursor()

  for item in items:
    cur.execute(
        "INSERT INTO order_details (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
        (order_id, item[0], item[2], item[1]),
    )

  conn.commit()
  conn.close()


# Function to checkout process (Example usage)
def checkout(user_id):
  # Check if user is logged in
  if not is_logged_in:
    print("Please log in to checkout.")
    return

  # Get cart items
  cart_items = get_cart_items(user_id)

  # Check if cart is empty
  if not cart_items:
    print("Your cart is empty. Please add some items before checkout.")
    return

  # Get shipping address
  shipping_address = get_shipping_address(user_id)

  # If no shipping address found, prompt user to update profile
  if not shipping_address:
    print(
        "No shipping address found in your profile. Please update your profile before checkout."
    )
    return

  # Calculate total price
  total_price = calculate_total(cart_items)

  # Get saved card information
  saved_card = get_saved_card(user_id)

  # Simulate payment
  if simulate_payment(total_price, saved_card):
    # Create order
    order_id = create_order(user_id, total_price)

    # Save order details
    save_order_details(order_id, cart_items)

    # Update order status to 'paid' after successful payment
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status = 'paid' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

    print(f"Order created successfully! Order ID: {order_id}")
    print(f"Shipping to: {shipping_address}")
    print(f"Total price: ${total_price:.2f}")
  else:
    print(
        "Payment failed. Please check your saved card information or try a different payment method."
    )

class TestCheckout(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        conn = connect_db()
        create_products_table(conn)
        create_users_table(conn)
        create_cart_table(conn)
        create_orders_table(conn)
        create_order_details_table(conn)
        conn.close()

    @classmethod
    def tearDownClass(cls):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS order_details")
        cur.execute("DROP TABLE IF EXISTS orders")
        cur.execute("DROP TABLE IF EXISTS cart")
        cur.execute("DROP TABLE IF EXISTS users")
        cur.execute("DROP TABLE IF EXISTS products")
        conn.commit()
        conn.close()

    def setUp(self):
        # Create test data
        conn = connect_db()
        cur = conn.cursor()

        # Insert sample product
        cur.execute("INSERT INTO products (name, price) VALUES (?, ?)", ("Test Product", 10.00))
        product_id = cur.lastrowid

        # Insert sample user with card info
        cur.execute(
            "INSERT INTO users (username, email, password, address, card_info) VALUES (?, ?, ?, ?, ?)",
            ("test_user", "test@example.com", "password", "123 Main St", "card_info_123"),
        )
        user_id = cur.lastrowid

        # Add product to cart
        cur.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, 1))

        conn.commit()
        conn.close()

        self.user_id = user_id

    def tearDown(self):
        # Remove test data
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM order_details")
        cur.execute("DELETE FROM orders")
        cur.execute("DELETE FROM cart")
        conn.commit()
        conn.close()

    def test_checkout_successful_payment(self):
        # Simulate successful payment (modify for actual payment processing)
        is_logged_in = True
        saved_card = "card_info_123"

        checkout(self.user_id, is_logged_in, saved_card)

        # Verify order created with 'paid' status
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT status FROM orders WHERE user_id = ?", (self.user_id,))
        order_status = cur.fetchone()[0]
        conn.close()

        self.assertEqual(order_status, "paid")

    def test_checkout_failed_payment(self):
        # Simulate failed payment (modify for actual payment processing)
        is_logged_in = True
        saved_card = None

        checkout(self.user_id, is_logged_in, saved_card)

        # Verify order not created
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (self.user_id,))
        order_count = cur.fetchone()[0]
        conn.close()

        self.assertEqual(order_count, 0)  # No order created


# Helper functions to create tables
def connect_db():
  conn = sqlite3.connect(DB_NAME)
  conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
  return conn

def create_products_table(conn):
  cur = conn.cursor()
  cur.execute("""
  CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL
  );
  """)
  conn.commit()

def create_users_table(conn):
  cur = conn.cursor()
  cur.execute("""
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    address TEXT,
    card_info TEXT
  );
  """)
  conn.commit()

def create_cart_table(conn):
  cur = conn.cursor()
  try:
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cart (
    user_id INTEGER REFERENCES users(id),   
    product_id INTEGER REFERENCES products(id), 
    quantity INTEGER NOT NULL,              
    FOREIGN KEY (user_id, product_id) PRIMARY KEY (user_id, product_id) 
     );
    """)
    conn.commit()
  except sqlite3.Error as e:
    print(f"Error creating cart table: {e}")

def create_orders_table(conn):
  cur = conn.cursor()
  cur.execute("""
  CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  
    user_id INTEGER REFERENCES users(id),   
    total_price REAL NOT NULL,      
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',          
    FOREIGN KEY (user_id) REFERENCES users(id) 
  );
  """)
  conn.commit()

def create_order_details_table(conn):
  cur = conn.cursor()
  try:
    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_details (
      order_id INTEGER REFERENCES orders(id),   -- Foreign key referencing order ID
      product_id INTEGER REFERENCES products(id), -- Foreign key referencing product ID
      quantity INTEGER NOT NULL,              -- Quantity of product in order
      price REAL NOT NULL,                    -- Price of the product
      PRIMARY KEY (order_id, product_id)  -- Composite primary key
    );
    """)
    conn.commit()
    print("Order details table created successfully!")
  except sqlite3.Error as e:
    print(f"Error creating order details table: {e}")

if __name__ == "__main__":
  unittest.main()

# Example usage (assuming you have created tables and have login logic)
is_logged_in = True  # Replace with actual login check
user_id = 1  # Replace with actual user ID
checkout(user_id)
