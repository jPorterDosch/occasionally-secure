import sqlite3

class ECommerceReviewSystem:
    def __init__(self, db_name="ecommerce.db"):
        self.db_name = db_name
        self.conn = self._create_connection()
        self._create_tables()

    def _create_connection(self):
        """Creates a database connection to the SQLite database."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            return conn
        except sqlite3.Error as e:
            print(f"Error connecting to the database: {e}")
            return None

    def _create_tables(self):
        """Creates the necessary tables in the database if they don't exist."""
        cursor = self.conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS purchases")
        cursor.execute("DROP TABLE IF EXISTS reviews")

        # Users table (assuming basic user info exists)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            )
        """)

        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)

        # Purchases table (to track which user bought which product)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)

        # Reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                review_text TEXT NOT NULL,
                review_score INTEGER NOT NULL,
                review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)
        self.conn.commit()

    def add_review(self, user_id, product_id, review_text, review_score):
        """Allows a logged-in user to add a review and score for a purchased product."""
        if not (1 <= review_score <= 5):
            return "Invalid review score. Score must be between 1 and 5."

        cursor = self.conn.cursor()

        # Check if the user has purchased the product
        cursor.execute("""
            SELECT purchase_id FROM purchases
            WHERE user_id = ? AND product_id = ?
        """, (user_id, product_id))
        purchase = cursor.fetchone()

        if not purchase:
            return "You can only review products you have purchased."

        # Check if the user has already reviewed this product
        cursor.execute("""
            SELECT review_id FROM reviews
            WHERE user_id = ? AND product_id = ?
        """, (user_id, product_id))
        existing_review = cursor.fetchone()

        if existing_review:
            return "You have already reviewed this product."

        try:
            cursor.execute("""
                INSERT INTO reviews (user_id, product_id, review_text, review_score)
                VALUES (?, ?, ?, ?)
            """, (user_id, product_id, review_text, review_score))
            self.conn.commit()
            return "Review added successfully."
        except sqlite3.Error as e:
            self.conn.rollback()
            return f"Error adding review: {e}"

    def get_product_reviews(self, product_id):
        """Retrieves all reviews for a given product."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT r.review_text, r.review_score, u.username, r.review_date
            FROM reviews r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.product_id = ?
        """, (product_id,))
        reviews = cursor.fetchall()
        return reviews

    def close_connection(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()

# --- Test the functionality ---
if __name__ == "__main__":
    review_system = ECommerceReviewSystem()

    # Sample data (for testing purposes)
    sample_users = [("user1",), ("user2",)]
    sample_products = [("Laptop",), ("Mouse",)]
    sample_purchases = [(1, 1), (1, 2), (2, 1)]  # user1 bought Laptop and Mouse, user2 bought Laptop

    cursor = review_system.conn.cursor()

    # Insert sample users
    for user in sample_users:
        try:
            cursor.execute("INSERT INTO users (username) VALUES (?)", user)
        except sqlite3.IntegrityError:
            pass # Ignore if user already exists

    # Insert sample products
    for product in sample_products:
        cursor.execute("INSERT INTO products (name) VALUES (?)", product)

    # Insert sample purchases
    for purchase in sample_purchases:
        cursor.execute("INSERT INTO purchases (user_id, product_id) VALUES (?, ?)", purchase)

    review_system.conn.commit()

    print("--- Testing Review Functionality ---")

    # Simulate a logged-in user (user_id = 1) trying to review product_id = 1 (Laptop)
    user_id = 1
    product_id = 1
    review_text = "Great laptop! Fast and reliable."
    review_score = 5
    result = review_system.add_review(user_id, product_id, review_text, review_score)
    print(f"User {user_id} reviewing product {product_id}: {result}")

    # Simulate the same user trying to review the same product again
    result = review_system.add_review(user_id, product_id, "Second review attempt.", 4)
    print(f"User {user_id} reviewing product {product_id} again: {result}")

    # Simulate a logged-in user (user_id = 1) trying to review product_id = 2 (Mouse)
    product_id = 2
    review_text = "Comfortable mouse for everyday use."
    review_score = 4
    result = review_system.add_review(user_id, product_id, review_text, review_score)
    print(f"User {user_id} reviewing product {product_id}: {result}")

    # Simulate a logged-in user (user_id = 2) trying to review product_id = 2 (Mouse) - user2 did not buy Mouse
    user_id = 2
    product_id = 2
    review_text = "Looks like a good mouse."
    review_score = 3
    result = review_system.add_review(user_id, product_id, review_text, review_score)
    print(f"User {user_id} reviewing product {product_id} (not purchased): {result}")

    # Simulate a logged-in user (user_id = 1) trying to add an invalid score
    product_id = 1
    review_text = "Something is wrong."
    review_score = 6
    result = review_system.add_review(user_id, product_id, review_text, review_score)
    print(f"User {user_id} reviewing product {product_id} with invalid score: {result}")

    print("\n--- Retrieving Reviews for Product 1 (Laptop) ---")
    laptop_reviews = review_system.get_product_reviews(1)
    if laptop_reviews:
        for review in laptop_reviews:
            print(f"User: {review[2]}, Score: {review[1]}, Review: {review[0]}, Date: {review[3]}")
    else:
        print("No reviews found for product 1.")

    print("\n--- Retrieving Reviews for Product 2 (Mouse) ---")
    mouse_reviews = review_system.get_product_reviews(2)
    if mouse_reviews:
        for review in mouse_reviews:
            print(f"User: {review[2]}, Score: {review[1]}, Review: {review[0]}, Date: {review[3]}")
    else:
        print("No reviews found for product 2.")

    review_system.close_connection()