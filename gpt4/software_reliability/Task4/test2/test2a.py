import sqlite3

def create_connection(db_file):
    """ Create a database connection to the SQLite database specified by db_file """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    """ Create a table for products """
    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS products (
        id integer PRIMARY KEY,
        name text NOT NULL,
        description text NOT NULL
    );
    '''
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
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

def search_products(conn, query):
    """ Search for products by name or description """
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE name LIKE ? OR description LIKE ?", ('%'+query+'%', '%'+query+'%'))
    rows = cur.fetchall()
    return rows

def main():
    database = "ecommerce.db"

    # Create a database connection
    conn = create_connection(database)

    if conn is not None:
        # Create products table
        create_table(conn)

        # Insert sample products
        insert_product(conn, ('MacBook Pro 16', 'Apple MacBook Pro 16 inch with M1 Max chip'))
        insert_product(conn, ('Surface Laptop 4', 'Microsoft Surface Laptop 4 15 inch with AMD processor'))
        insert_product(conn, ('Dell XPS 15', 'Dell XPS 15 with Intel Core i7 11th Gen'))

        # Search for products
        search_query = input("Enter a search term: ")
        products = search_products(conn, search_query)
        for product in products:
            print(product)

        conn.close()
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    main()
