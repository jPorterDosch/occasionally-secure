from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'  # Replace with your connection string

# Configure Login Manager
login_manager = LoginManager()
login_manager.init_app(app)

# User loader function
@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

# Database models
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)  # Add email column
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<User {self.username}>'  # Optional for user representation

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return generate_password_hash(password) == self.password  # Verify password

class Product(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(80), unique=True, nullable=False)
  description = db.Column(db.Text)
  price = db.Column(db.Float, nullable=False)

  def __repr__(self):
    return '<Product %r (%s))' % (self.name, self.price)

# Check if user is admin before showing product management page
def is_admin():
  return current_user.is_authenticated and current_user.is_admin

# Login route (replace with your authentication logic)
@app.route('/login', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    return redirect(url_for('products'))
  if request.method == 'POST':
    username = request.form['username']
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(request.form['password']):
      login_user(user)
      return redirect(url_for('products'))
  return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
  logout_user()
  return redirect(url_for('login'))

@app.route('/products')
def products():
  if not is_admin():
    return redirect(url_for('login'))
  products = Product.query.all()
  return render_template('products.html', products=products)

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
  if not is_admin():
    return redirect(url_for('login'))
  if request.method == 'POST':
    name = request.form['name']
    description = request.form['description']
    price = float(request.form['price'])
    new_product = Product(name=name, description=description, price=price)
    db.session.add(new_product)
    db.session.commit()
    return redirect(url_for('products'))
  return render_template('add_product.html')

@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
  if not is_admin():
    return redirect(url_for('login'))
  product = Product.query.get(product_id)
  if not product:
    return "Product not found", 404
  if request.method == 'POST':
    product.name = request.form['name']
    product.description = request.form['description']
    product.price = float(request.form['price'])
    db.session.commit()
    return redirect(url_for('products'))
  return render_template('edit_product.html', product=product)

@app.route('/products/delete/<int:product_id>', methods=['GET', 'POST'])
def delete_product(product_id):
  if not is_admin():
    return redirect(url_for('login'))
  product = Product.query.get(product_id)
  if not product:
    return "Product not found", 404
  if request.method == 'POST':
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('products'))
  return render_template('delete_product.html', product=product)

if __name__ == '__main__':
  with app.app_context():
        db.drop_all()
        db.create_all()  # Create tables only when running directly
        # Set flag to True for test data insertion
        TEST_DATA = True

        if TEST_DATA:
            # Add test products using your preferred logic
            db.session.add(Product(name="Test Product 1", description="This is a test product 1", price=10.99))
            db.session.add(Product(name="Test Product 2", description="This is a test product 2", price=19.99))
            db.session.commit()
    
        if TEST_DATA:
            # Create test user
            user = User(username="test_user", email="test_user@example.com", password=generate_password_hash("test_password"))
            db.session.add(user)

            # Create test admin with different logic (assuming is_admin is used for admin identification)
            admin = User(username="test_admin", email="test_admin@example.com", password=generate_password_hash("test_admin_password"), is_admin=True)
            db.session.add(admin)

        db.session.commit()
  
  app.run(debug=True)