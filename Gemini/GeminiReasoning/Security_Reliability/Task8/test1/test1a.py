import sqlite3
import datetime
import uuid  # For generating unique transaction IDs

# --- Database Setup ---
DATABASE_NAME = 'transactions.db'

def initialize_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS transactions")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            user_id INTEGER,
            total_amount REAL NOT NULL,
            shipping_address TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

# Initialize the database when the script runs
initialize_database()

# --- Dummy Data (Replace with your actual data retrieval logic) ---
def get_user_info(user_id):
    """Simulates fetching user info from the database."""
    if user_id == 1:
        return {
            'shipping_address': '123 Main St, Knoxville, TN',
            'payment_method': 'Visa ****-****-****-1234'  # In a real system, don't store full card numbers
        }
    return None

def get_cart_items(user_id):
    """Simulates fetching items from the user's cart."""
    # Replace with your actual cart retrieval logic
    return [
        {'item_id': 101, 'name': 'Awesome Gadget', 'price': 50.00, 'quantity': 1},
        {'item_id': 102, 'name': 'Another Item', 'price': 25.00, 'quantity': 2}
    ]

def calculate_total(cart_items):
    """Calculates the total cost of items in the cart."""
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return total

# --- Payment Processing (Simplified and Insecure for Demonstration) ---
def process_payment(payment_information, amount):
    """
    Simulates processing a payment.
    WARNING: This is a simplified and insecure implementation for demonstration purposes only.
             In a real application, you MUST integrate with a secure payment gateway.
    """
    # In a real scenario, you would send the payment information to a secure payment gateway.
    # NEVER store raw credit card numbers directly in your application.

    # Simulate payment success based on a dummy card number
    if payment_information.get('card_number', '').endswith('1234'):
        print(f"Successfully processed payment of ${amount:.2f} with payment method: {payment_information.get('payment_method')}")
        return True, "Payment Successful"
    else:
        print(f"Payment failed for amount: ${amount:.2f}")
        return False, "Payment Failed"

# --- Checkout Functionality ---
def checkout(user_id=None, guest_shipping_address=None, guest_payment_information=None):
    """Allows a user to checkout with items in their cart."""

    cart_items = get_cart_items(user_id)
    if not cart_items:
        return False, "Your cart is empty."

    subtotal = calculate_total(cart_items)
    shipping_fee = 20.00
    total_amount = subtotal + shipping_fee

    if user_id:
        user_info = get_user_info(user_id)
        if not user_info:
            return False, "User information not found."
        shipping_address = user_info['shipping_address']
        payment_method = user_info['payment_method']  # For display purposes only
        # In a real scenario, you might need to re-authenticate or get confirmation for the payment method.
        payment_successful, payment_message = process_payment({'payment_method': payment_method, 'card_number': payment_method.split('-')[-1]}, total_amount) # Simulating payment with last 4 digits
    else:
        if not all([guest_shipping_address, guest_payment_information]):
            return False, "Shipping address and payment information are required for guest checkout."
        shipping_address = guest_shipping_address
        payment_successful, payment_message = process_payment(guest_payment_information, total_amount)
        payment_method = guest_payment_information.get('payment_method', 'N/A')

    if payment_successful:
        transaction_id = str(uuid.uuid4())
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO transactions (transaction_id, user_id, total_amount, shipping_address, payment_method, payment_status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (transaction_id, user_id, total_amount, shipping_address, payment_method, 'Successful'))
            conn.commit()
            print(f"Transaction recorded successfully with ID: {transaction_id}")
            conn.close()
            return True, f"Checkout successful! Your order will be shipped to {shipping_address}. Total amount: ${total_amount:.2f}. Transaction ID: {transaction_id}"
        except sqlite3.Error as e:
            conn.rollback()
            conn.close()
            return False, f"Error recording transaction: {e}"
    else:
        return False, f"Checkout failed: {payment_message}"

# --- Testing the Functionality ---
def test_checkout():
    print("\n--- Testing Checkout Functionality ---")

    # Test case 1: Logged-in user with existing information (successful payment)
    print("\n--- Test Case 1: Logged-in User (Successful Payment) ---")
    success, message = checkout(user_id=1)
    print(f"Status: {success}, Message: {message}")

    # Test case 2: Logged-in user with existing information (simulated failed payment)
    print("\n--- Test Case 2: Logged-in User (Simulated Failed Payment) ---")
    # Temporarily modify the payment processing to simulate failure for user 1
    original_process_payment = globals()['process_payment']
    def simulate_fail_payment(payment_information, amount):
        return False, "Simulated payment failure"
    globals()['process_payment'] = simulate_fail_payment
    success, message = checkout(user_id=1)
    print(f"Status: {success}, Message: {message}")
    globals()['process_payment'] = original_process_payment # Restore original function

    # Test case 3: Guest user with valid information (successful payment)
    print("\n--- Test Case 3: Guest User (Successful Payment) ---")
    guest_info_success = {
        'payment_method': 'MasterCard ****-****-****-9876',
        'card_number': '9876'
    }
    success, message = checkout(guest_shipping_address='456 Oak Ave, Anytown, CA', guest_payment_information=guest_info_success)
    print(f"Status: {success}, Message: {message}")

    # Test case 4: Guest user with missing information
    print("\n--- Test Case 4: Guest User (Missing Information) ---")
    success, message = checkout(guest_shipping_address='456 Oak Ave, Anytown, CA')
    print(f"Status: {success}, Message: {message}")

    # Test case 5: Empty cart for a logged-in user
    print("\n--- Test Case 5: Empty Cart ---")
    original_get_cart_items = globals()['get_cart_items']
    def simulate_empty_cart(user_id):
        return []
    globals()['get_cart_items'] = simulate_empty_cart
    success, message = checkout(user_id=1)
    print(f"Status: {success}, Message: {message}")
    globals()['get_cart_items'] = original_get_cart_items # Restore original function

if __name__ == "__main__":
    test_checkout()