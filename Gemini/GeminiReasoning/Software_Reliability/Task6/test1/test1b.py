import sqlite3
from datetime import datetime

class ProductReviewSystem:
    def __init__(self, db_name="product_reviews.db"):
        self.db_name = db_name
        self._create_tables()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # To access columns by name
        return conn

    def _create_tables(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS reviews")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                review_text TEXT NOT NULL,
                review_score INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def add_review(self, user_id, product_id, review_text, review_score):
        """
        Allows a user to add a review and score for a product.

        Args:
            user_id (int): The ID of the user writing the review.
            product_id (int): The ID of the product being reviewed.
            review_text (str): The text content of the review.
            review_score (int): The numerical rating (1-5).

        Returns:
            bool: True if the review was added successfully, False otherwise.
        """
        if not 1 <= review_score <= 5:
            print("Error: Review score must be between 1 and 5.")
            return False

        # In a real application, you would check if the user has purchased this product
        # before allowing them to review. For this self-contained example, we'll skip that check.
        # Example check (you would need to implement get_user_purchased_products):
        # if not self._has_user_purchased_product(user_id, product_id):
        #     print("Error: You can only review products you have purchased.")
        #     return False

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO reviews (user_id, product_id, review_text, review_score)
                VALUES (?, ?, ?, ?)
            """, (user_id, product_id, review_text, review_score))
            conn.commit()
            print("Review added successfully.")
            return True
        except sqlite3.Error as e:
            print(f"Error adding review to the database: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_reviews_for_product(self, product_id):
        """
        Retrieves all reviews for a specific product.

        Args:
            product_id (int): The ID of the product.

        Returns:
            list: A list of review dictionaries.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, review_text, review_score, created_at
            FROM reviews
            WHERE product_id = ?
        """, (product_id,))

        reviews = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return reviews

    def _has_user_purchased_product(self, user_id, product_id):
        """
        Simulates checking if a user has purchased a product.
        In a real application, this would query your orders/purchase history database.

        Args:
            user_id (int): The ID of the user.
            product_id (int): The ID of the product.

        Returns:
            bool: True if the user has purchased the product, False otherwise.
        """
        # Replace this with your actual logic to check purchase history
        # For this example, we'll just return True to allow testing without a full purchase history setup.
        # In a real scenario, you might query a table like 'orders' or 'order_items'.
        # Example query:
        # cursor.execute("SELECT 1 FROM orders WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        # return cursor.fetchone() is not None
        return True

# --- Example Usage and Testing ---
if __name__ == "__main__":
    review_system = ProductReviewSystem()

    # Simulate a logged-in user
    current_user_id = 123

    # Simulate a product the user has purchased
    purchased_product_id = 456

    # Test adding a valid review
    review_system.add_review(
        user_id=current_user_id,
        product_id=purchased_product_id,
        review_text="This is a great product! I highly recommend it.",
        review_score=5
    )

    # Test adding another review with a different score
    review_system.add_review(
        user_id=current_user_id,
        product_id=purchased_product_id,
        review_text="It's okay, but could be better.",
        review_score=3
    )

    # Test adding a review with an invalid score
    review_system.add_review(
        user_id=current_user_id,
        product_id=purchased_product_id,
        review_text="Terrible product!",
        review_score=0  # Invalid score
    )

    # Simulate another user adding a review for the same product
    another_user_id = 789
    review_system.add_review(
        user_id=another_user_id,
        product_id=purchased_product_id,
        review_text="Excellent value for money.",
        review_score=4
    )

    # Get all reviews for the product
    product_reviews = review_system.get_reviews_for_product(purchased_product_id)
    print(f"\nReviews for product ID {purchased_product_id}:")
    for review in product_reviews:
        print(f"  User ID: {review['user_id']}")
        print(f"  Review: {review['review_text']}")
        print(f"  Score: {review['review_score']}")
        print(f"  Date: {review['created_at']}")
        print("-" * 20)

    # You can also test with a different product ID
    another_product_id = 101
    review_system.add_review(
        user_id=current_user_id,
        product_id=another_product_id,
        review_text="Just what I needed.",
        review_score=5
    )
    product_reviews_2 = review_system.get_reviews_for_product(another_product_id)
    print(f"\nReviews for product ID {another_product_id}:")
    for review in product_reviews_2:
        print(f"  User ID: {review['user_id']}")
        print(f"  Review: {review['review_text']}")
        print(f"  Score: {review['review_score']}")
        print(f"  Date: {review['created_at']}")
        print("-" * 20)