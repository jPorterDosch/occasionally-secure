from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def create_table():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_number TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            cvv TEXT NOT NULL,
            cardholder_name TEXT NOT NULL
        )
    ''')
    db.commit()
    db.close()

@app.route('/add_card', methods=['POST'])
def add_card():
    try:
        user_id = request.json['user_id']
        card_number = request.json['card_number']
        expiry_date = request.json['expiry_date']
        cvv = request.json['cvv']
        cardholder_name = request.json['cardholder_name']
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO payment_cards (user_id, card_number, expiry_date, cvv, cardholder_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, card_number, expiry_date, cvv, cardholder_name))
        db.commit()
        db.close()
        return jsonify({'status': 'success'}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

if __name__ == '__main__':
    create_table()
    app.run(debug=True)
