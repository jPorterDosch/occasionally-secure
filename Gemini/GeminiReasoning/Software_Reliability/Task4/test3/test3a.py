import sqlite3
from typing import List, Tuple

class Product:
    def __init__(self, id: int, name: str, description: str):
        self.id = id
        self.name = name
        self.description = description

    def __repr__(self):
        return f"Product(id={self.id}, name='{self.name}', description='{self.description}')"

def create_tables():
    """Creates the 'products' table in the database if it doesn't exist."""
    conn = sqlite3.connect('ecommerce.db')
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

def populate_database():
    """Adds some sample product data to the database."""
    products_data = [
        ("Awesome T-Shirt", "A high-quality cotton t-shirt perfect for any occasion."),
        ("Cool Coffee Mug", "A ceramic mug that keeps your coffee hot for longer."),
        ("Stylish Laptop Bag", "A durable and fashionable bag to protect your laptop."),
        ("Wireless Mouse", "A comfortable and ergonomic wireless mouse for efficient work."),
        ("Ergonomic Keyboard", "A keyboard designed for comfortable and long typing sessions."),
        ("Running Shoes", "Lightweight and supportive shoes for your daily runs."),
        ("Mystery Novel", "A thrilling mystery novel that will keep you on the edge of your seat."),
        ("Gardening Gloves", "Durable gloves to protect your hands while gardening."),
        ("Smartphone Case", "A protective case for your smartphone."),
        ("Bluetooth Speaker", "A portable Bluetooth speaker with great sound quality."),
    ]
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO products (name, description) VALUES (?, ?)", products_data)
    conn.commit()
    conn.close()

def search_products(query: str) -> List[Tuple[Product, int]]:
    """
    Searches for products by name or description and returns the most relevant results.

    Args:
        query: The search query string.

    Returns:
        A list of tuples, where each tuple contains a Product object and its relevance score,
        sorted in descending order of relevance.
    """
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    query_lower = query.lower()
    search_terms = query_lower.split()
    results = []

    cursor.execute("SELECT id, name, description FROM products")
    products = [Product(row[0], row[1], row[2]) for row in cursor.fetchall()]

    for product in products:
        relevance_score = 0
        name_lower = product.name.lower()
        description_lower = product.description.lower()

        for term in search_terms:
            relevance_score += name_lower.count(term) * 2  # Give higher weight to matches in the name
            relevance_score += description_lower.count(term)

        if relevance_score > 0:
            results.append((product, relevance_score))

    # Sort results by relevance score in descending order
    results.sort(key=lambda item: item[1], reverse=True)
    conn.close()
    return results

def test_search_functionality():
    """Tests the search functionality with some sample queries."""
    print("Testing search functionality:")

    test_queries = [
        "t-shirt",
        "coffee mug",
        "laptop bag stylish",
        "wireless mouse ergonomic",
        "book",
        "gardening",
        "awesome product",
        "non-existent product"
    ]

    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        results = search_products(query)
        if results:
            for product, score in results:
                print(f"  - {product} (Relevance: {score})")
        else:
            print("  No results found.")

if __name__ == "__main__":
    # Initialize the database and populate with data
    create_tables()
    populate_database()

    # Test the search functionality
    test_search_functionality()