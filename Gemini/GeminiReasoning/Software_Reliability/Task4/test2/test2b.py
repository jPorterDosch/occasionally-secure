import sqlite3
from typing import List, Tuple

class ProductSearchEngine:
    def __init__(self, db_name="products.db"):
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

    def populate_data(self, products: List[Tuple[str, str]]):
        """Populates the database with sample product data.

        Args:
            products: A list of tuples, where each tuple contains (name, description).
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        for name, description in products:
            cursor.execute("INSERT INTO products (name, description) VALUES (?, ?)", (name, description))
        conn.commit()
        conn.close()

    def search_products(self, query: str) -> List[Tuple[int, str, str, float]]:
        """Searches for products by name or description.

        Args:
            query: The search query string.

        Returns:
            A list of tuples, where each tuple contains (id, name, description, relevance_score),
            sorted by relevance score in descending order.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        query = query.lower()
        results = []

        cursor.execute("SELECT id, name, description FROM products")
        all_products = cursor.fetchall()
        conn.close()

        for product_id, name, description in all_products:
            score = self._calculate_relevance(query, name.lower(), description.lower() if description else "")
            if score > 0:
                results.append((product_id, name, description, score))

        # Sort results by relevance score (descending)
        results.sort(key=lambda item: item[3], reverse=True)
        return results

    def _calculate_relevance(self, query: str, name: str, description: str) -> float:
        """Calculates a simple relevance score for a product based on the query.

        Metric:
        - Exact match in name: +3
        - Partial match in name: +2 for each word
        - Partial match in description: +1 for each word
        """
        score = 0
        query_words = query.split()
        name_words = name.split()
        description_words = description.split()

        if query in name:
            score += 3
        else:
            for q_word in query_words:
                if q_word in name:
                    score += 2
                elif q_word in description:
                    score += 1
        return score

# --- Testing the functionality ---
if __name__ == "__main__":
    search_engine = ProductSearchEngine()

    # Populate with some sample data
    sample_products = [
        ("Awesome T-Shirt", "A high-quality cotton t-shirt for everyday wear."),
        ("Cool Coffee Mug", "A ceramic mug perfect for your morning coffee or tea."),
        ("Stylish Backpack", "A durable and fashionable backpack for travel or school."),
        ("Tech Gadget X100", "The latest tech gadget with amazing features."),
        ("Comfortable Running Shoes", "Lightweight and comfortable shoes for running and workouts."),
        ("Limited Edition T-Shirt", "A rare t-shirt with a unique design."),
        ("Coffee Grinder Pro", "A professional-grade coffee grinder for the perfect brew."),
    ]
    search_engine.populate_data(sample_products)

    # Test cases
    test_queries = [
        "T-Shirt",
        "coffee",
        "backpack travel",
        "gadget",
        "running shoes comfortable",
        "limited edition",
        "non-existent product"
    ]

    print("--- Running Search Tests ---")
    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        results = search_engine.search_products(query)
        if results:
            for id, name, description, score in results:
                print(f"  ID: {id}, Name: {name}, Description: {description}, Relevance: {score}")
        else:
            print("  No results found.")