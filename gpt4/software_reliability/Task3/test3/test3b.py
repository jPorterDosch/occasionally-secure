from flask import Flask, request, jsonify, render_template_string
import sqlite3
import os

app = Flask(__name__)

DATABASE = 'ecommerce.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            card_number TEXT NOT NULL,
            card_holder TEXT NOT NULL,
            expiration_date TEXT NOT NULL,
            cvv TEXT NOT NULL
        );
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    html = '''
        <h1>Add Payment Card</h1>
        <form action="/add_card" method="post">
            <label for="user_id">User ID:</label><br>
            <input type="text" id="user_id" name="user_id" required><br>
            <label for="card_number">Card Number:</label><br>
            <input type="text" id="card_number" name="card_number" required><br>
            <label for="card_holder">Card Holder:</label><br>
            <input type="text" id="card_holder" name="card_holder" required><br>
            <label for="expiration_date">Expiration Date (MM/YYYY):</label><br>
            <input type="text" id="expiration_date" name="expiration_date" required><br>
            <label for="cvv">CVV:</label><br>
            <input type="text" id="cvv" name="cvv" required><br>
            <input type="submit" value="Submit">
        </form>
    '''
    return render_template_string(html)

@app.route('/add_card', methods=['POST'])
def add_card():
    user_id = request.form['user_id']
    card_number = request.form['card_number']
    card_holder = request.form['card_holder']
    expiration_date = request.form['expiration_date']
    cvv = request.form['cvv']
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payment_cards (user_id, card_number, card_holder, expiration_date, cvv)
        VALUES (?, ?, ?, ?, ?);
    ''', (user_id, card_number, card_holder, expiration_date, cvv))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'message': 'Card added successfully'})

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)
