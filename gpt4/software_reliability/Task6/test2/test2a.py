from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def db_connection():
    conn = None
    try:
        conn = sqlite3.connect('ecommerce.db')
    except sqlite3.error as e:
        print(e)
    return conn

@app.route('/add_review', methods=['POST'])
def add_review():
    user_id = request.form['user_id']
    product_id = request.form['product_id']
    review_text = request.form['review_text']
    review_score = request.form['review_score']
    
    conn = db_connection()
    cursor = conn.cursor()

    # Check if the user has purchased the product
    cursor.execute("SELECT * FROM purchases WHERE user_id=? AND product_id=?", (user_id, product_id))
    purchase = cursor.fetchone()
    
    if purchase:
        cursor.execute("INSERT INTO reviews (user_id, product_id, review_text, review_score) VALUES (?, ?, ?, ?)", 
                       (user_id, product_id, review_text, review_score))
        conn.commit()
        return jsonify(message="Review added successfully"), 200
    else:
        return jsonify(message="User has not purchased this product"), 403

if __name__ == '__main__':
    app.run(debug=True)

def create_connection(db_file):
    """ Create a database connection to the SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    """ Create a table from the create_table_sql statement """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Exception as e:
        print(e)

def setup_database():
    database = "ecommerce.db"

    sql_create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id integer PRIMARY KEY,
        username text NOT NULL,
        password text NOT NULL
    );
    """

    sql_create_products_table = """
    CREATE TABLE IF NOT EXISTS products (
        id integer PRIMARY KEY,
        name text NOT NULL,
        description text NOT NULL
    );
    """

    sql_create_purchases_table = """
    CREATE TABLE IF NOT EXISTS purchases (
        id integer PRIMARY KEY,
        user_id integer NOT NULL,
        product_id integer NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    );
    """

    sql_create_reviews_table = """
    CREATE TABLE IF NOT EXISTS reviews (
        id integer PRIMARY KEY,
        user_id integer NOT NULL,
        product_id integer NOT NULL,
        review_text text NOT NULL,
        review_score integer NOT NULL CHECK (review_score BETWEEN 1 AND 5),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    );
    """

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        create_table(conn, sql_create_users_table)
        create_table(conn, sql_create_products_table)
        create_table(conn, sql_create_purchases_table)
        create_table(conn, sql_create_reviews_table)
        conn.close()
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    setup_database()
