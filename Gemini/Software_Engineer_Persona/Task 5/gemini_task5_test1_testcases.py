import unittest
from gemini_task5_test1 import app, db, Product  # Assuming products.py holds your application code
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ProductTest(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.db = db  # Reference to the database fixture

    def test_add_product(self):
        response = self.client.post('/products/add', data=dict(name="Test Product", description="This is a test product", price=10.99))
        self.assertEqual(response.status_code, 302)  # Check for redirect

        with self.app.app_context():
            product = Product.query.get(1)  # Assuming product ID starts from 1
            self.assertEqual(product.name, "Test Product")
            self.assertEqual(product.description, "This is a test product")
            self.assertEqual(product.price, 10.99)

if __name__ == '__main__':
  unittest.main()