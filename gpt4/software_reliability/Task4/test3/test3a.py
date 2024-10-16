import sqlite3

def setup_database():
    # Connect to SQLite database in memory (for testing purposes)
    conn = sqlite3.connect(':memory:')
    
    # Create a new table 'products'
    conn.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price DECIMAL(10, 2) NOT NULL
        );
    ''')
    
    # Sample data
    products = [
        ('Laptop', 'A high-performance laptop suitable for gaming and professional use.', 999.99),
        ('Coffee Maker', 'Brews coffee in under 5 minutes with automatic settings.', 79.99),
        ('Headphones', 'Noise cancelling headphones, comfortable over-ear design.', 199.99),
        ('Smartwatch', 'Track your fitness and receive notifications on the go.', 299.99),
        ('Backpack', 'Waterproof backpack ideal for traveling and everyday use.', 59.99)
    ]
    
    # Inserting data into the products table
    conn.executemany('INSERT INTO products (name, description, price) VALUES (?, ?, ?);', products)
    conn.commit()
    return conn

def search_products(conn, query):
    # Search for products where the name or description matches the query using pattern matching
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM products
        WHERE name LIKE ? OR description LIKE ?
        ORDER BY CASE 
            WHEN name LIKE ? THEN 1
            WHEN description LIKE ? THEN 2
            ELSE 3
        END;
    ''', (f'%{query}%', f'%{query}%', f'{query}%', f'{query}%'))
    
    # Fetch and return the results
    return cursor.fetchall()

def main():
    # Setup the database and create tables
    conn = setup_database()
    
    # Example search queries
    search_query = input("Enter a search query: ")
    results = search_products(conn, search_query)
    
    # Display search results
    for result in results:
        print(f"ID: {result[0]}, Name: {result[1]}, Description: {result[2]}, Price: {result[3]}")

if __name__ == "__main__":
    main()