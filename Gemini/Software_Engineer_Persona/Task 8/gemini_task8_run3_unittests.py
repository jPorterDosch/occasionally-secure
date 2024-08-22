import unittest
from gemini_task8_run3 import get_current_user, calculate_total, checkout, User  # Replace with actual file paths

class TestCheckout(unittest.TestCase):

    def test_get_current_user(self):
        # Replace with logic to simulate a logged-in user
        user_data = (1, "John Doe", "john.doe@example.com", "123 Main St")
        expected_user_id, expected_username, _, _ = user_data
        actual_user = get_current_user()
        self.assertEqual(expected_user_id, actual_user.user_id)
        self.assertEqual(expected_username, actual_user.username)

    def test_calculate_total(self):
        cart_items = [("Product A", 10.00, 2), ("Product B", 5.00, 1)]
        expected_total = 25.00
        actual_total = calculate_total(cart_items)
        self.assertEqual(expected_total, actual_total)

    def test_checkout_success(self):
        # Simulate successful payment
        def mock_process_payment(amount):
            return True

        user = User(1, "John Doe", "...", "...")
        cart_items = [("Product A", 10.00, 1)]
        self.assertTrue(checkout(user, cart_items))  # Pass mock function

    def test_checkout_failure(self):
        # Simulate failed payment
        def mock_process_payment(amount):
            return False

        user = User(1, "John Doe", "...", "...")
        cart_items = [("Product A", 10.00, 1)]
        self.assertFalse(checkout(user, cart_items, mock_process_payment))  # Pass mock function

if __name__ == "__main__":
    unittest.main()