import sqlite3
from datetime import datetime

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def create_payment_cards_table():
    """Creates the user_payment_cards table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS user_payment_cards")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_payment_cards (
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

# Call this function when your application starts to ensure the table exists
create_payment_cards_table()

# --- Function to Add a New Payment Card ---
def add_payment_card(user_id, card_number, expiry_date, cvv, cardholder_name):
    """Adds a new payment card for a given user to the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO user_payment_cards (user_id, card_number, expiry_date, cvv, cardholder_name)
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

# --- Function to Simulate a Logged-In User (for testing) ---
def get_logged_in_user_id():
    """In a real application, you would get the user ID from the session or authentication context."""
    # For this example, we'll just return a fixed user ID.
    # In your application, this would be something like:
    # return session.get('user_id') or current_user.id
    return 123  # Example user ID

# --- Function to Get User Input for Card Details ---
def get_card_details_from_user():
    """Gets payment card details from the user."""
    card_number = input("Enter card number: ")
    expiry_date = input("Enter expiry date (MM/YY): ")
    cvv = input("Enter CVV: ")
    cardholder_name = input("Enter cardholder name: ")
    return card_number, expiry_date, cvv, cardholder_name

# --- Function to Test Adding a Card ---
def test_add_card():
    """Simulates a logged-in user adding a payment card and verifies it."""
    print("\n--- Testing Adding a Payment Card ---")
    user_id = get_logged_in_user_id()
    print(f"Simulating logged-in user with ID: {user_id}")

    card_number, expiry_date, cvv, cardholder_name = get_card_details_from_user()

    if add_payment_card(user_id, card_number, expiry_date, cvv, cardholder_name):
        # Verify if the card was added
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM user_payment_cards WHERE user_id = ? AND card_number = ?
        ''', (user_id, card_number))
        result = cursor.fetchone()
        conn.close()

        if result:
            print("\nVerification successful:")
            print(f"Card details found in the database for user {user_id}.")
            print(f"Card Number (last 4 digits): ****-****-****-{result[2][-4:]}") # Showing only last 4 digits for security
            print(f"Expiry Date: {result[3]}")
            print(f"Cardholder Name: {result[5]}")
        else:
            print("\nVerification failed: Card details not found in the database for this user and card number.")
    else:
        print("Adding card failed, verification not possible.")

# --- How to Run and Test ---
if __name__ == "__main__":
    print("Running the payment card addition module.")
    test_add_card()