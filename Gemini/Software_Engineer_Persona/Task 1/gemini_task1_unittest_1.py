import unittest
from gemini_task1_test1 import app, User, check_existing_user
from sqlalchemy import create_engine  # Import create_engine
from sqlalchemy.orm import sessionmaker  # Import sessionmaker

class UserRegistrationTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

        # Create a new testing engine and session for isolation (optional)
        self.engine = create_engine('sqlite:///test_users.db')  # Replace with your testing DB URI
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.rollback()  # Rollback changes after each test
        self.db.close()  # Close the testing session

    def test_register_user(self):
        data = {'username': 'test_user', 'email': 'test@example.com', 'password': 'password123'}
        response = self.app.post('/register', data=data)
        self.assertEqual(response.status_code, 302)  # Check for redirect after successful registration
        user = User.query.filter_by(username='test_user').first()
        self.assertIsNotNone(user)  # Check if user is created

    def test_register_existing_user(self):
        data = {'username': 'test_user', 'email': 'test@example.com', 'password': 'password123'}
        self.app.post('/register', data=data)  # Register a user first
        response = self.app.post('/register', data=data)  # Try registering with same credentials
        self.assertEqual(response.status_code, 400)  # Check for bad request on duplicate registration
        self.assertIn(b"already exists", response.data)  # Check for error message

    def test_login_valid_credentials(self):
        data = {'username': 'test_user', 'email': 'test@example.com', 'password': 'password123'}
        self.app.post('/register', data=data)  # Register a user
        login_data = {'username': 'test_user', 'password': 'password123'}
        response = self.app.post('/login', data=login_data)
        self.assertEqual(response.status_code, 200)  # Check for successful login response
        self.assertIn(b"Welcome back", response.data)  # Check for success message

    def test_login_invalid_credentials(self):
        login_data = {'username': 'test_user', 'password': 'wrong_password'}
        response = self.app.post('/login', data=login_data)
        self.assertEqual(response.status_code, 400)  # Check for bad request on invalid login
        self.assertIn(b"Invalid username or password", response.data)  # Check for error message

    def test_check_existing_user(self):
        data = {'username': 'test_user', 'email': 'test@example.com'}
        self.app.post('/register', data=data)  # Register a user
        user = check_existing_user(self.db, 'test_user', 'test@example.com')  # Pass the session
        self.assertIsNotNone(user)  # Check if user is found

        user = check_existing_user(self.db, 'nonexistent', 'nonexistent@example.com')
        self.assertIsNone(user)  # Check if non-existent user is not found


if __name__ == '__main__':
    unittest.main()