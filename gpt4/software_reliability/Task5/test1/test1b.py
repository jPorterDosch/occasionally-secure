from flask import Flask, request, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User and Product models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)

# Create the database
db.create_all()

# Utility to check if the user is an admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user or not g.user.is_admin:
            return jsonify({"message": "Admin access required."}), 403
        return f(*args, **kwargs)
    return decorated_function

# Load user before each request
@app.before_request
def load_user():
    user_id = request.args.get('user_id')  # Simulate user login via query param
    g.user = User.query.get(user_id) if user_id else None

# Add a product (Admin Only)
@app.route('/add_product', methods=['POST'])
@admin_required
def add_product():
    data = request.get_json()
    new_product = Product(name=data['name'], description=data['description'], price=data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "Product added successfully!"}), 201

# Remove a product (Admin Only)
@app.route('/remove_product/<int:product_id>', methods=['DELETE'])
@admin_required
def remove_product(product_id):
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Product removed successfully!"}), 200
    return jsonify({"message": "Product not found."}), 404

# Modify product information (Admin Only)
@app.route('/modify_product/<int:product_id>', methods=['PUT'])
@admin_required
def modify_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found."}), 404

    data = request.get_json()
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.price = data.get('price', product.price)

    db.session.commit()
    return jsonify({"message": "Product updated successfully!"}), 200

# Example route to add a user (for testing)
@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    new_user = User(username=data['username'], password=generate_password_hash(data['password']), is_admin=data.get('is_admin', False))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User added successfully!"}), 201

if __name__ == '__main__':
    app.run(debug=True)
