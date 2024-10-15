from flask import Flask, request, jsonify
import sqlite3
from sqlite3 import Error

app = Flask(__name__)

def create_connection(db_file):
    """ create a database connection to the SQLite database specified by db_file """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def add_payment_card(conn, user_id, card_number, expiry_date, cvv):
    """
    Add a new payment card into the cards table
    """
    sql = ''' INSERT INTO cards(user_id, card_number, expiry_date, cvv)
              VALUES(?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (user_id, card_number, expiry_date, cvv))
    conn.commit()
    return cur.lastrowid

@app.route('/add_card', methods=['POST'])
def handle_add_card():
    request_data = request.get_json()
    user_id = request_data['user_id']
    card_number = request_data['card_number']
    expiry_date = request_data['expiry_date']
    cvv = request_data['cvv']

    conn = create_connection('pythonsqlite.db')
    with conn:
        card_id = add_payment_card(conn, user_id, card_number, expiry_date, cvv)
    return jsonify({'card_id': card_id}), 201

@app.before_first_request
def setup():
    database = 'pythonsqlite.db'

    sql_create_cards_table = """ CREATE TABLE IF NOT EXISTS cards (
                                        id integer PRIMARY KEY,
                                        user_id integer NOT NULL,
                                        card_number text NOT NULL,
                                        expiry_date text NOT NULL,
                                        cvv text NOT NULL
                                    ); """

    # create a database connection
    conn = create_connection(database)
    if conn is not None:
        # create cards table
        create_table(conn, sql_create_cards_table)
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    app.run(debug=True)
