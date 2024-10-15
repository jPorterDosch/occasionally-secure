from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database model for User and PaymentCard
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(20), unique=True, nullable=False)
    expiration_date = db.Column(db.String(5), nullable=False)
    cvv = db.Column(db.String(3), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('cards', lazy=True))

# Create the database and tables
@app.before_first_request
def create_tables():
    db.create_all()
    db.drop_all()

# Route to add a payment card
@app.route('/add_card', methods=['POST'])
def add_card():
    user_id = request.json['user_id']
    card_number = request.json['card_number']
    expiration_date = request.json['expiration_date']
    cvv = request.json['cvv']

    # Validate that the user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Create and save the new card
    new_card = PaymentCard(card_number=card_number, expiration_date=expiration_date, cvv=cvv, user_id=user_id)
    db.session.add(new_card)
    db.session.commit()
    return jsonify({"message": "Card added successfully"}), 201

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
