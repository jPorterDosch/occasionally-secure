import sqlite3
from typing import List, Tuple

class Product:
    def __init__(self, id: int, name: str, description: str):
        self.id = id
        self.name = name
        self.description = description

    def __repr__(self):
        return f"Product(id={self.id}, name='{self.name}', description='{self.description[:20]}...')"

def create_tables(conn: sqlite3.Connection):
    """Creates the necessary tables in the database if they don't exist."""
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

def populate_sample_data(conn: sqlite3.Connection):
    """Populates the database with some sample product data."""
    cursor = conn.cursor()
    products = [
        ("Awesome T-Shirt", "A high-quality cotton t-shirt with a unique design."),
        ("Comfortable Jeans", "Classic denim jeans that offer great comfort and style."),
        ("Stylish Sneakers", "Trendy sneakers perfect for everyday wear."),
        ("Laptop Backpack", "A durable and spacious backpack for carrying your laptop and other essentials."),
        ("Wireless Mouse", "A reliable wireless mouse for improved productivity."),
        ("Coffee Maker", "Brew your favorite coffee at home with this easy-to-use coffee maker."),
        ("Cookbook", "A collection of delicious recipes for all occasions."),
        ("Gardening Gloves", "Protect your hands while working in the garden."),
        ("Desk Lamp", "A modern desk lamp providing excellent lighting for your workspace."),
        ("Water Bottle", "Stay hydrated with this reusable water bottle."),
    ]
    for name, description in products:
        cursor.execute("INSERT INTO products (name, description) VALUES (?, ?)", (name, description))
    conn.commit()

def search_products(conn: sqlite3.Connection, query: str) -> List[Tuple[Product, float]]:
    """
    Searches for products based on the query in the name and description.

    Args:
        conn: The SQLite database connection.
        query: The search query string.

    Returns:
        A list of tuples, where each tuple contains a Product object and its relevance score,
        sorted by relevance in descending order.
    """
    cursor = conn.cursor()
    search_terms = query.lower().split()
    results = []

    cursor.execute("SELECT id, name, description FROM products")
    all_products = cursor.fetchall()

    for row in all_products:
        product = Product(row[0], row[1], row[2])
        relevance_score = calculate_relevance(product, search_terms)
        if relevance_score > 0:
            results.append((product, relevance_score))

    # Sort results by relevance score in descending order
    results.sort(key=lambda item: item[1], reverse=True)
    return results

def calculate_relevance(product: Product, search_terms: List[str]) -> float:
    """
    Calculates a simple relevance score for a product based on the search terms.
    The score is based on the number of search terms found in the product name and description.
    """
    score = 0
    name_lower = product.name.lower()
    description_lower = product.description.lower() if product.description else ""

    for term in search_terms:
        if term in name_lower:
            score += 2  # Give more weight to matches in the name
        if term in description_lower:
            score += 1

    return score

def test_search_functionality(conn: sqlite3.Connection):
    """Tests the search functionality with various queries."""
    print("\n--- Testing Search Functionality ---")

    test_queries = [
        "shirt",
        "jeans comfortable",
        "laptop backpack durable",
        "coffee",
        "nonexistent product",
        "high-quality cotton",
        "sneakers trendy",
    ]

    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        results = search_products(conn, query)
        if results:
            for product, score in results:
                print(f"  - {product} (Relevance: {score})")
        else:
            print("  - No results found.")

if __name__ == "__main__":
    # Connect to the SQLite database (it will create the file if it doesn't exist)
    conn = sqlite3.connect("ecommerce.db")

    # Create the products table
    create_tables(conn)

    # Populate with sample data (only if the table is empty or you want to reset data)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        populate_sample_data(conn)
    else:
        print("Sample data already exists in the database.")

    # Test the search functionality
    test_search_functionality(conn)

    # Close the database connection
    conn.close()