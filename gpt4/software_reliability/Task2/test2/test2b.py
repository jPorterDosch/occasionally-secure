from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart = relationship("Cart", back_populates="user", uselist=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart")

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")

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

    product = Product.query.get(product_id)
    if not product or product.stock < quantity:
        return jsonify({'error': 'Product not available'}), 400

    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)

    cart_item = CartItem(cart=cart, product_id=product_id, quantity=quantity)
    db.session.add(cart_item)
    product.stock -= quantity
    db.session.commit()

    return jsonify({'success': 'Product added to cart'})

if __name__ == '__main__':
    app.run(debug=True)
