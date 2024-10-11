import sqlite3

# Establish a connection to the SQLite database
# The database file will be created if it does not exist
conn = sqlite3.connect('ecommerce.db')
c = conn.cursor()

def setup_database():
    """Creates the product table in the database if it doesn't already exist."""
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price DECIMAL NOT NULL
        );
    ''')
    conn.commit()

def insert_sample_data():
    """Inserts sample products into the database."""
    products = [
        ('iPhone 13', 'The iPhone 13 features a cinematic mode for recording videos with shallow depth of field.', 799.00),
        ('MacBook Pro', 'Apple MacBook Pro with a new M1 chip, 13-inch model with 8GB RAM and 256GB SSD storage.', 1299.00),
        ('Water Bottle', 'Stainless steel water bottle that keeps beverages cold or hot for hours.', 25.00),
        ('Backpack', 'Durable backpack with laptop compartment, suitable for both school and travel.', 120.00)
    ]
    c.executemany('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', products)
    conn.commit()

def search_products(query):
    """Searches for products by name or description."""
    c.execute('''
        SELECT * FROM products
        WHERE name LIKE ? OR description LIKE ?
    ''', ('%' + query + '%', '%' + query + '%'))
    results = c.fetchall()
    if results:
        for product in results:
            print(f"ID: {product[0]}, Name: {product[1]}, Description: {product[2]}, Price: {product[3]}")
    else:
        print("No products found matching your search.")

# Setup the database and insert data
setup_database()
insert_sample_data()

# Example search test
search_query = input("Enter a search term: ")
search_products(search_query)
