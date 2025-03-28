import sqlite3
from datetime import datetime

DATABASE_NAME = 'ecommerce.db'

def create_payment_cards_table():
    """Creates the payment_cards table in the database if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_number TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            cvv TEXT NOT NULL,
            cardholder_name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_payment_card(user_id, card_number, expiry_date, cvv, cardholder_name):
    """Adds a new payment card for a given user to the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO payment_cards (user_id, card_number, expiry_date, cvv, cardholder_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, card_number, expiry_date, cvv, cardholder_name))
        conn.commit()
        print("Payment card added successfully!")
        return True
    except sqlite3.Error as e:
        print(f"Error adding payment card: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_user_payment_cards(user_id):
    """Retrieves all payment cards associated with a given user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, card_number, expiry_date, cardholder_name FROM payment_cards WHERE user_id = ?
    ''', (user_id,))
    cards = cursor.fetchall()
    conn.close()
    return cards

def test_add_payment_card():
    """Tests the functionality of adding a payment card."""
    create_payment_cards_table()  # Ensure the table exists

    # Simulate a logged-in user (replace with your actual user identification mechanism)
    logged_in_user_id = 1

    # Example card details (in a real application, you would get this from a form)
    card_number = "1234567890123456"
    expiry_date = "12/25"
    cvv = "123"
    cardholder_name = "John Doe"

    # Add the payment card
    if add_payment_card(logged_in_user_id, card_number, expiry_date, cvv, cardholder_name):
        # Verify if the card was added by retrieving the user's payment cards
        user_cards = get_user_payment_cards(logged_in_user_id)
        if user_cards:
            print("\nUser's payment cards:")
            for card in user_cards:
                print(f"  ID: {card[0]}, Number: ****-****-****-{card[1][-4:]}, Expiry: {card[2]}, Name: {card[3]}")
            print("\nTest passed: Payment card added and retrieved successfully.")
        else:
            print("\nTest failed: Payment card not found for the user.")
    else:
        print("\nTest failed: Could not add the payment card.")

if __name__ == "__main__":
    test_add_payment_card()