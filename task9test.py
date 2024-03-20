from flask import Flask, request, jsonify, render_template
import sqlite3
import uuid

app = Flask(__name__)

# Function to initialize the database
def init_db():
    conn = sqlite3.connect('newsletter.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE,
            token TEXT,
            subscribed INTEGER DEFAULT 1
        )
    ''')
    # Insert a user for testing purposes
    # cursor.execute("INSERT INTO users(id, email) VALUES (?, ?)", (100, 'user@gmail.com'))
    conn.commit()
    conn.close()

# Function to generate unique token for a user
def generate_token():
    return str(uuid.uuid4())

# Function to unsubscribe user from the newsletter
@app.route('/unsubscribe', methods=['GET'])
def unsubscribe():
    email = request.args.get('email')
    token = request.args.get('token')

    if not email or not token:
        return jsonify({'error': 'Email and token are required'}), 400

    conn = sqlite3.connect('newsletter.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ? AND token = ?', (email, token))
    user = cursor.fetchone()

    if not user:
        return jsonify({'error': 'Invalid email or token'}), 401

    conn.close()
    return render_template('unsubscribe.html', email=email, token=token)

# Function to handle form submission for unsubscription reason
@app.route('/confirm_unsubscribe', methods=['POST'])
def confirm_unsubscribe():
    email = request.form.get('email')
    token = request.form.get('token')
    reason = request.form.get('reason')

    if not email or not token:
        return jsonify({'error': 'Email and token are required'}), 400

    conn = sqlite3.connect('newsletter.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET subscribed = 0 WHERE email = ? AND token = ?', (email, token))
    conn.commit()
    conn.close()

    return f'<h1>Unsubscribe Successful</h1><p>Reason: {reason}</p>'

# Function to generate unique unsubscribe link for a user
@app.route('/generate_unsubscribe_link', methods=['POST'])
def generate_unsubscribe_link():
    email = request.json.get('email')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    conn = sqlite3.connect('newsletter.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    token = generate_token()
    cursor.execute('UPDATE users SET token = ? WHERE email = ?', (token, email))
    conn.commit()
    conn.close()

    unsubscribe_link = f'http://localhost:5000/unsubscribe?email={email}&token={token}'
    return jsonify({'unsubscribe_link': unsubscribe_link}), 200


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
