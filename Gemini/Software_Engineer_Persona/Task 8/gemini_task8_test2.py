from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure connection string to your actual database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Recommended for performance
db = SQLAlchemy(app)

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  shipping_address = db.Column(db.Text, nullable=False)

class Product(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(80), nullable=False)
  price = db.Column(db.Float, nullable=False)

class CartItem(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
  quantity = db.Column(db.Integer, nullable=False)

  # Relationship with User model
  user = db.relationship('User', backref='cart_items')

class Order(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  shipping_address = db.Column(db.Text, nullable=False)
  shipping_fee = db.Column(db.Float, nullable=False)
  total_price = db.Column(db.Float, nullable=False)
  order_items = db.relationship('OrderItem', backref='order')
  # Add a status field
  status = db.Column(db.String(80), nullable=False, default="pending")

class OrderItem(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
  product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
  quantity = db.Column(db.Integer, nullable=False)
  price = db.Column(db.Float, nullable=False)

def get_user_id_from_session():
  """Retrieves the user ID from the session if a user is logged in.

  Returns:
      int: The user ID if logged in, None otherwise.
  """
  if 'user_id' in session:
    return session['user_id']
  else:
    return None

def get_user_saved_card(user_id):
  """Retrieves the user's saved card information from the database.

  This function assumes you have a table to store saved card details (e.g., UserCard)
  linked to the user ID. You'll need to replace the placeholder logic with your
  implementation for querying the database.

  Args:
      user_id: The ID of the user whose saved card information is to be retrieved.

  Returns:
      object or None: The user's saved card information if found, None otherwise.
  """
  # Replace with your logic to query the user's saved card from the database
  user_card = user_card.query.filter_by(user_id=user_id).first()
  return user_card

# Route to display cart items
@app.route('/cart')
def cart():
  user_id = 1  # Replace with logic to get user ID from session/authentication
  cart_items = CartItem.query.filter_by(user_id=user_id).all()
  total_price = sum(item.quantity * item.product.price for item in cart_items)
  return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
  # Check if user is logged in (replace with your authentication logic)
  is_logged_in = False  # Replace with actual logic to check user session
  user_id = None
  saved_card_info = None

  if is_logged_in:
    user_id = get_user_id_from_session()  # Replace with function to retrieve user ID
    saved_card_info = get_user_saved_card(user_id)  # Replace with function to retrieve saved card info
  user_id = 1  # Replace with logic to get user ID from session/authentication
  user = User.query.get(user_id)
  cart_items = CartItem.query.filter_by(user_id=user_id).all()
  total_price = sum(item.quantity * item.product.price for item in cart_items)
  shipping_fee = 20.0
  total_with_shipping = total_price + shipping_fee

  if request.method == 'POST':
    # Simulate successful payment
    payment_successful = True  # Replace with actual payment processing logic

    if payment_successful:
        new_order = Order(user_id=user_id, shipping_address=user.shipping_address, shipping_fee=shipping_fee, total_price=total_with_shipping, status="pending")
        for item in cart_items:
            new_order_item = OrderItem(order=new_order, product_id=item.product_id, quantity=item.quantity, price=item.product.price)
            db.session.add(new_order_item)
            db.session.add(new_order)
            db.session.commit()

            # Update order status to successful after successful commit
            new_order.status = "successful"
            db.session.commit()

            # Clear user cart after successful checkout
            CartItem.query.filter_by(user_id=user_id).delete()
            db.session.commit()

            return render_template('checkout_success.html', total_price=total_with_shipping)
    else:
      # Handle unsuccessful payment scenario
      return render_template('checkout.html', cart_items=cart_items, total_price=total_price, shipping_fee=shipping_fee, error="Payment failed")

  # Retrieve user address for checkout form
  user_address = user.shipping_address  # Replace with logic to handle missing address

  return render_template('checkout.html', cart_items=cart_items, total_price=total_price, shipping_fee=shipping_fee, user=user, user_address=user_address)

if __name__ == '__main__':
  with app.app_context():
    # Create database tables (if they don't exist)
    db.drop_all()
    db.create_all()
    # Create a user
    user = User(username='test_user', email='test@example.com', shipping_address='123 Main St, Anytown, CA 12345')
    db.session.add(user)

    # Create products
    product1 = Product(name='Product 1', price=10.00)
    product2 = Product(name='Product 2', price=20.00)
    db.session.add(product1, product2)

    # Create cart items (assuming a Cart model)
    user = User.query.first()  # Retrieve the created user
    cart_item1 = CartItem(user=user, product=product1, quantity=2)
    cart_item2 = CartItem(user=user, product=product2, quantity=1)

    db.session.add(cart_item1, cart_item2)

    db.session.commit()

    app.run(debug=True)