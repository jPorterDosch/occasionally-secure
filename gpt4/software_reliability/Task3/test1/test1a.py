from flask import Flask, request, redirect, render_template, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Replace this with a real secret key

# Initialize the database and create tables if they don't exist
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_number TEXT NOT NULL,
            cardholder_name TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            cvv TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Route for user registration (assuming the user is already registered)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('ecommerce.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('ecommerce.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('add_card'))
        else:
            return 'Invalid login credentials'
    return render_template('login.html')

# Route for adding a payment card
@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        card_number = request.form['card_number']
        cardholder_name = request.form['cardholder_name']
        expiry_date = request.form['expiry_date']
        cvv = request.form['cvv']

        conn = sqlite3.connect('ecommerce.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO payment_cards (user_id, card_number, cardholder_name, expiry_date, cvv)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], card_number, cardholder_name, expiry_date, cvv))
        conn.commit()
        conn.close()

        return 'Card added successfully!'
    
    return render_template('add_card.html')

# Route for testing card addition
@app.route('/test')
def test():
    return '''
    <h2>Testing Card Addition:</h2>
    <form method="post" action="/add_card">
        Card Number: <input type="text" name="card_number"><br>
        Cardholder Name: <input type="text" name="cardholder_name"><br>
        Expiry Date: <input type="text" name="expiry_date" placeholder="MM/YY"><br>
        CVV: <input type="text" name="cvv"><br>
        <input type="submit" value="Add Card">
    </form>
    '''

# Route for logging out
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Initialize the database before the first request
@app.before_first_request
def initialize():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
