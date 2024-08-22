from flask import Flask, jsonify, request
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
import pytest

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_unique_and_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# User Model (using Flask-Login)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    cart_id = db.Column(ForeignKey('cart.id', use_alter=True), unique=True)
    cart = db.relationship('Cart', backref='user')  # One-to-one

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)  # Use a hasher like werkzeug.security.generate_password_hash

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)  # Use a hasher like werkzeug.security.check_password_hash

    def __repr__(self):
        return f'<User {self.username}>'

# Product Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    stock = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Product {self.name}>'

    def serialize(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Cart Model (one-to-one relationship with User)
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    items = db.relationship('CartItem', backref='cart')

# Cart Item Model (many-to-many relationship between Product and Cart) 
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<CartItem product_id: {self.product_id}, quantity: {self.quantity}>'

# Function to create tables if they don't exist
def create_tables():
    with app.app_context():
        db.drop_all()
        db.create_all()
        user_data = {'username': 'test_user', 'password': 'password123'}
        user = User(username=user_data['username'])
        user.set_password(user_data['password'])
        db.session.add(user)

        product_data = [
    {
        "name": "T-Shirt",
        "description": "A comfortable and stylish T-shirt",
        "stock": 10,
        "price": 19.99
    },
    {
        "name": "Coffee Mug",
        "description": "The perfect mug for your morning coffee",
        "stock": 25,
        "price": 9.99
    },
    {
        "name": "Wireless Headphones",
        "description": "Enjoy your music wirelessly",
        "stock": 5,
        "price": 79.99
    },
    {
        "name": "Notebook",
        "description": "A stylish notebook for all your notes",
        "stock": 15,
        "price": 12.99
    },
    {
        "name": "Water Bottle",
        "description": "Stay hydrated with this reusable water bottle",
        "stock": 20,
        "price": 14.99
    }
]
        for item in product_data:
            product = Product(**item)
            db.session.add(product)
            db.session.commit()

# Function to serialize model objects to JSON format
def serialize(obj):
    if isinstance(obj, (list, tuple)):
        return [serialize(item) for item in obj]
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

# Import for password hashing (assuming Flask-WTF or Werkzeug)
from werkzeug.security import generate_password_hash, check_password_hash

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route to get product information by ID
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product.serialize())

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    try:
        # Get product ID, user ID, and quantity from request data
        product_id = request.json['product_id']
        user_id = request.json.get('user_id')
        quantity = int(request.json.get('quantity', 1))  # Default quantity to 1

        # Check for missing data
        if not product_id or not user_id:
            return jsonify({'error': 'Missing product or user ID'}), 400

        # Check product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Retrieve user based on user ID
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Check for a valid user (optional, depending on your authentication setup)
        # if not user.is_authenticated:
        #     return jsonify({'error': 'You must be logged in to add items to cart'}), 401

        # Retrieve or create user's cart (assuming one-to-one relationship)
        cart = user.cart or Cart()  # If cart doesn't exist, create one

        # Check stock availability
        if quantity > product.stock:
            return jsonify({'error': 'Insufficient product stock'}), 400

        # Add item to cart
        cart_item = CartItem(product=product, quantity=quantity)
        cart.items.append(cart_item)

        # Update product stock
        product.stock -= quantity

        # Save changes to database
        db.session.add(cart)
        db.session.add(product)
        db.session.commit()

        # Return success message
        return jsonify({'message': 'Product added to cart successfully!'})

    except (KeyError, ValueError):
        # Handle potential errors like invalid JSON data
        return jsonify({'error': 'Invalid data provided'}), 400

    except Exception as e:
        # Catch any unexpected exceptions (log for debugging)
        print(f"Error adding product to cart: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    # Check if username and password are provided
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    # Fetch user by username
    user = User.query.filter_by(username=username).first()

    # Check if user exists and password matches
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Login user if credentials are valid
    login_user(user)
    return jsonify({'message': 'Login successful!'})

# Logout route
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully!'})

if __name__ == '__main__':
    create_tables()  # Create tables if they don't exist
    app.run(debug=True)  # Run the development server