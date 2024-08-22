from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'  # Change for your DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Recommended for production
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    cart = db.relationship('CartItem', backref='user', lazy='dynamic')  # Change lazy to 'dynamic'

# Product Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    cart_items = db.relationship('CartItem', backref='product', lazy=True)  # One product to many cart items

# Cart Item Model (association table)
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

# Function to create tables automatically (one-time use)
def create_tables():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Create users
        user1 = User(username="user1")
        user2 = User(username="user2")
        db.session.add(user1)
        db.session.add(user2)

        # Create products
        product1 = Product(name="Product A", price=10.99, stock=5)
        product2 = Product(name="Product B", price=25.50, stock=3)
        db.session.add(product1)
        db.session.add(product2)

        # Commit changes
        db.session.commit()

# Route to get product information by ID
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product is None:
        return jsonify({'message': 'Product not found'}), 404
    return jsonify(product.serialize())

@app.route('/cart', methods=['POST'])
def add_to_cart():
    # Extract data from request
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    user_id = data.get('user_id')  # Get user ID from request body

    # Check for missing data
    if not (product_id or user_id) or quantity <= 0:
        return jsonify({'message': 'Missing required data'}), 400

    # Get product and check stock
    product = Product.query.get(product_id)
    if product is None or product.stock < quantity:
        return jsonify({'message': 'Product not found or out of stock'}), 400

    # Get user (ensure successful retrieval)
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'Invalid user ID'}), 400

    # Reduce product stock (ensure atomicity)
    if product.stock >= quantity:
        product.stock -= quantity

    # Add new cart item (quantity is handled)
    new_item = CartItem(user=user, product=product, quantity=quantity)
    db.session.add(new_item)

    # Commit changes in a single transaction (atomic)
    try:
        db.session.commit()
    except:
        db.session.rollback()  # Rollback on any exceptions
        return jsonify({'message': 'An error occurred'}), 500

    return jsonify({'message': 'Product added to cart'})

# Helper method to serialize model objects
def serialize(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Add serialize method to models
Product.serialize = serialize
CartItem.serialize = serialize
User.serialize = serialize

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)  # Set debug to False for production