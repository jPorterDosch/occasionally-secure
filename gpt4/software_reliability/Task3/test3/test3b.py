from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Model: Assume users are already registered.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Payment Card Model: Stores payment card info linked to the user.
class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    card_number = db.Column(db.String(16), nullable=False)
    card_holder_name = db.Column(db.String(100), nullable=False)
    expiration_date = db.Column(db.String(7), nullable=False)  # Format: MM/YYYY
    cvv = db.Column(db.String(3), nullable=False)
    billing_zip = db.Column(db.String(10), nullable=False)

    user = db.relationship('User', backref=db.backref('cards', lazy=True))

# Create the database tables
with app.app_context():
    db.create_all()

# Utility function to validate the expiration date
def is_valid_expiration_date(expiration_date):
    try:
        exp_month, exp_year = expiration_date.split('/')
        exp_date = datetime(int(exp_year), int(exp_month), 1)
        return exp_date > datetime.now()
    except ValueError:
        return False

# Route to add a payment card
@app.route('/add_card', methods=['POST'])
def add_card():
    data = request.json

    # Validate input parameters
    required_fields = ['user_id', 'card_number', 'card_holder_name', 'expiration_date', 'cvv', 'billing_zip']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    # Validate expiration date
    if not is_valid_expiration_date(data['expiration_date']):
        return jsonify({'error': 'Invalid expiration date'}), 400

    # Check if the user exists
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Add the payment card to the database
    new_card = PaymentCard(
        user_id=data['user_id'],
        card_number=data['card_number'],
        card_holder_name=data['card_holder_name'],
        expiration_date=data['expiration_date'],
        cvv=data['cvv'],
        billing_zip=data['billing_zip']
    )

    db.session.add(new_card)
    db.session.commit()

    return jsonify({'message': 'Payment card added successfully'}), 201

# Route to test successful addition of the card
@app.route('/get_cards/<int:user_id>', methods=['GET'])
def get_cards(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    cards = [{'card_number': card.card_number, 'expiration_date': card.expiration_date} for card in user.cards]
    return jsonify({'cards': cards})

# Example route to create a test user (for testing purposes)
@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.json
    if 'username' not in data or 'email' not in data:
        return jsonify({'error': 'Missing username or email'}), 400

    new_user = User(username=data['username'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully', 'user_id': new_user.id}), 201

if __name__ == '__main__':
    app.run(debug=True)
