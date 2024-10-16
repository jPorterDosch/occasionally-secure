import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """ Create a database connection to the SQLite database specified by db_file """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def create_table(conn):
    """ Create a table in the database """
    try:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id integer PRIMARY KEY,
                name text NOT NULL,
                description text NOT NULL
            );
        ''')
    except Error as e:
        print(e)

def add_product(conn, product):
    """ Add a new product to the products table """
    sql = ''' INSERT INTO products(name, description)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, product)
    conn.commit()
    return cur.lastrowid

def search_products(conn, query):
    """ Search for products by name or description """
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE name LIKE ? OR description LIKE ?", ('%' + query + '%', '%' + query + '%',))
    rows = cur.fetchall()

    for row in rows:
        print(row)

def main():
    database = "ecommerce.db"

    # Create a database connection
    conn = create_connection(database)

    with conn:
        # Create products table
        create_table(conn)

        # Add products
        # Note: You can comment out these lines after the first run to avoid inserting duplicates
        add_product(conn, ('Red Shirt', 'Comfortable cotton t-shirt'))
        add_product(conn, ('Blue Jeans', 'Stylish denim for all seasons'))
        add_product(conn, ('Running Shoes', 'High performance athletic shoes'))

        # Search for products
        print("Search Results:")
        search_query = input("Enter search query: ")
        search_products(conn, search_query)

if __name__ == '__main__':
    main()