import sqlite3
from typing import List, Tuple

def initialize_database():
    """Initializes the SQLite database and creates the products table if it doesn't exist."""
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    # Add some sample products
    products = [
        ('Awesome T-Shirt', 'A high-quality cotton t-shirt perfect for any occasion.', 25.99),
        ('Cool Coffee Mug', 'A ceramic mug that keeps your coffee hot for longer.', 12.50),
        ('Stylish Laptop Bag', 'A durable and water-resistant bag to protect your laptop.', 49.99),
        ('Comfortable Running Shoes', 'Lightweight and breathable shoes for running and workouts.', 79.00),
        ('Funny Novelty Socks', 'Socks with a hilarious design to brighten your day.', 9.75),
        ('Another Awesome T-Shirt', 'A different style of our popular awesome t-shirt.', 27.50),
    ]
    cursor.executemany("INSERT OR IGNORE INTO products (name, description, price) VALUES (?, ?, ?)", products)
    conn.commit()
    conn.close()

def search_products(search_term: str = None, price_min: float = None, price_max: float = None) -> List[Tuple]:
    """
    Searches for products based on the provided criteria.

    Args:
        search_term: A string to search for in the name and description.
        price_min: The minimum price to filter by.
        price_max: The maximum price to filter by.

    Returns:
        A list of tuples, where each tuple contains (product_id, name, description, price, relevance_score).
        The list is sorted by relevance score in descending order.
    """
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    conditions = []
    params = []

    if search_term:
        search_words = search_term.lower().split()
        name_conditions = ' OR '.join(['lower(name) LIKE ?'] * len(search_words))
        description_conditions = ' OR '.join(['lower(description) LIKE ?'] * len(search_words))
        conditions.append(f'({name_conditions} OR {description_conditions})')
        for word in search_words:
            params.extend([f'%{word}%'] * 2)  # Two placeholders for name and description

    if price_min is not None:
        conditions.append('price >= ?')
        params.append(price_min)

    if price_max is not None:
        conditions.append('price <= ?')
        params.append(price_max)

    query = "SELECT id, name, description, price FROM products"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    # Calculate a simple relevance score
    scored_results = []
    if search_term:
        search_words = set(search_term.lower().split())
        for product in results:
            product_id, name, description, price = product
            score = 0
            name_lower = name.lower()
            description_lower = (description or "").lower()
            for word in search_words:
                if word in name_lower:
                    score += 2  # Higher score for matches in the name
                if word in description_lower:
                    score += 1
            scored_results.append((product_id, name, description, price, score))
        scored_results.sort(key=lambda item: item[4], reverse=True)
    else:
        scored_results = [(p[0], p[1], p[2], p[3], 0) for p in results]

    return scored_results

def test_search_functionality():
    """Tests the search functionality with various queries."""
    initialize_database()

    print("--- Testing Search Functionality ---")

    print("\nSearching for 'T-Shirt':")
    results = search_products(search_term='T-Shirt')
    for result in results:
        print(f"ID: {result[0]}, Name: {result[1]}, Price: ${result[3]}, Relevance: {result[4]}")

    print("\nSearching for 'coffee mug':")
    results = search_products(search_term='coffee mug')
    for result in results:
        print(f"ID: {result[0]}, Name: {result[1]}, Price: ${result[3]}, Relevance: {result[4]}")

    print("\nSearching for 'awesome':")
    results = search_products(search_term='awesome')
    for result in results:
        print(f"ID: {result[0]}, Name: {result[1]}, Price: ${result[3]}, Relevance: {result[4]}")

    print("\nSearching with price filter (min $20):")
    results = search_products(price_min=20.0)
    for result in results:
        print(f"ID: {result[0]}, Name: {result[1]}, Price: ${result[3]}, Relevance: {result[4]}")

    print("\nSearching with price filter (max $50):")
    results = search_products(price_max=50.0)
    for result in results:
        print(f"ID: {result[0]}, Name: {result[1]}, Price: ${result[3]}, Relevance: {result[4]}")

    print("\nSearching with price range ($20 - $60):")
    results = search_products(price_min=20.0, price_max=60.0)
    for result in results:
        print(f"ID: {result[0]}, Name: {result[1]}, Price: ${result[3]}, Relevance: {result[4]}")

    print("\nSearching for 'shirt' within price range ($20 - $30):")
    results = search_products(search_term='shirt', price_min=20.0, price_max=30.0)
    for result in results:
        print(f"ID: {result[0]}, Name: {result[1]}, Price: ${result[3]}, Relevance: {result[4]}")

if __name__ == "__main__":
    test_search_functionality()