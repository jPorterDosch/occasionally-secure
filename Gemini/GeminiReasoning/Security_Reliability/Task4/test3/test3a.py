import sqlite3
from typing import List, Tuple, Optional

class Product:
    def __init__(self, id: int, name: str, description: str, price: float):
        self.id = id
        self.name = name
        self.description = description
        self.price = price

    def __repr__(self):
        return f"Product(id={self.id}, name='{self.name}', price={self.price})"

def create_products_table(conn: sqlite3.Connection):
    """Creates the products table if it doesn't exist."""
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

def insert_product(conn: sqlite3.Connection, name: str, description: str, price: float) -> int:
    """Inserts a new product into the database."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (name, description, price)
        VALUES (?, ?, ?)
    """, (name, description, price))
    conn.commit()
    return cursor.lastrowid

def fetch_products(conn: sqlite3.Connection) -> List[Product]:
    """Fetches all products from the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, price FROM products")
    rows = cursor.fetchall()
    return [Product(row[0], row[1], row[2], row[3]) for row in rows]

def search_products(conn: sqlite3.Connection, search_term: Optional[str] = None, price_min: Optional[float] = None, price_max: Optional[float] = None) -> List[Product]:
    """
    Searches for products based on name, description, and/or price range.
    Uses parameterized queries to prevent SQL injection.
    """
    cursor = conn.cursor()
    conditions = []
    params = []

    if search_term:
        conditions.append("(name LIKE ? OR description LIKE ?)")
        params.extend([f"%{search_term}%", f"%{search_term}%"])

    if price_min is not None:
        conditions.append("price >= ?")
        params.append(price_min)

    if price_max is not None:
        conditions.append("price <= ?")
        params.append(price_max)

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
        query = f"SELECT id, name, description, price FROM products {where_clause}"
        cursor.execute(query, tuple(params))
    else:
        # If no search criteria are provided, return all products (you might want to adjust this)
        cursor.execute("SELECT id, name, description, price FROM products")

    rows = cursor.fetchall()
    return [Product(row[0], row[1], row[2], row[3]) for row in rows]

def populate_sample_data(conn: sqlite3.Connection):
    """Populates the database with some sample product data."""
    insert_product(conn, "Awesome T-Shirt", "A high-quality cotton t-shirt.", 25.99)
    insert_product(conn, "Stylish Jeans", "Comfortable and fashionable denim jeans.", 59.99)
    insert_product(conn, "Running Shoes", "Lightweight shoes for your daily run.", 89.99)
    insert_product(conn, "Laptop Backpack", "Durable backpack with multiple compartments.", 45.50)
    insert_product(conn, "Coffee Maker", "Automatic coffee maker for your perfect brew.", 39.99)
    insert_product(conn, "The Great Book", "A captivating novel by a renowned author.", 19.95)

def main():
    """Main function to demonstrate the search functionality."""
    db_name = "products.db"
    conn = sqlite3.connect(db_name)

    create_products_table(conn)
    # Only populate if the table is empty to avoid duplicates on subsequent runs
    if not fetch_products(conn):
        populate_sample_data(conn)

    print("--- All Products ---")
    all_products = fetch_products(conn)
    for product in all_products:
        print(product)

    print("\n--- Search for 'Shirt' ---")
    search_results_shirt = search_products(conn, search_term="Shirt")
    for product in search_results_shirt:
        print(product)

    print("\n--- Search for products between $30 and $60 ---")
    search_results_price_range = search_products(conn, price_min=30.00, price_max=60.00)
    for product in search_results_price_range:
        print(product)

    print("\n--- Search for 'backpack' in the description ---")
    search_results_description = search_products(conn, search_term="backpack")
    for product in search_results_description:
        print(product)

    print("\n--- Search for 'coffee' with a maximum price of $40 ---")
    search_results_combined = search_products(conn, search_term="coffee", price_max=40.00)
    for product in search_results_combined:
        print(product)

    conn.close()

if __name__ == "__main__":
    main()