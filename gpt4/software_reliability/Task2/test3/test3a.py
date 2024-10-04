from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ecommerce.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)

# Initialize the database and create tables
db.create_all()

# API Endpoints
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({'id': product.id, 'name': product.name, 'price': product.price, 'stock': product.stock})
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)

    if not all([user_id, product_id]):
        return jsonify({'error': 'Missing user_id or product_id'}), 400

    product = Product.query.get(product_id)
    if not product or product.stock <= 0:
        return jsonify({'error': 'Product not available'}), 404

    cart = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
    db.session.add(cart)
    db.session.commit()

    return jsonify({'message': 'Product added to cart successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)
