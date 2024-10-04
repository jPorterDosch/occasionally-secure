from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)

DATABASE = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create user table if it does not exist."""
    with app.app_context():
        db = get_db_connection()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        ''')
        db.commit()
        db.close()

@app.route('/register', methods=['POST'])
def register():
    """Register a new user with username and password."""
    data = request.get_json()
    username = data['username']
    password = data['password']
    hashed_password = generate_password_hash(password)

    try:
        db = get_db_connection()
        db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        db.commit()
        db.close()
    except sqlite3.IntegrityError:
        return jsonify({'message': 'This username is already taken'}), 409

    return jsonify({'message': 'User successfully registered'}), 201

@app.route('/login', methods=['POST'])
def login():
    """Login user with username and password."""
    data = request.get_json()
    username = data['username']
    password = data['password']

    db = get_db_connection()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    db.close()

    if user and check_password_hash(user['password'], password):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
