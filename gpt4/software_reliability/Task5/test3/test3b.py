from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
db = SQLAlchemy(app)

# Models

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)

# Create the tables
with app.app_context():
    db.create_all()

# Utility Functions

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('user_id')
        user = User.query.filter_by(id=user_id).first()
        
        if not user:
            return jsonify({"message": "User not found."}), 404
        if not user.is_admin:
            return jsonify({"message": "Admin privileges required."}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

# Routes for managing products

@app.route('/products', methods=['POST'])
@admin_required
def add_product():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    
    if Product.query.filter_by(name=name).first():
        return jsonify({"message": "Product already exists."}), 400
    
    new_product = Product(name=name, description=description, price=price)
    db.session.add(new_product)
    db.session.commit()
    
    return jsonify({"message": "Product added successfully!"}), 201

@app.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required
def remove_product(product_id):
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({"message": "Product not found."}), 404
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({"message": "Product removed successfully!"}), 200

@app.route('/products/<int:product_id>', methods=['PUT'])
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

# Test Route to simulate user login and actions
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({"message": "User not found."}), 404
    
    return jsonify({
        "message": f"Logged in as {username}",
        "user_id": user.id,
        "is_admin": user.is_admin
    }), 200

# Test Route to add users (for testing purposes)
@app.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    username = data.get('username')
    is_admin = data.get('is_admin', False)
    
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "User already exists."}), 400
    
    new_user = User(username=username, is_admin=is_admin)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User added successfully!"}), 201

if __name__ == '__main__':
    app.run(debug=True)
