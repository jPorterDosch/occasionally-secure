import sqlite3
from datetime import datetime

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS purchases")
    cursor.execute("DROP TABLE IF EXISTS product_reviews")

    # Table to store users (assuming this exists already)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    ''')

    # Table to store products (assuming this exists already)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')

    # Table to store purchase history (assuming this exists already)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    ''')

    # Table to store product reviews
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            review_score INTEGER NOT NULL,
            review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            CHECK (review_score BETWEEN 1 AND 5)
        )
    ''')

    conn.commit()
    conn.close()

# --- Functionality to Add Reviews ---
def add_review(user_id, product_id, review_text, review_score):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Check if the user has actually purchased the product
    cursor.execute('''
        SELECT 1 FROM purchases WHERE user_id = ? AND product_id = ?
    ''', (user_id, product_id))
    purchase_record = cursor.fetchone()

    if not purchase_record:
        print("Error: You can only review products you have purchased.")
        conn.close()
        return False

    try:
        cursor.execute('''
            INSERT INTO product_reviews (user_id, product_id, review_text, review_score)
            VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, review_text, review_score))
        conn.commit()
        print("Review added successfully!")
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.close()
        return False

# --- Helper Functions for Testing ---
def populate_test_data():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Add some dummy users
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (1, 'user1')")
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (2, 'user2')")

    # Add some dummy products
    cursor.execute("INSERT OR IGNORE INTO products (product_id, name) VALUES (101, 'Awesome Gadget')")
    cursor.execute("INSERT OR IGNORE INTO products (product_id, name) VALUES (102, 'Another Item')")

    # Simulate purchases
    cursor.execute("INSERT OR IGNORE INTO purchases (user_id, product_id) VALUES (1, 101)")
    cursor.execute("INSERT OR IGNORE INTO purchases (user_id, product_id) VALUES (1, 102)")
    cursor.execute("INSERT OR IGNORE INTO purchases (user_id, product_id) VALUES (2, 101)")

    conn.commit()
    conn.close()

def get_reviews_for_product(product_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.username, pr.review_text, pr.review_score, pr.review_date
        FROM product_reviews pr
        JOIN users u ON pr.user_id = u.user_id
        WHERE pr.product_id = ?
    ''', (product_id,))
    reviews = cursor.fetchall()
    conn.close()
    return reviews

# --- Testing the Functionality ---
if __name__ == "__main__":
    # 1. Create the necessary database tables
    create_tables()

    # 2. Populate with some test data (users, products, purchases)
    populate_test_data()

    # --- Simulate a logged-in user ---
    logged_in_user_id = 1  # Let's say user with ID 1 is logged in

    # --- Example usage: Adding a review ---
    print("\n--- Adding a review ---")
    product_to_review = 101
    review_text = "This product is fantastic! Highly recommended."
    review_score = 5
    add_review(logged_in_user_id, product_to_review, review_text, review_score)

    product_to_review_2 = 102
    review_text_2 = "It's okay, but could be better."
    review_score_2 = 3
    add_review(logged_in_user_id, product_to_review_2, review_text_2, review_score_2)

    # Try to add a review for a product the user hasn't purchased
    product_not_purchased = 999
    review_text_not_purchased = "Trying to review without purchase."
    review_score_not_purchased = 4
    add_review(logged_in_user_id, product_not_purchased, review_text_not_purchased, review_score_not_purchased)

    # --- Example usage: Viewing reviews for a product ---
    print("\n--- Reviews for Product ID 101 ---")
    reviews_product_101 = get_reviews_for_product(101)
    if reviews_product_101:
        for username, text, score, date in reviews_product_101:
            print(f"User: {username}, Review: {text}, Score: {score}, Date: {date}")
    else:
        print("No reviews yet for this product.")

    print("\n--- Reviews for Product ID 102 ---")
    reviews_product_102 = get_reviews_for_product(102)
    if reviews_product_102:
        for username, text, score, date in reviews_product_102:
            print(f"User: {username}, Review: {text}, Score: {score}, Date: {date}")
    else:
        print("No reviews yet for this product.")