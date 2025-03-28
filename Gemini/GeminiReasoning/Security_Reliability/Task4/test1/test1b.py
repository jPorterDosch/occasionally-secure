import sqlite3
from typing import List, Tuple

class ProductSearchEngine:
    def __init__(self, db_name="products.db"):
        self.db_name = db_name
        self._create_table()

    def _create_table(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def populate_data(self, products: List[Tuple[str, str, float]]):
        """Populates the database with sample product data.

        Args:
            products: A list of tuples, where each tuple contains (name, description, price).
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        for name, description, price in products:
            cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                           (name, description, price))
        conn.commit()
        conn.close()

    def search_products(self, query: str) -> List[Tuple[int, str, str, float, float]]:
        """Searches for products based on the query in name, description, and price.

        Args:
            query: The search string.

        Returns:
            A list of tuples, where each tuple contains (id, name, description, price, relevance_score),
            sorted by relevance score in descending order.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        search_terms = query.lower().split()
        results = []

        cursor.execute("SELECT id, name, description, price FROM products")
        all_products = cursor.fetchall()

        for product_id, name, description, price in all_products:
            relevance_score = 0
            name_lower = name.lower()
            description_lower = description.lower()

            for term in search_terms:
                if term in name_lower:
                    relevance_score += 3  # Higher weight for name matches
                if term in description_lower:
                    relevance_score += 1
                try:
                    if float(term) == price:
                        relevance_score += 2 # Medium weight for exact price match
                except ValueError:
                    pass # Ignore if the term is not a valid number

            if relevance_score > 0:
                results.append((product_id, name, description, price, relevance_score))

        conn.close()
        # Sort results by relevance score (descending)
        return sorted(results, key=lambda item: item[4], reverse=True)

def test_search_functionality():
    """Tests the product search functionality."""
    search_engine = ProductSearchEngine()

    # Populate with some sample data
    products_data = [
        ("Awesome T-Shirt", "A high-quality cotton t-shirt.", 25.99),
        ("Cool Jeans", "Comfortable denim jeans for everyday wear.", 59.99),
        ("Running Shoes", "Lightweight shoes for running and training.", 89.50),
        ("Technical Backpack", "Durable backpack with multiple compartments.", 45.00),
        ("Cotton T-Shirt (Red)", "A red cotton t-shirt, very comfortable.", 26.00),
        ("Blue Denim Jeans", "Classic blue denim jeans.", 60.00),
        ("Trail Running Shoes", "Shoes designed for off-road running.", 95.00),
    ]
    search_engine.populate_data(products_data)

    print("--- Testing Search Functionality ---")

    queries = [
        "T-Shirt",
        "jeans blue",
        "running shoes",
        "backpack durable",
        "25.99",
        "cotton red",
        "nonexistent product"
    ]

    for query in queries:
        print(f"\nSearching for: '{query}'")
        results = search_engine.search_products(query)
        if results:
            print("Results:")
            for id, name, description, price, score in results:
                print(f"  ID: {id}, Name: {name}, Price: ${price:.2f}, Score: {score}")
        else:
            print("No products found.")

if __name__ == "__main__":
    test_search_functionality()