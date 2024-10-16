import sqlite3
from sqlite3 import Error

# Function to create a connection to an SQLite database
def create_connection(db_file):
    """ Create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn

# Function to create the products table
def create_table(conn):
    try:
        sql_create_products_table = """ CREATE TABLE IF NOT EXISTS products (
                                            id integer PRIMARY KEY,
                                            name text NOT NULL,
                                            description text NOT NULL
                                        ); """
        cursor = conn.cursor()
        cursor.execute(sql_create_products_table)
    except Error as e:
        print(e)

# Function to insert a new product into the products table
def create_product(conn, product):
    sql = ''' INSERT INTO products(name, description)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, product)
    conn.commit()
    return cur.lastrowid

# Function to search products by name or description
def search_products(conn, query):
    sql = ''' SELECT name, description,
              (LENGTH(name) - LENGTH(REPLACE(LOWER(name), LOWER(?), ''))) / LENGTH(?) AS name_relevance,
              (LENGTH(description) - LENGTH(REPLACE(LOWER(description), LOWER(?), ''))) / LENGTH(?) AS desc_relevance
              FROM products
              ORDER BY (name_relevance + desc_relevance) DESC
           '''
    cur = conn.cursor()
    cur.execute(sql, (query, query, query, query))
    rows = cur.fetchall()
    return rows

# Main function to demonstrate functionality
def main():
    database = "pythonsqlite.db"

    # Create a database connection
    conn = create_connection(database)
    if conn is not None:
        # Create products table
        create_table(conn)

        # Insert products
        product1 = ('iPhone 12', 'New Apple iPhone 12 (64GB) - Blue')
        product2 = ('Samsung Galaxy S21', 'Experience the new Samsung Galaxy S21 Ultra with 128GB storage')
        product3 = ('iPhone Charger', 'Fast charging USB-C cable for iPhone')
        create_product(conn, product1)
        create_product(conn, product2)
        create_product(conn, product3)

        # Search for a product
        search_query = "iphone"
        results = search_products(conn, search_query)
        print("Search results:")
        for result in results:
            print(result)

        conn.close()
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    main()