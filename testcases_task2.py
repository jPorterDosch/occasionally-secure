import sqlite3
import requests

# Test cases for verifying the functionality and adherence to ground rules of task2test.py

# Connect to the database
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Query products table
print("Products Table:")
cursor.execute("SELECT * FROM products")
print(cursor.fetchall())

# Query carts table
print("\nCarts Table:")
cursor.execute("SELECT * FROM carts")
print(cursor.fetchall())

# Close connection
conn.close()

# test adding a product to cart.
data = {
    'user_id': 123,
    'product_id': 1,
    'quantity': 1000
}
response = requests.post('http://localhost:5000/add-to-cart', json=data)
print(response.json())

