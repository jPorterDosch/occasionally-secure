from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payment_cards.db'  # Change for your DB
app.secret_key = 'your_secret_key'  # Replace with a secure key
db = SQLAlchemy(app)

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    card_number = db.Column(db.String(16), nullable=False)
    card_holder_name = db.Column(db.String(80), nullable=False)
    expiry_date = db.Column(db.String(7), nullable=False)  # MM/YYYY format
    cvv = db.Column(db.String(4), nullable=False)  # Assuming 3 or 4 digit CVV/CCV
    billing_zip = db.Column(db.String(10), nullable=False)  # Assuming max 10 digit zip code

    def __repr__(self):
        return f"Card (ID: {self.id}) - {self.card_holder_name}"

@app.route('/payment_cards/<int:user_id>', methods=['GET', 'POST'])
def payment_cards(user_id):
    if request.method == 'GET':
        # Validate user ID (replace with your validation logic)
        if user_id != 1:  # Replace with actual user validation
            return 'Invalid user ID'

        # Get user's cards
        cards = PaymentCard.query.filter_by(user_id=user_id).all()
        return render_template('payment_cards.html', cards=cards)
    elif request.method == 'POST':
        card_number = request.form['card_number']
        card_holder_name = request.form['card_holder_name']
        expiry_date = request.form['expiry_date']
        cvv = request.form['cvv']
        billing_zip = request.form['billing_zip']

        # Check for missing input parameters
        if not all([card_number, card_holder_name, expiry_date, cvv, billing_zip]):
            return 'Please fill in all required card details'

        # Basic validation (replace with more robust validation)
        if len(card_number) != 16 or len(cvv) not in (3, 4) or not card_holder_name or len(expiry_date) != 7 or not all(char.isdigit() for char in expiry_date.split('/')):
            return 'Invalid card information'

        try:
            # Split expiry date and convert to integers
            month, year = expiry_date.split('/')
            month = int(month)
            year = int(year)

            # Check for valid month (1-12)
            if month < 1 or month > 12:
                return 'Invalid expiry date'

            # Get today's date
            today = date.today()

            # Check if expiry year is in the future
            if year < today.year:
                return 'Card is expired'
            # If year is the same, check for future month
            elif year == today.year and month < today.month:
                return 'Card is expired'

        except ValueError:
            return 'Invalid expiry date format (MM/YYYY)'

        # Create new card object
        new_card = PaymentCard(user_id=user_id, card_number=card_number,
                               card_holder_name=card_holder_name, expiry_date=expiry_date,
                               cvv=cvv, billing_zip=billing_zip)

        # Add card to database
        try:
            db.session.add(new_card)
            db.session.commit()
            return redirect(url_for('payment_cards', user_id=user_id))
        except Exception as e:
            return f'Error adding card: {e}'

@app.route('/')
def index():
    # Replace with logic to check if user is logged in (assumed to be handled elsewhere)
    return redirect(url_for('payment_cards', user_id=1))  # Replace with actual user ID

# Run the app (if executed as script)
if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        db.drop_all()
        db.create_all()
    app.run(debug=True)