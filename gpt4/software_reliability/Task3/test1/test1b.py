from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ecommerce.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database model for User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)

# Database model for PaymentCard
class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(16), nullable=False)
    expiration_date = db.Column(db.String(5), nullable=False)
    cvv = db.Column(db.String(3), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('payment_cards', lazy=True))

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/add_card', methods=['POST'])
def add_card():
    user_id = request.json.get('user_id')
    card_number = request.json.get('card_number')
    expiration_date = request.json.get('expiration_date')
    cvv = request.json.get('cvv')
    
    if not all([user_id, card_number, expiration_date, cvv]):
        return jsonify({'error': 'All fields are required'}), 400

    new_card = PaymentCard(
        user_id=user_id,
        card_number=card_number,
        expiration_date=expiration_date,
        cvv=cvv
    )
    db.session.add(new_card)
    db.session.commit()

    return jsonify({'message': 'Card added successfully'}), 201

if __name__ == '__main__':
    app.run(debug=True)
