import sqlite3

def create_connection():
    """ Create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(':memory:')  # Use an in-memory database for demonstration
        print("Connection established.")
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    """ Create product table """
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL
            );
        ''')
        print("Table created.")
    except sqlite3.Error as e:
        print(e)

def insert_product(conn, product):
    """ Insert a new product into the products table """
    sql = ''' INSERT INTO products(name, description)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, product)
    conn.commit()
    return cur.lastrowid

def search_products(conn, search_query):
    """ Search products by name or description """
    cur = conn.cursor()
    query = f"%{search_query}%"
    cur.execute('''
        SELECT *, 
               ((LENGTH(name) - LENGTH(REPLACE(LOWER(name), LOWER(?), ''))) / LENGTH(?)) +
               ((LENGTH(description) - LENGTH(REPLACE(LOWER(description), LOWER(?), ''))) / LENGTH(?)) AS relevance
        FROM products
        WHERE name LIKE ? OR description LIKE ?
        ORDER BY relevance DESC
    ''', (search_query, search_query, search_query, search_query, query, query))
    rows = cur.fetchall()
    return rows

def main():
    # Establish connection and create table
    conn = create_connection()
    create_table(conn)
    
    # Sample products
    products = [
        ('Nike Air Max', 'Comfortable sports shoes'),
        ('Adidas Slippers', 'Casual wear slippers'),
        ('Puma Running Shoes', 'Shoes best for running and jogging'),
        ('Nike Air Jordan', 'High-quality basketball shoes'),
        ('Max Cushioning Elite', 'Enhanced cushion for maximum comfort'),
    ]
    
    # Insert products into the database
    for product in products:
        insert_product(conn, product)
    
    # Search test
    search_query = input("Enter a search term: ")
    results = search_products(conn, search_query)
    print("Search Results:")
    for row in results:
        print(row)

if __name__ == '__main__':
    main()
