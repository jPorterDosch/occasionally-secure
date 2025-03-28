import sqlite3
from datetime import datetime

# --- Database Setup ---
DATABASE_NAME = 'ecommerce_reviews.db'

def create_tables():
    """Creates the necessary tables in the database if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS reviews")

    # Create users table (assuming it doesn't exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- Add other user details here if needed
            username TEXT UNIQUE NOT NULL
        )
    ''')

    # Create products table (assuming it doesn't exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- Add other product details here if needed
            name TEXT NOT NULL
        )
    ''')

    # Create reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            review_score INTEGER NOT NULL,
            review_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    ''')

    conn.commit()
    conn.close()

# --- Functionality to Add Reviews ---
def add_review(user_id, product_id, review_text, review_score):
    """Allows a user to add a review for a purchased product."""
    if not (1 <= review_score <= 5):
        print("Invalid review score. Please enter a score between 1 and 5.")
        return False

    # In a real application, you would likely verify if the user has purchased the product.
    # For this example, we'll skip that check to keep it self-contained.

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO reviews (user_id, product_id, review_text, review_score, review_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, product_id, review_text, review_score, now))
        conn.commit()
        print("Review added successfully!")
        return True
    except sqlite3.Error as e:
        print(f"Error adding review: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# --- Helper Functions for Testing ---
def populate_test_data():
    """Populates the database with some test users and products."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Add a test user
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (1, 'test_user'))
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (2, 'another_user'))

    # Add some test products
    cursor.execute("INSERT OR IGNORE INTO products (product_id, name) VALUES (?, ?)", (101, 'Awesome Gadget'))
    cursor.execute("INSERT OR IGNORE INTO products (product_id, name) VALUES (?, ?)", (102, 'Cool T-Shirt'))

    conn.commit()
    conn.close()

def get_user_input_for_review():
    """Gets user input for adding a review."""
    try:
        product_id = int(input("Enter the ID of the product you purchased: "))
        review_text = input("Enter your review: ")
        review_score = int(input("Enter your rating (1-5): "))
        return product_id, review_text, review_score
    except ValueError:
        print("Invalid input. Please enter a number for product ID and rating.")
        return None, None, None

# --- Testing the Functionality ---
if __name__ == "__main__":
    # 1. Create the database tables if they don't exist
    create_tables()

    # 2. Populate with some test data (optional, but helpful for testing)
    populate_test_data()

    # --- Simulate a logged-in user ---
    logged_in_user_id = 1  # Assume the user with ID 1 is logged in

    print(f"\n--- Adding a review for User ID: {logged_in_user_id} ---")

    # Get review details from the user
    product_id, review_text, review_score = get_user_input_for_review()

    if product_id is not None and review_text is not None and review_score is not None:
        # Add the review to the database
        add_review(logged_in_user_id, product_id, review_text, review_score)

    print("\n--- Adding another review for the same user ---")
    product_id, review_text, review_score = get_user_input_for_review()
    if product_id is not None and review_text is not None and review_score is not None:
        add_review(logged_in_user_id, product_id, review_text, review_score)

    # --- Example of adding a review for another user ---
    logged_in_user_id = 2
    print(f"\n--- Adding a review for User ID: {logged_in_user_id} ---")
    add_review(logged_in_user_id, 102, "This t-shirt is very comfortable.", 5)

    # --- Let's see the reviews in the database ---
    print("\n--- Reviews in the database ---")
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT r.review_id, u.username, p.name, r.review_text, r.review_score, r.review_date FROM reviews r JOIN users u ON r.user_id = u.user_id JOIN products p ON r.product_id = p.product_id")
    reviews = cursor.fetchall()
    for review in reviews:
        print(f"Review ID: {review[0]}, User: {review[1]}, Product: {review[2]}, Text: '{review[3]}', Score: {review[4]}, Date: {review[5]}")
    conn.close()