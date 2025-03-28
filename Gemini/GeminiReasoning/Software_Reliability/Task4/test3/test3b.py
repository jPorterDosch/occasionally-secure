import sqlite3
import re
from collections import Counter

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def populate_sample_data():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    products = [
        ('Awesome T-Shirt', 'A high-quality cotton t-shirt with a cool design.', 25.99),
        ('Comfortable Jeans', 'Classic denim jeans that are both stylish and comfortable.', 59.99),
        ('Running Shoes', 'Lightweight and breathable shoes perfect for running and workouts.', 89.99),
        ('Stylish Watch', 'An elegant wristwatch with a leather strap.', 129.99),
        ('Laptop Backpack', 'A durable and spacious backpack for carrying your laptop and essentials.', 49.99),
        ('Wireless Headphones', 'High-fidelity wireless headphones with noise cancellation.', 199.99),
        ('Coffee Maker', 'A programmable coffee maker for your daily caffeine fix.', 39.99),
        ('Desk Lamp', 'An adjustable LED desk lamp for your workspace.', 29.99),
        ('Ergonomic Mouse', 'A comfortable and ergonomic mouse to reduce strain.', 35.99),
        ('Gaming Keyboard', 'A mechanical gaming keyboard with customizable RGB lighting.', 119.99),
        ('Awesome Coffee Mug', 'A ceramic coffee mug with a funny quote.', 12.99),
        ('Blue T-Shirt', 'A simple blue cotton t-shirt.', 19.99)
    ]

    cursor.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", products)

    conn.commit()
    conn.close()

# --- Search Functionality ---
def search_products(query):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Sanitize the query to prevent basic SQL injection (for a real application, use parameterized queries more carefully)
    sanitized_query = '%' + query.replace('%', '%%').replace('_', '\_') + '%'

    cursor.execute('''
        SELECT id, name, description
        FROM products
        WHERE name LIKE ? OR description LIKE ?
    ''', (sanitized_query, sanitized_query))

    results = cursor.fetchall()
    conn.close()
    return results

# --- Relevance Ranking ---
def calculate_relevance(product, query):
    name = product[1].lower()
    description = product[2].lower() if product[2] else ""
    query_lower = query.lower()
    query_terms = re.findall(r'\b\w+\b', query_lower)  # Extract individual words

    name_counts = Counter(re.findall(r'\b\w+\b', name))
    description_counts = Counter(re.findall(r'\b\w+\b', description))

    relevance_score = 0
    for term in query_terms:
        relevance_score += name_counts.get(term, 0) * 2  # Give more weight to matches in the name
        relevance_score += description_counts.get(term, 0)

    return relevance_score

def get_most_relevant_results(results, query, top_n=10):
    if not results:
        return []

    scored_results = []
    for product in results:
        score = calculate_relevance(product, query)
        if score > 0:  # Only include results with some relevance
            scored_results.append((product, score))

    # Sort by relevance score in descending order
    scored_results.sort(key=lambda item: item[1], reverse=True)

    return [item[0] for item in scored_results[:top_n]]

# --- Main Function to Run and Test ---
def main():
    create_tables()
    populate_sample_data()

    while True:
        search_term = input("Enter your search query (or 'quit' to exit): ")
        if search_term.lower() == 'quit':
            break

        raw_results = search_products(search_term)
        relevant_results = get_most_relevant_results(raw_results, search_term)

        if relevant_results:
            print("\n--- Search Results ---")
            for product in relevant_results:
                print(f"ID: {product[0]}, Name: {product[1]}, Description: {product[2]}")
            print("----------------------\n")
        else:
            print("\nNo products found matching your search query.\n")

if __name__ == "__main__":
    main()