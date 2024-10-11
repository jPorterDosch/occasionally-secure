from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

# Initialize Flask app
app = Flask(__name__)

# Configure SQLAlchemy to use SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    role = db.Column(db.String(80), nullable=False)  # "admin" or "user"

# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)

# Create all the tables in the database
with app.app_context():
    db.create_all()

# Helper function to get the current logged-in user (simulated for this example)
def get_current_user():
    # Simulate fetching the current user (in real-world use authentication)
    return User.query.filter_by(username="admin_user").first()

# Role-based access control decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = get_current_user()
        if current_user.role != "admin":
            return jsonify({"error": "Admin privileges required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# Route to add a new product (Admin only)
@app.route('/products', methods=['POST'])
@admin_required
def add_product():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')

    if not name or not price:
        return jsonify({"error": "Product name and price are required"}), 400

    new_product = Product(name=name, description=description, price=price)
    db.session.add(new_product)
    db.session.commit()

    return jsonify({"message": "Product added successfully", "product": {"id": new_product.id, "name": new_product.name}}), 201

# Route to modify an existing product (Admin only)
@app.route('/products/<int:product_id>', methods=['PUT'])
@admin_required
def modify_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.get_json()
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.price = data.get('price', product.price)

    db.session.commit()

    return jsonify({"message": "Product updated successfully", "product": {"id": product.id, "name": product.name}}), 200

# Route to remove an existing product (Admin only)
@app.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required
def remove_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()

    return jsonify({"message": "Product removed successfully"}), 200

# Route to get all products (Public)
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    product_list = [{"id": p.id, "name": p.name, "description": p.description, "price": p.price} for p in products]
    return jsonify({"products": product_list}), 200

# Test the API
if __name__ == '__main__':
    # Add a test user and test product for demo purposes
    with app.app_context():
        if not User.query.filter_by(username="admin_user").first():
           
