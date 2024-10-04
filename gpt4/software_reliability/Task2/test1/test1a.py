from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock
        })
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)

    user = User.query.get(user_id)
    product = Product.query.get(product_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    if product.stock < quantity:
        return jsonify({'error': 'Insufficient stock'}), 400

    new_cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
    db.session.add(new_cart_item)
    product.stock -= quantity  # Update stock
    db.session.commit()

    return jsonify({'message': 'Product added to cart successfully'})

if __name__ == '__main__':
    app.run(debug=True)
