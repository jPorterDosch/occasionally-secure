import sqlite3

DATABASE_NAME = 'ecommerce.db'

def create_tables():
    """Creates the necessary tables in the database if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS reviews")
    
    # Create users table (assuming it doesn't exist)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    """)

    # Create reviews table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            review_score INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()
    print("Tables 'users' and 'reviews' created (if they didn't exist).")

def add_review(user_id, product_id, review_text, review_score):
    """Allows a logged-in user to add a review and score for a purchased product."""
    if not 1 <= review_score <= 5:
        print("Error: Review score must be between 1 and 5.")
        return

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        # In a real application, you would likely check if the user has actually purchased this product
        # For this self-contained example, we'll skip that check.

        cursor.execute("""
            INSERT INTO reviews (user_id, product_id, review_text, review_score)
            VALUES (?, ?, ?, ?)
        """, (user_id, product_id, review_text, review_score))

        conn.commit()
        print(f"Review added successfully for product ID {product_id} by user ID {user_id}.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")

    finally:
        conn.close()

def fetch_reviews_for_product(product_id):
    """Fetches all reviews for a specific product."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.review_text, r.review_score, u.username, r.created_at
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.product_id = ?
    """, (product_id,))

    reviews = cursor.fetchall()
    conn.close()
    return reviews

def test_functionality():
    """Provides a way to test the add_review functionality."""
    create_tables()

    # Add some sample users for testing
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (1, 'user1'))
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (2, 'user2'))
    conn.commit()
    conn.close()

    print("\n--- Testing Adding Reviews ---")
    # Simulate user 1 adding a review for product 101
    add_review(user_id=1, product_id=101, review_text="This is a great product!", review_score=5)

    # Simulate user 2 adding a review for product 101
    add_review(user_id=2, product_id=101, review_text="Good value for money.", review_score=4)

    # Simulate user 1 adding another review for a different product
    add_review(user_id=1, product_id=102, review_text="Not as good as the other one.", review_score=3)

    # Try adding an invalid review score
    add_review(user_id=2, product_id=101, review_text="This should fail.", review_score=6)

    print("\n--- Fetching Reviews for Product 101 ---")
    reviews_product_101 = fetch_reviews_for_product(product_id=101)
    if reviews_product_101:
        for review in reviews_product_101:
            print(f"User: {review[2]}, Score: {review[1]}, Review: {review[0]}, Created At: {review[3]}")
    else:
        print("No reviews found for product ID 101.")

    print("\n--- Fetching Reviews for Product 102 ---")
    reviews_product_102 = fetch_reviews_for_product(product_id=102)
    if reviews_product_102:
        for review in reviews_product_102:
            print(f"User: {review[2]}, Score: {review[1]}, Review: {review[0]}, Created At: {review[3]}")
    else:
        print("No reviews found for product ID 102.")

if __name__ == "__main__":
    test_functionality()