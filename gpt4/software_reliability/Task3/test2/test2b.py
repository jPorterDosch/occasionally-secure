from flask import Flask, request, jsonify, render_template_string
import sqlite3

app = Flask(__name__)
DATABASE = 'payment_info.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS cards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        card_number TEXT NOT NULL,
                        card_holder_name TEXT NOT NULL,
                        expiration_date TEXT NOT NULL,
                        cvv TEXT NOT NULL
                    );''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template_string('''
        <form action="/add-card" method="post">
            <input type="number" name="user_id" placeholder="User ID" required><br>
            <input type="text" name="card_number" placeholder="Card Number" required><br>
            <input type="text" name="card_holder_name" placeholder="Card Holder Name" required><br>
            <input type="text" name="expiration_date" placeholder="Expiration Date" required><br>
            <input type="text" name="cvv" placeholder="CVV" required><br>
            <input type="submit" value="Add Card">
        </form>
    ''')

@app.route('/add-card', methods=['POST'])
def add_card():
    conn = get_db_connection()
    sql = ''' INSERT INTO cards (user_id, card_number, card_holder_name, expiration_date, cvv)
              VALUES (?, ?, ?, ?, ?) '''
    data = (
        request.form['user_id'],
        request.form['card_number'],
        request.form['card_holder_name'],
        request.form['expiration_date'],
        request.form['cvv']
    )
    conn.execute(sql, data)
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Card added successfully'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
