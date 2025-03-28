import sqlite3
from datetime import datetime

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS payment_cards")
    
    # Create users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    ''')

    # Create payment_cards table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            card_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_number TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            cvv TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    conn.commit()
    conn.close()

# Call this function to ensure tables exist when the script runs
create_tables()

# --- User Authentication Simulation ---
# In a real application, you would have a proper authentication system.
# Here, we'll just simulate a logged-in user.
LOGGED_IN_USER_ID = 1  # Assuming user with ID 1 is logged in

def get_logged_in_user():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (LOGGED_IN_USER_ID,))
    user = cursor.fetchone()
    conn.close()
    return user

# For demonstration purposes, let's create a dummy user if they don't exist
if not get_logged_in_user():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username) VALUES (?)", ('testuser',))
    conn.commit()
    conn.close()

# --- Function to Add Payment Card ---
def add_payment_card(user_id, card_number, expiry_date, cvv):
    try:
        # Basic validation (you'd likely have more robust validation)
        if not card_number.isdigit() or len(card_number) < 10:
            return "Invalid card number."
        try:
            datetime.strptime(expiry_date, '%Y-%m')
        except ValueError:
            return "Invalid expiry date format (YYYY-MM)."
        if not cvv.isdigit() or len(cvv) < 3:
            return "Invalid CVV."

        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO payment_cards (user_id, card_number, expiry_date, cvv)
            VALUES (?, ?, ?, ?)
        ''', (user_id, card_number, expiry_date, cvv))
        conn.commit()
        conn.close()
        return "Payment card added successfully."
    except sqlite3.Error as e:
        return f"Error adding payment card: {e}"

# --- Function to Get User's Payment Cards (for testing) ---
def get_user_payment_cards(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payment_cards WHERE user_id = ?", (user_id,))
    cards = cursor.fetchall()
    conn.close()
    return cards

# --- Testing the Functionality ---
if __name__ == "__main__":
    logged_in_user = get_logged_in_user()
    if logged_in_user:
        print(f"Logged in user: {logged_in_user[1]}")

        # Simulate user input for a new card
        card_number = input("Enter card number: ")
        expiry_date = input("Enter expiry date (YYYY-MM): ")
        cvv = input("Enter CVV: ")

        result = add_payment_card(LOGGED_IN_USER_ID, card_number, expiry_date, cvv)
        print(result)

        # Verify if the card was added
        user_cards = get_user_payment_cards(LOGGED_IN_USER_ID)
        print("\nUser's payment cards:")
        if user_cards:
            for card in user_cards:
                print(f"  Card ID: {card[0]}, Number: ****-****-****-{card[2][-4:]}, Expiry: {card[3]}")
        else:
            print("  No payment cards found for this user.")
    else:
        print("No logged-in user found.")