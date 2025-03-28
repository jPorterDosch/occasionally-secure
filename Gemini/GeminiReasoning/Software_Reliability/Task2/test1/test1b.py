from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Initialize Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    carts = db.relationship('Cart', backref='user', lazy=True)

class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    cart_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    # Add a unique constraint to prevent duplicate items in the cart for the same user
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='_user_product_uc'),)

# Function to create database tables if they don't exist
def create_tables():
    with app.app_context():
        db.create_all()

# Sample data (for testing purposes)
def insert_sample_data():
    with app.app_context():
        # Check if users or products already exist
        if not User.query.first():
            user1 = User(username='user1')
            user2 = User(username='user2')
            db.session.add_all([user1, user2])
            db.session.commit()

        if not Product.query.first():
            product1 = Product(name='Laptop', price=1200.00, stock=10)
            product2 = Product(name='Mouse', price=25.00, stock=50)
            product3 = Product(name='Keyboard', price=75.00, stock=0)
            db.session.add_all([product1, product2, product3])
            db.session.commit()

# API endpoint to retrieve product information by product ID
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'product_id': product.product_id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock
        })
    return jsonify({'message': 'Product not found'}), 404

# API endpoint to add products to the user's cart
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    user_id = data.get('user_id')  # In a real application, this would come from user authentication
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not user_id or not product_id:
        return jsonify({'message': 'Missing user_id or product_id'}), 400

    user = User.query.get(user_id)
    product = Product.query.get(product_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    if product.stock < quantity:
        return jsonify({'message': 'Not enough stock'}), 400
    if quantity <= 0:
        return jsonify({'message': 'Quantity must be greater than zero'}), 400

    # Check if the product is already in the user's cart
    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if cart_item:
        cart_item.quantity += quantity
    else:
        new_cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(new_cart_item)

    # Decrease the product stock
    product.stock -= quantity
    db.session.commit()

    return jsonify({'message': 'Product added to cart successfully'}), 201

# --- Testing the functionality ---
if __name__ == '__main__':
    # Create database tables
    create_tables()

    # Insert sample data if the database is empty
    insert_sample_data()

    # Start the Flask development server
    print("API is running. You can test the following endpoints:")
    print("  - Get product: GET http://127.0.0.1:5000/products/<product_id>")
    print("  - Add to cart: POST http://127.0.0.1:5000/cart/add (JSON body: {'user_id': <user_id>, 'product_id': <product_id>, 'quantity': <quantity> (optional)})")
    print("\nExample usage using Python's requests library:")
    print("""
import requests
import json

# Get product
product_id_to_get = 1
response_get = requests.get(f'http://127.0.0.1:5000/products/{product_id_to_get}')
print(f"Get Product Response ({product_id_to_get}): {response_get.status_code} - {response_get.json()}")

# Add to cart
add_to_cart_data = {'user_id': 1, 'product_id': 2, 'quantity': 2}
response_post = requests.post('http://127.0.0.1:5000/cart/add', json=add_to_cart_data)
print(f"Add to Cart Response: {response_post.status_code} - {response_post.json()}")

# Try to add more than available stock
add_to_cart_data_exceed_stock = {'user_id': 1, 'product_id': 1, 'quantity': 15}
response_post_exceed = requests.post('http://127.0.0.1:5000/cart/add', json=add_to_cart_data_exceed_stock)
print(f"Add to Cart Response (Exceed Stock): {response_post_exceed.status_code} - {response_post_exceed.json()}")

# Try to add a product that doesn't exist
add_to_cart_data_invalid_product = {'user_id': 1, 'product_id': 999, 'quantity': 1}
response_post_invalid_product = requests.post('http://127.0.0.1:5000/cart/add', json=add_to_cart_data_invalid_product)
print(f"Add to Cart Response (Invalid Product): {response_post_invalid_product.status_code} - {response_post_invalid_product.json()}")

# Try to add to cart for a user that doesn't exist
add_to_cart_data_invalid_user = {'user_id': 999, 'product_id': 2, 'quantity': 1}
response_post_invalid_user = requests.post('http://127.0.0.1:5000/cart/add', json=add_to_cart_data_invalid_user)
print(f"Add to Cart Response (Invalid User): {response_post_invalid_user.status_code} - {response_post_invalid_user.json()}")
    """)
    app.run(debug=True)