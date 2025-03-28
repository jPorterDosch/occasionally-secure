import sqlite3
from flask import Flask, request, jsonify
from typing import Optional, Tuple

# --- Database Setup ---
DATABASE = 'products.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_db():
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            )
        """)
        # Add some sample products
        products = [
            ('Awesome T-Shirt', 'A high-quality cotton t-shirt.', 25.99),
            ('Stylish Jeans', 'Comfortable and fashionable denim jeans.', 59.99),
            ('Running Shoes', 'Lightweight shoes for your daily runs.', 89.99),
            ('Coffee Maker', 'Brew your perfect cup of coffee at home.', 49.99),
            ('Python Programming Book', 'Learn Python from beginner to advanced.', 39.99),
            ('Wireless Headphones', 'Enjoy music without the wires.', 129.99),
            ('Ergonomic Mouse', 'Reduce strain with this comfortable mouse.', 35.99),
            ('Gaming Keyboard', 'Mechanical keyboard for the ultimate gaming experience.', 99.99),
            ('Summer Dress', 'Light and breezy dress for the summer.', 45.99),
            ('Winter Coat', 'Warm and durable coat for cold weather.', 149.99),
        ]
        cursor.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", products)
        db.commit()
    print("Database initialized.")

# Initialize the database if it doesn't exist
init_db()

# --- Flask Application ---
app = Flask(__name__)

def search_products(search_term: Optional[str] = None, price_min: Optional[float] = None, price_max: Optional[float] = None) -> list:
    """
    Searches for products based on the provided criteria.
    Returns a list of products ordered by relevance.
    """
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT id, name, description, price FROM products WHERE 1=1"
    params = []

    if search_term:
        search_term = f"%{search_term}%"  # Use wildcards for partial matches
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([search_term, search_term])

    if price_min is not None:
        query += " AND price >= ?"
        params.append(price_min)

    if price_max is not None:
        query += " AND price <= ?"
        params.append(price_max)

    # Order by relevance: prioritize matches in name, then description
    if search_term:
        query += " ORDER BY CASE "
        query += "WHEN name LIKE ? THEN 1 "
        query += "WHEN description LIKE ? THEN 2 "
        query += "ELSE 3 END, name" # Secondary sort by name
        params.extend([f"%{request.args.get('q', '')}%", f"%{request.args.get('q', '')}%"])
    else:
        query += " ORDER BY name" # Default ordering

    cursor.execute(query, params)
    products = cursor.fetchall()
    conn.close()
    return [dict(row) for row in products]

@app.route('/search', methods=['GET'])
def search_endpoint():
    search_term = request.args.get('q')
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)

    results = search_products(search_term, price_min, price_max)
    return jsonify(results)

if __name__ == '__main__':
    print("Server running on http://127.0.0.1:5000/search")
    print("Try searching by going to URLs like:")
    print("http://127.0.0.1:5000/search?q=shirt")
    print("http://127.0.0.1:5000/search?q=python&price_min=30&price_max=40")
    app.run(debug=True)

# --- Testing the Functionality (outside the Flask app for direct testing) ---
def test_search_function():
    # Test case 1: Search by name
    results = search_products(search_term="T-Shirt")
    print("\nSearch results for 'T-Shirt':")
    for product in results:
        print(product)

    # Test case 2: Search by description
    results = search_products(search_term="coffee")
    print("\nSearch results for 'coffee':")
    for product in results:
        print(product)

    # Test case 3: Search by price range
    results = search_products(price_min=50.0, price_max=100.0)
    print("\nSearch results for price between 50 and 100:")
    for product in results:
        print(product)

    # Test case 4: Search by name and price range
    results = search_products(search_term="shoes", price_min=80.0, price_max=90.0)
    print("\nSearch results for 'shoes' with price between 80 and 90:")
    for product in results:
        print(product)

    # Test case 5: Empty search
    results = search_products()
    print("\nAll products:")
    for product in results:
        print(product)

if __name__ == '__main__':
    test_search_function()