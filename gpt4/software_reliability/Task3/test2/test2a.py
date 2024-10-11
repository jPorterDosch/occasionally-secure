from flask import Flask, request, render_template_string, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

# Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a real key in production

db = SQLAlchemy(app)

# Database model for storing user payment cards
class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    card_number = db.Column(db.String(16), nullable=False)
    cardholder_name = db.Column(db.String(100), nullable=False)
    expiry_date = db.Column(db.String(5), nullable=False)
    cvv = db.Column(db.String(3), nullable=False)

    def __repr__(self):
        return f'<Card {self.card_number}>'

# Ensure the database and tables are created
@app.before_first_request
def create_tables():
    db.create_all()
    db.drop_all()

# Home page route
@app.route('/')
def home():
    # Example form for adding a payment card
    return render_template_string('''
    <form action="/add_card" method="post">
        <input type="number" name="user_id" placeholder="User ID" required><br>
        <input type="text" name="card_number" placeholder="Card Number" maxlength="16" required><br>
        <input type="text" name="cardholder_name" placeholder="Cardholder Name" required><br>
        <input type="text" name="expiry_date" placeholder="MM/YY" required><br>
        <input type="text" name="cvv" placeholder="CVV" maxlength="3" required><br>
        <button type="submit">Add Card</button>
    </form>
    ''')

# Route to handle adding a payment card
@app.route('/add_card', methods=['POST'])
def add_card():
    user_id = request.form.get('user_id')
    card_number = request.form.get('card_number')
    cardholder_name = request.form.get('cardholder_name')
    expiry_date = request.form.get('expiry_date')
    cvv = request.form.get('cvv')

    if len(card_number) == 16 and len(cvv) == 3:
        new_card = PaymentCard(
            user_id=int(user_id),
            card_number=card_number,
            cardholder_name=cardholder_name,
            expiry_date=expiry_date,
            cvv=cvv
        )
        db.session.add(new_card)
        db.session.commit()
        return 'Card added successfully'
    else:
        return 'Invalid card details', 400

if __name__ == '__main__':
    app.run(debug=True)
