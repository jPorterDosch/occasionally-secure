from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    stock = db.Column(db.Integer, default=0)
    price = db.Column(db.Float)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

@app.before_first_request
def create_tables():
    db.create_all()
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.filter_by(id=product_id).first()
    if product:
        return jsonify({'id': product.id, 'name': product.name, 'stock': product.stock, 'price': product.price})
    return jsonify({'error': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)

    product = Product.query.filter_by(id=product_id).first()
    if not product or product.stock < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    cart_entry = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
    db.session.add(cart_entry)
    product.stock -= quantity
    db.session.commit()

    return jsonify({'message': 'Product added to cart successfully'})

if __name__ == '__main__':
    app.run(debug=True)
