import sqlite3

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS user_purchases")
    cursor.execute("DROP TABLE IF EXISTS product_reviews")
    # Create users table (assuming it doesn't exist) - for simulating logged-in users and purchases
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL
    )
    """)

    # Create products table (assuming it doesn't exist) - for simulating products
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    # Create a table to track user purchases (assuming it doesn't exist)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_purchases (
        purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    """)

    # Create the product reviews table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        review_text TEXT NOT NULL,
        review_score INTEGER NOT NULL CHECK (review_score BETWEEN 1 AND 5),
        review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    """)

    conn.commit()
    conn.close()
    print("Database tables created (if they didn't exist).")

# --- Sample Data Insertion (for testing) ---
def insert_sample_data():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Add some sample users
    users = [('user1',), ('user2',)]
    cursor.executemany("INSERT OR IGNORE INTO users (username) VALUES (?)", users)

    # Add some sample products
    products = [('Laptop',), ('Mouse',), ('Keyboard',)]
    cursor.executemany("INSERT OR IGNORE INTO products (name) VALUES (?)", products)

    # Simulate user purchases
    purchases = [
        (1, 1),  # user1 purchased Laptop
        (1, 2),  # user1 purchased Mouse
        (2, 3),  # user2 purchased Keyboard
    ]
    cursor.executemany("INSERT OR IGNORE INTO user_purchases (user_id, product_id) VALUES (?, ?)", purchases)

    conn.commit()
    conn.close()
    print("Sample users, products, and purchases added.")

# --- Function to Add Review ---
def add_product_review(user_id, product_id, review_text, review_score):
    if not (1 <= review_score <= 5):
        print("Invalid review score. Score must be between 1 and 5.")
        return False

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # In a real application, you would likely check if the user has actually purchased the product
    # before allowing them to review. For this self-contained example, we'll skip that strict check.
    # You could implement a check like this:
    # cursor.execute("SELECT 1 FROM user_purchases WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    # if cursor.fetchone() is None:
    #     print("User has not purchased this product and cannot leave a review.")
    #     conn.close()
    #     return False

    try:
        cursor.execute("""
        INSERT INTO product_reviews (user_id, product_id, review_text, review_score)
        VALUES (?, ?, ?, ?)
        """, (user_id, product_id, review_text, review_score))
        conn.commit()
        print(f"Review added successfully for product ID {product_id} by user ID {user_id}.")
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error adding review: {e}")
        conn.close()
        return False

# --- Function to Display Reviews for a Product (for testing) ---
def get_product_reviews(product_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT r.review_text, r.review_score, u.username, r.review_date
    FROM product_reviews r
    JOIN users u ON r.user_id = u.user_id
    WHERE r.product_id = ?
    """, (product_id,))
    reviews = cursor.fetchall()
    conn.close()
    if reviews:
        print(f"\nReviews for Product ID {product_id}:")
        for review in reviews:
            text, score, username, date = review
            print(f"- '{text}' (Score: {score}) by {username} on {date}")
    else:
        print(f"\nNo reviews found for Product ID {product_id}.")

# --- Testing the Functionality ---
if __name__ == "__main__":
    # 1. Create database tables
    create_tables()

    # 2. Insert sample data (if you want to test with pre-existing users and products)
    insert_sample_data()

    # --- Simulate a logged-in user ---
    logged_in_user_id = 1  # Assuming user with ID 1 is logged in

    # --- Example usage: Adding reviews ---
    print("\n--- Adding Reviews ---")
    add_product_review(user_id=logged_in_user_id, product_id=1, review_text="This laptop is great!", review_score=5)
    add_product_review(user_id=logged_in_user_id, product_id=2, review_text="The mouse works well.", review_score=4)
    add_product_review(user_id=2, product_id=3, review_text="Good keyboard for the price.", review_score=3)
    add_product_review(user_id=1, product_id=1, review_text="Second review for the same product.", review_score=4)
    add_product_review(user_id=logged_in_user_id, product_id=1, review_text="Trying an invalid score.", review_score=6) # This should fail

    # --- Example usage: Displaying reviews for a product ---
    print("\n--- Displaying Reviews ---")
    get_product_reviews(product_id=1)
    get_product_reviews(product_id=2)
    get_product_reviews(product_id=3)
    get_product_reviews(product_id=4) # Product that might not have reviews