import sqlite3
from datetime import datetime

# Create a connection to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db')
    return conn

# Create table for storing payment card details if not exists
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            cardholder_name TEXT NOT NULL,
            card_number TEXT NOT NULL,
            expiration_date TEXT NOT NULL,
            cvv TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Function to add a new payment card for a logged-in user
def add_payment_card(user_id, cardholder_name, card_number, expiration_date, cvv):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO payment_cards (user_id, cardholder_name, card_number, expiration_date, cvv)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, cardholder_name, card_number, expiration_date, cvv))
    
    conn.commit()
    conn.close()
    print(f"Payment card added for user {user_id}")

# Function to list all cards for a specific user for testing purposes
def list_user_cards(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM payment_cards WHERE user_id = ?', (user_id,))
    cards = cursor.fetchall()
    
    conn.close()
    return cards

# Function to test adding a card
def test_add_card():
    user_id = 1  # Assume user 1 is logged in
    cardholder_name = "John Doe"
    card_number = "4111111111111111"  # Dummy Visa card number
    expiration_date = "12/26"
    cvv = "123"

    print("Adding card...")
    add_payment_card(user_id, cardholder_name, card_number, expiration_date, cvv)
    
    print("Fetching user cards to verify...")
    cards = list_user_cards(user_id)
    for card in cards:
        print(card)

if __name__ == '__main__':
    # Create the table if not already present
    create_table()

    # Test adding a card
    test_add_card()
