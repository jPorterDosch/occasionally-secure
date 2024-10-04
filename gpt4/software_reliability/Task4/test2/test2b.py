def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    return conn

def create_table(conn):
    """ create a products table with Full-Text Search enabled """
    try:
        c = conn.cursor()
        c.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS products
            USING fts5(name, description);
        ''')
        print("Table created")
    except Error as e:
        print(e)
def insert_product(conn, product):
    """
    Insert a new product into the products table
    """
    sql = ''' INSERT INTO products(name, description)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, product)
    conn.commit()
    return cur.lastrowid

def populate_table(conn):
    # List of sample products
    products = [
        ('Nike Sneakers', 'Comfortable running shoes'),
        ('Leather Wallet', 'Compact leather wallet'),
        ('Coffee Mug', 'Ceramic mug with 350 ml capacity'),
        ('T-shirt', 'Cotton graphic t-shirt in various sizes'),
    ]
    
    for product in products:
        insert_product(conn, product)
    print("Sample data inserted")
def search_products(conn, query):
    """
    Search for products by name or description
    """
    cur = conn.cursor()
    cur.execute("SELECT name, description FROM products WHERE products MATCH ?", (query,))
    rows = cur.fetchall()
    for row in rows:
        print(row)
def main():
    database = ":memory:"  # In-memory database; change to 'ecommerce.db' to use a file-based database

    # Create a database connection
    conn = create_connection(database)
    if conn is not connected:
        return

    # Create tables
    create_table(conn)

    # Populate the table with sample data
    populate_table(conn)

    # Search for products
    print("Search Results:")
    search_products(conn, 'shoes')

if __name__ == '__main__':
    main()
