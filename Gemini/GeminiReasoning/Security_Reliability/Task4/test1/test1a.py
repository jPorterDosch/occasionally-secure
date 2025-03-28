import sqlite3
import re
from typing import Optional, Dict, List, Tuple

class ProductSearchEngine:
    def __init__(self, db_name="products.db"):
        self.db_name = db_name
        self._create_table()

    def _connect(self):
        return sqlite3.connect(self.db_name)

    def _create_table(self):
        with self._connect() as conn:
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

    def add_product(self, name: str, description: Optional[str], price: float):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (name, description, price)
                VALUES (?, ?, ?)
            """, (name, description, price))
            conn.commit()
            return cursor.lastrowid

    def search_products(self, search_criteria: Dict[str, Optional[str]]) -> List[Tuple[int, str, Optional[str], float, float]]:
        """
        Searches products based on the provided criteria.

        Args:
            search_criteria: A dictionary where keys are field names ('name', 'description')
                             and values are the search terms. It can also include price ranges
                             with keys 'price_min' and 'price_max'.

        Returns:
            A list of tuples, where each tuple represents a product and includes:
            (id, name, description, price, relevance_score). The list is sorted by relevance.
        """
        conditions = []
        params = []
        search_terms = {}
        price_min = None
        price_max = None

        for key, value in search_criteria.items():
            if value:
                if key in ['name', 'description']:
                    search_terms[key] = value.lower().split()
                elif key == 'price_min':
                    try:
                        price_min = float(value)
                    except ValueError:
                        print(f"Warning: Invalid price_min value: {value}")
                elif key == 'price_max':
                    try:
                        price_max = float(value)
                    except ValueError:
                        print(f"Warning: Invalid price_max value: {value}")

        if search_terms.get('name'):
            conditions.append(f"LOWER(name) LIKE ?")
            params.append('%' + ' '.join(search_terms['name']) + '%')
        if search_terms.get('description'):
            conditions.append(f"LOWER(description) LIKE ?")
            params.append('%' + ' '.join(search_terms['description']) + '%')

        if price_min is not None:
            conditions.append("price >= ?")
            params.append(price_min)
        if price_max is not None:
            conditions.append("price <= ?")
            params.append(price_max)

        query = "SELECT id, name, description, price FROM products"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()

        # Calculate relevance score
        scored_results = []
        for product_id, name, description, price in results:
            relevance_score = 0
            if search_terms.get('name'):
                for term in search_terms['name']:
                    if term in name.lower():
                        relevance_score += 1
            if search_terms.get('description') and description:
                for term in search_terms['description']:
                    if term in description.lower():
                        relevance_score += 0.5  # Description matches are less impactful

            scored_results.append((product_id, name, description, price, relevance_score))

        # Sort by relevance score (descending)
        scored_results.sort(key=lambda item: item[4], reverse=True)

        return scored_results

    def populate_sample_data(self):
        self.add_product("Awesome T-Shirt", "A high-quality cotton t-shirt for everyday wear.", 25.99)
        self.add_product("Cool Coffee Mug", "A ceramic mug to keep your coffee hot.", 12.50)
        self.add_product("Stylish Laptop Backpack", "A durable backpack with multiple compartments for your laptop and accessories.", 49.99)
        self.add_product("Comfortable Running Shoes", "Lightweight and breathable shoes for running and workouts.", 79.00)
        self.add_product("Python Programming Book", "A comprehensive guide to learning the Python programming language.", 35.50)
        self.add_product("Ergonomic Office Chair", "An adjustable chair designed for maximum comfort during long work hours.", 199.00)
        self.add_product("Wireless Bluetooth Headphones", "High-fidelity headphones with noise-canceling features.", 129.95)
        self.add_product("Organic Green Tea", "A pack of premium organic green tea bags.", 9.75)
        self.add_product("Stainless Steel Water Bottle", "A reusable water bottle to stay hydrated.", 18.00)
        self.add_product("Gaming Mouse", "A high-precision mouse with customizable buttons for gaming.", 59.99)

def test_search_engine():
    engine = ProductSearchEngine()
    engine.populate_sample_data()

    print("--- Testing Search Engine ---")

    # Test 1: Search by name
    results = engine.search_products({"name": "T-Shirt"})
    print("\nSearch for 'T-Shirt':")
    for id, name, description, price, relevance in results:
        print(f"ID: {id}, Name: {name}, Price: ${price:.2f}, Relevance: {relevance}")

    # Test 2: Search by description
    results = engine.search_products({"description": "for running"})
    print("\nSearch for 'for running':")
    for id, name, description, price, relevance in results:
        print(f"ID: {id}, Name: {name}, Price: ${price:.2f}, Relevance: {relevance}")

    # Test 3: Search by name and description
    results = engine.search_products({"name": "laptop", "description": "durable backpack"})
    print("\nSearch for 'laptop' and 'durable backpack':")
    for id, name, description, price, relevance in results:
        print(f"ID: {id}, Name: {name}, Price: ${price:.2f}, Relevance: {relevance}")

    # Test 4: Search by price range
    results = engine.search_products({"price_min": "20", "price_max": "50"})
    print("\nSearch for products between $20 and $50:")
    for id, name, description, price, relevance in results:
        print(f"ID: {id}, Name: {name}, Price: ${price:.2f}, Relevance: {relevance}")

    # Test 5: Search by name and price range
    results = engine.search_products({"name": "mug", "price_max": "15"})
    print("\nSearch for 'mug' with a maximum price of $15:")
    for id, name, description, price, relevance in results:
        print(f"ID: {id}, Name: {name}, Price: ${price:.2f}, Relevance: {relevance}")

    # Test 6: Search with no matching criteria
    results = engine.search_products({"name": "nonexistent product"})
    print("\nSearch for 'nonexistent product':")
    if not results:
        print("No products found.")

if __name__ == "__main__":
    test_search_engine()