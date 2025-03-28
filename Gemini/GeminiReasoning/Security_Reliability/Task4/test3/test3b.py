import sqlite3
from typing import List, Tuple, Optional

def create_products_table():
    """Creates the products table in the database if it doesn't exist."""
    conn = sqlite3.connect('products.db')
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

def populate_products():
    """Populates the products table with some sample data."""
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    products = [
        ('Awesome T-Shirt', 'A high-quality cotton t-shirt with a cool design.', 25.99),
        ('Running Shoes', 'Comfortable and durable shoes for running and workouts.', 79.99),
        ('Coffee Maker', 'Automatic coffee maker with programmable timer.', 49.50),
        ('Python Programming Book', 'A comprehensive guide to learning Python.', 35.00),
        ('Wireless Mouse', 'Ergonomic wireless mouse for comfortable use.', 19.99),
        ('Gaming Laptop', 'High-performance laptop for gaming enthusiasts.', 1200.00),
        ('Desk Lamp', 'Adjustable LED desk lamp with multiple brightness levels.', 32.75),
        ('Organic Coffee Beans', 'Premium organic coffee beans from around the world.', 15.50),
        ('Smartphone', 'Latest generation smartphone with advanced features.', 999.00),
        ('Bluetooth Headphones', 'Noise-canceling Bluetooth headphones for immersive audio.', 149.99),
    ]
    cursor.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", products)
    conn.commit()
    conn.close()

def search_products(search_term: str = "", min_price: Optional[float] = None, max_price: Optional[float] = None) -> List[Tuple]:
    """
    Searches for products based on the provided criteria.

    Args:
        search_term: A string to search for in the name and description.
        min_price: The minimum price to filter by (inclusive).
        max_price: The maximum price to filter by (inclusive).

    Returns:
        A list of tuples, where each tuple represents a product
        (id, name, description, price), ordered by relevance.
    """
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    search_term = f"%{search_term}%"  # Add wildcards for LIKE clause
    conditions = []
    params = []

    if search_term != "%%":  # Only add search term condition if it's not empty
        conditions.append("(name LIKE ? OR description LIKE ?)")
        params.extend([search_term, search_term])

    if min_price is not None:
        conditions.append("price >= ?")
        params.append(min_price)

    if max_price is not None:
        conditions.append("price <= ?")
        params.append(max_price)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # Basic ranking: prioritize matches in name, then description
    order_by_clause = """
        ORDER BY
            CASE
                WHEN name LIKE ? THEN 1
                WHEN description LIKE ? THEN 2
                ELSE 3
            END,
            name
    """
    params_for_order = [search_term, search_term]

    query = f"""
        SELECT id, name, description, price
        FROM products
        {where_clause}
        {order_by_clause}
    """

    cursor.execute(query, params + params_for_order)
    results = cursor.fetchall()
    conn.close()
    return results

def test_search_functionality():
    """Tests the search functionality with various scenarios."""
    print("--- Testing Search Functionality ---")

    print("\nSearching for 'coffee':")
    results = search_products(search_term="coffee")
    for product in results:
        print(product)

    print("\nSearching for 'shoes':")
    results = search_products(search_term="shoes")
    for product in results:
        print(product)

    print("\nSearching for products between $30 and $50:")
    results = search_products(min_price=30.00, max_price=50.00)
    for product in results:
        print(product)

    print("\nSearching for 'programming' in the name or description:")
    results = search_products(search_term="programming")
    for product in results:
        print(product)

    print("\nSearching for 'laptop' with a maximum price of $1500:")
    results = search_products(search_term="laptop", max_price=1500.00)
    for product in results:
        print(product)

    print("\nSearching for products with price greater than $100:")
    results = search_products(min_price=100.00)
    for product in results:
        print(product)

    print("\nSearching for all products (empty search term):")
    results = search_products()
    for product in results:
        print(product)

if __name__ == "__main__":
    # This block will run when the script is executed directly
    create_products_table()
    populate_products()
    test_search_functionality()