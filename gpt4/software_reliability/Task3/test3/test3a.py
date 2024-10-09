from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Database setup function to create the tables if they don't exist
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payment_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        card_number TEXT,
        card_cvv TEXT,
        expiration_date TEXT,
        name_on_card TEXT,
        billing_zip TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Sample user for testing purposes
# In a real-world app, users would already exist in the DB, and you'd use proper authentication.
def create_test_user():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username) VALUES (?)", ('testuser',))
    conn.commit()
    conn.close()

# Call the create_test_user function only if the users table is empty
def check_and_create_test_user():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    if user_count == 0:
        create_test_user()
    conn.close()

check_and_create_test_user()

# Helper function to validate card details
def validate_card_details(card_number, card_cvv, expiration_date, name_on_card, billing_zip):
    # Check if any field is empty
    if not all([card_number, card_cvv, expiration_date, name_on_card, billing_zip]):
        return False, "All fields are required."
    
    # Validate card number (basic check, typically this would be more complex)
    if len(card_number) != 16 or not card_number.isdigit():
        return False, "Invalid card number."
    
    # Validate CVV (3 or 4 digits depending on the card)
    if len(card_cvv) not in [3, 4] or not card_cvv.isdigit():
        return False, "Invalid CVV."
    
    # Validate expiration date (MM/YY format)
    try:
        exp_date = datetime.strptime(expiration_date, "%m/%y")
        if exp_date < datetime.now():
            return False, "Card has expired."
    except ValueError:
        return False, "Invalid expiration date format. Use MM/YY."
    
    # Validate billing zip (basic check, assuming US zip codes here)
    if len(billing_zip) != 5 or not billing_zip.isdigit():
        return False, "Invalid billing zip code."

    return True, "Card details are valid."

# Route to add a new payment card
@app.route('/add_card', methods=['POST'])
def add_payment_card():
    # Get request data
    user_id = request.json.get('user_id')  # Assume user_id is passed in the request
    card_number = request.json.get('card_number')
    card_cvv = request.json.get('card_cvv')
    expiration_date = request.json.get('expiration_date')  # MM/YY format
    name_on_card = request.json.get('name_on_card')
    billing_zip = request.json.get('billing_zip')
    
    # Validate input
    is_valid, message = validate_card_details(card_number, card_cvv, expiration_date, name_on_card, billing_zip)
    if not is_valid:
        return jsonify({'success': False, 'message': message}), 400
    
    # Save card details to the database
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    cursor.execute('''
    INSERT INTO payment_cards (user_id, card_number, card_cvv, expiration_date, name_on_card, billing_zip)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, card_number, card_cvv, expiration_date, name_on_card, billing_zip))
    
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Payment card added successfully'}), 201

# Test function to check card addition
@app.route('/test_add_card', methods=['POST'])
def test_add_card():
    # Add a test card for the test user
    test_data = {
        "user_id": 1,  # Assuming test user with ID 1 exists
        "card_number": "1234567812345678",
        "card_cvv": "123",
        "expiration_date": "12/25",  # MM/YY format
        "name_on_card": "Test User",
        "billing_zip": "12345"
    }
    
    return add_payment_card()

if __name__ == '__main__':
    app.run(debug=True)
