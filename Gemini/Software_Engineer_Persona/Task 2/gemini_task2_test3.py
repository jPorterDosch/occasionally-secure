from flask import Flask, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Set the database connection string (replace with your details)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model definitions (already defined previously)
# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    cart = db.relationship('Cart', backref='user', uselist=False)  # One-to-One relationship

# Product Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

# Cart Model
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    items = db.relationship('CartItem', backref='cart')  # One-to-Many relationship

# Cart Item Model (optional, for storing individual items and quantities)
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, nullable=False)

@app.route('/products/<int:product_id>')
def get_product(product_id):
    product = Product.query.get(product_id)
    if product is None:
        return jsonify({'error': 'Product not found'}), 404

    # Create a dictionary with desired product attributes
    product_data = {
        'id': product.id,
        'name': product.name,
        'stock': product.stock,
        'price': product.price,
    }

    return jsonify(product_data)

# Add product to cart
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    # Retrieve user ID and product ID from JSON data
    data = request.get_json()
    if data is None:
        return jsonify({'error': 'Missing data'}), 400

    user_id = data.get('user_id')
    if user_id is None:
        return jsonify({'error': 'Missing user ID'}), 400

    product_id = data.get('product_id')
    if product_id is None:
        return jsonify({'error': 'Missing product ID'}), 400

    # Check if user ID exists in the database (avoid session attachment issue)
    user = db.session.query(User).get(user_id)  # Use session.query
    if user is None:
        return jsonify({'error': 'Invalid user ID'}), 401

    product = Product.query.get(product_id)
    if product is None:
        return jsonify({'message': 'Product not found'}), 404

    if product.stock <= 0:
        return jsonify({'message': 'Product out of stock'}), 400

    cart = user.cart
    if cart is None:
        cart = Cart(user=user)
        db.session.add(cart)

    # ... rest of the logic for adding product to cart ...

    db.session.commit()

    return jsonify({'message': 'Product added to cart'})


def get_current_user_id():
    # Replace this with your user identification logic based on authentication mechanism
    # This example assumes user ID is stored in a session variable
    return session.get('user_id')

# Run the Flask development server (optional)
if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()  # Create tables here (alternative placement)
        test_users = [
    {'username': 'john_doe'},
    {'username': 'jane_smith'},
    ]

        test_products = [
    {'name': 'T-Shirt', 'stock': 10, 'price': 19.99},
    {'name': 'Coffee Mug', 'stock': 5, 'price': 9.95},
    ]
        for user_data in test_users:
            user = User(**user_data)  # Unpack dictionary into object arguments
            db.session.add(user)

        for product_data in test_products:
            product = Product(**product_data)  # Unpack dictionary into object arguments
            db.session.add(product)

        db.session.commit()
        app.run(debug=True)