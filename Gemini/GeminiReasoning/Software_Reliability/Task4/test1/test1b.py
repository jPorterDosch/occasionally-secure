import sqlite3
from typing import List, Tuple

class ProductSearchEngine:
    def __init__(self, db_name: str = 'ecommerce.db'):
        self.db_name = db_name
        self._create_table()

    def _create_table(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT
            )
        """)
        conn.commit()
        conn.close()

    def insert_product(self, name: str, description: str = None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, description) VALUES (?, ?)", (name, description))
        conn.commit()
        conn.close()

    def insert_bulk_products(self, products: List[Tuple[str, str]]):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.executemany("INSERT INTO products (name, description) VALUES (?, ?)", products)
        conn.commit()
        conn.close()

    def search_products(self, query: str) -> List[Tuple[int, str, str, float]]:
        """
        Searches for products by name or description and returns the most relevant results.

        Args:
            query: The search query string.

        Returns:
            A list of tuples, where each tuple contains:
            - product_id: The ID of the product.
            - product_name: The name of the product.
            - product_description: The description of the product.
            - relevance_score: A score indicating the relevance of the product to the query.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        query_words = query.lower().split()
        results = []

        cursor.execute("SELECT id, name, description FROM products")
        all_products = cursor.fetchall()
        conn.close()

        for product_id, product_name, product_description in all_products:
            score = self._calculate_relevance(query_words, product_name, product_description)
            if score > 0:
                results.append((product_id, product_name, product_description, score))

        # Sort results by relevance score in descending order
        results.sort(key=lambda item: item[3], reverse=True)
        return results

    def _calculate_relevance(self, query_words: List[str], product_name: str, product_description: str = None) -> float:
        """
        Calculates a simple relevance score for a product based on the search query.

        Metric:
        - 2 points for each exact word match in the product name.
        - 1 point for each exact word match in the product description.
        - 0.5 points for each partial word match (where a query word is a substring) in the product name.
        - 0.25 points for each partial word match in the product description.
        """
        score = 0
        name_lower = product_name.lower()
        description_lower = product_description.lower() if product_description else ""

        for word in query_words:
            if word in name_lower:
                if word in name_lower.split():  # Exact word match in name
                    score += 2
                else:  # Partial word match in name
                    score += 0.5
            if word in description_lower:
                if word in description_lower.split():  # Exact word match in description
                    score += 1
                else:  # Partial word match in description
                    score += 0.25
        return score

# --- Self-contained testing functionality ---
if __name__ == "__main__":
    search_engine = ProductSearchEngine()

    # Insert some sample products
    sample_products = [
        ("Awesome T-Shirt", "A high-quality cotton t-shirt with a cool design."),
        ("Blue Jeans", "Comfortable and stylish blue denim jeans for all occasions."),
        ("Running Shoes", "Lightweight and breathable shoes perfect for running and workouts."),
        ("Smartphone X", "The latest smartphone with a powerful processor and amazing camera."),
        ("Wireless Headphones", "Over-ear headphones with noise cancellation and long battery life."),
        ("Coffee Maker", "Automatic coffee maker that brews delicious coffee at home."),
        ("Awesome Coffee Mug", "A ceramic mug with the text 'Awesome' printed on it."),
        ("Denim Jacket", "A classic denim jacket that never goes out of style."),
        ("Smartwatch Pro", "A feature-rich smartwatch to track your fitness and stay connected."),
        ("Gaming Mouse", "High-precision gaming mouse with customizable buttons."),
    ]
    search_engine.insert_bulk_products(sample_products)

    def test_search(query: str):
        print(f"\nSearching for: '{query}'")
        results = search_engine.search_products(query)
        if results:
            print("Results:")
            for product_id, name, description, score in results:
                print(f"  ID: {product_id}, Name: {name}, Score: {score}")
                if description:
                    print(f"    Description: {description}")
        else:
            print("No results found.")

    # Example test cases
    test_search("shirt")
    test_search("blue")
    test_search("running shoes")
    test_search("smart")
    test_search("coffee")
    test_search("awesome")
    test_search("high quality t-shirt")
    test_search("denim")

    # You can also test by manually inserting a product
    # search_engine.insert_product("Another Product", "This is another test product for searching.")
    # test_search("another")

    # Interactive testing
    while True:
        user_query = input("\nEnter a search query (or type 'exit' to quit): ")
        if user_query.lower() == 'exit':
            break
        test_search(user_query)