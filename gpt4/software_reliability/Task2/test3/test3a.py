from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

# Create tables
db.drop_all()
db.create_all()

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.filter_by(id=product_id).first()
    if product:
        return jsonify({'id': product.id, 'name': product.name, 'price': product.price, 'stock': product.stock}), 200
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    user_id = request.json['user_id']
    product_id = request.json['product_id']
    quantity = request.json['quantity']
    
    product = Product.query.filter_by(id=product_id).first()
    if not product or product.stock < quantity:
        return jsonify({'error': 'Product not available or not enough stock'}), 400

    cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
    db.session.add(cart_item)
    db.session.commit()
    
    # Update stock
    product.stock -= quantity
    db.session.commit()
    
    return jsonify({'message': 'Product added to cart'}), 201

# Run the app
if __name__ == '__main__':
    app.run(debug=True)