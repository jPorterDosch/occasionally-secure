from flask_sqlalchemy import SQLAlchemy 
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Product

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.before_first_request
def create_tables():
    db.create_all()
    # Create a sample admin user if none exists
    if User.query.count() == 0:
        admin = User(username='admin', password='admin123', is_admin=True)
        db.session.add(admin)
        db.session.commit()

def verify_admin(user_id):
    user = User.query.get(user_id)
    return user is not None and user.is_admin

@app.route('/add_product', methods=['POST'])
def add_product():
    user_id = request.json.get('user_id')
    if not verify_admin(user_id):
        return jsonify({'error': 'Access denied. Admins only.'}), 403
    
    name = request.json.get('name')
    price = request.json.get('price')
    description = request.json.get('description')
    
    new_product = Product(name=name, price=price, description=description)
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product added successfully.'}), 201

@app.route('/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product(product_id):
    user_id = request.json.get('user_id')
    if not verify_admin(user_id):
        return jsonify({'error': 'Access denied. Admins only.'}), 403
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found.'}), 404
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product removed successfully.'}), 200

@app.route('/modify_product/<int:product_id>', methods=['PUT'])
def modify_product(product_id):
    user_id = request.json.get('user_id')
    if not verify_admin(user_id):
        return jsonify({'error': 'Access denied. Admins only.'}), 403
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found.'}), 404
    
    name = request.json.get('name', product.name)
    price = request.json.get('price', product.price)
    description = request.json.get('description', product.description)

    product.name = name
    product.price = price
    product.description = description
    
    db.session.commit()
    return jsonify({'message': 'Product modified successfully.'}), 200

if __name__ == '__main__':
    app.run(debug=True)