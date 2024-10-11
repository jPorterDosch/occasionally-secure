from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE = 'ecommerce.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db_connection()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE
            );
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT
            );
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                score INTEGER CHECK(score BETWEEN 1 AND 5),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );
        ''')
        db.commit()

@app.route('/review', methods=['POST'])
def add_review():
    review_details = request.get_json()
    user_id = review_details['user_id']
    product_id = review_details['product_id']
    text = review_details['text']
    score = review_details['score']
    
    if not (user_id and product_id and text and (1 <= score <= 5)):
        return jsonify({'error': 'Invalid input'}), 400
    
    db = get_db_connection()
    db.execute('INSERT INTO reviews (user_id, product_id, text, score) VALUES (?, ?, ?, ?)',
               (user
