from flask import Flask, request, jsonify
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    card_number = db.Column(db.String(20), nullable=False)
    card_holder_name = db.Column(db.String(100), nullable=False)
    expiration_date = db.Column(db.String(10), nullable=False)
    cvv = db.Column(db.String(3), nullable=False)

    def __repr__(self):
        return f"<Card {self.card_number}>"

@app.before_first_request
def create_tables():
    db.create_all()
    db.drop_all()

@app.route('/add_card', methods=['POST'])
def add_card():
    data = request.json
    user_id = data.get('user_id')
    card_number = data.get('card_number')
    card_holder_name = data.get('card_holder_name')
    expiration_date = data.get('expiration_date')
    cvv = data.get('cvv')
    
    # Basic validation
    if not all([user_id, card_number, card_holder_name, expiration_date, cvv]):
        return jsonify({"error": "Missing information"}), 400

    # Insert the new card
    new_card = PaymentCard(user_id=user_id, card_number=card_number, 
                           card_holder_name=card_holder_name, expiration_date=expiration_date, cvv=cvv)
    db.session.add(new_card)
    db.session.commit()
    return jsonify({"message": "Card added successfully"}), 201

if __name__ == '__main__':
    app.run(debug=True)
