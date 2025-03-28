import sqlite3

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def create_payment_methods_table():
    """Creates the user_payment_methods table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS user_payment_methods")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_payment_methods (
            payment_method_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_number TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            cvv TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Create the table when the script is run
create_payment_methods_table()

# --- Function to Add Payment Card ---
def add_payment_card(user_id):
    """Allows a logged-in user to add a new payment card."""
    print("\n--- Add New Payment Card ---")
    card_number = input("Enter card number: ")
    expiry_date = input("Enter expiry date (MM/YY): ")
    cvv = input("Enter CVV: ")

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO user_payment_methods (user_id, card_number, expiry_date, cvv)
            VALUES (?, ?, ?, ?)
        """, (user_id, card_number, expiry_date, cvv))
        conn.commit()
        print("Payment card added successfully!")
    except sqlite3.Error as e:
        print(f"Error adding payment card: {e}")
        conn.rollback()
    finally:
        conn.close()

# --- Function to Test Adding a Card ---
def test_add_payment_card():
    """Simulates a logged-in user and adds a new payment card for testing."""
    print("\n--- Testing Adding Payment Card ---")
    # Assume a logged-in user with ID 1 (you might fetch this from your session)
    logged_in_user_id = 1

    # Simulate the user providing card details
    print(f"Adding a card for user ID: {logged_in_user_id}")
    add_payment_card(logged_in_user_id)

    # Verify if the card was added
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT payment_method_id, card_number, expiry_date
        FROM user_payment_methods
        WHERE user_id = ?
    """, (logged_in_user_id,))
    payment_methods = cursor.fetchall()
    conn.close()

    if payment_methods:
        print(f"\nPayment methods found for user ID {logged_in_user_id}:")
        for method in payment_methods:
            print(f"  ID: {method[0]}, Card Number: ****-****-****-{method[1][-4:]}, Expiry: {method[2]}")
    else:
        print(f"No payment methods found for user ID {logged_in_user_id}.")

# --- Example Usage ---
if __name__ == "__main__":
    # Simulate a user session by setting a current user ID
    # In a real application, this would come from your authentication system
    current_user_id = 1

    # You would typically integrate this into your web application's routes/views
    # For example, when a user submits a form to add a payment method.
    add_payment_card(current_user_id)

    # --- How to Test ---
    # After running the script once to add a card, you can run the test function
    # to see if it was saved in the database.
    test_add_payment_card()

    # You can also add another card for the same user or a different simulated user
    # by changing the 'current_user_id' and running the add_payment_card function again.
    # For example:
    # current_user_id = 2
    # add_payment_card(current_user_id)
    # test_add_payment_card() # This will only show results for user ID 1 as it's hardcoded in the test function.

    # To test for different users, you'd modify the test_add_payment_card function
    # or create a new test function.