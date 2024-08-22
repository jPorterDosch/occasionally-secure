import sqlite3
import datetime


def add_payment_card(user_id, card_number, card_holder_name, expiry_date, cvv, billing_zip):
  """
  Adds a new payment card to the database for a logged-in user.

  Args:
      user_id (int): The ID of the logged-in user.
      card_number (str): The card number.
      card_holder_name (str): The name on the card.
      expiry_date (str): The expiration date in MM/YYYY format.
      cvv (str): The card verification code (CVV/CVV2).
      billing_zip (str): The billing zip code.

  Returns:
      None
  """

  conn = sqlite3.connect('ecommerce.db')
  c = conn.cursor()

  # Check if all required fields are provided
  if not all([card_number, card_holder_name, expiry_date, cvv, billing_zip]):
    print("Error: Please provide all required information for your payment card.")
    return

  try:
    # Parse the expiry date string (assuming format MM/YYYY)
    expiration_date = datetime.datetime.strptime(expiry_date, "%m/%Y").date()

    # Check if expiration date is in the future
    today = datetime.date.today()
    if expiration_date < today:
      print("Error: The provided expiration date is invalid (already expired).")
      return

  except ValueError:
    print("Error: Please enter the expiration date in MM/YYYY format (e.g., 12/2025).")
    return

  # Simulate secure payment processing (replace with real integration)
  print("Simulating secure payment processing...")

  # Insert card details into the table (assuming CVV is not stored)
  try:
    c.execute("INSERT INTO payment_cards (user_id, card_number, card_holder_name, expiry_date) VALUES (?, ?, ?, ?)",
              (user_id, card_number, card_holder_name, expiry_date))
    conn.commit()
    print("Card added successfully!")
  except sqlite3.Error as e:
    print("Error adding card:", e)
  finally:
    conn.close()


# Database setup (automatic table creation)
conn = sqlite3.connect('ecommerce.db')
c = conn.cursor()
try:
  c.execute("DROP TABLE IF EXISTS payment_cards")
  c.execute('''CREATE TABLE IF NOT EXISTS payment_cards (
              user_id INTEGER,
              card_number TEXT,
              card_holder_name TEXT,
              expiry_date TEXT,
              cvv TEXT,
              FOREIGN KEY (user_id) REFERENCES users(id)
          )''')
  conn.commit()
except sqlite3.Error as e:
  print("Error creating table:", e)
finally:
  conn.close()

# Example usage (assuming you have user data from the session)
user_id = 1  # Replace with actual user ID from the session
card_number = "1234567890123456"  # Replace with user-entered data
card_holder_name = "John Doe"  # Replace with user-entered data
expiry_date = "12/2025"  # Replace with user-entered data
cvv = "123"  # Replace with user-entered data (**NEVER store CVV**)
billing_zip = "12345"  # Replace with user-entered data

add_payment_card(user_id, card_number, card_holder_name, expiry_date, cvv, billing_zip)