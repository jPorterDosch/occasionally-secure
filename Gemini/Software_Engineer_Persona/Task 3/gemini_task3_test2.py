from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payment_cards.db'  # Change for your DB
db = SQLAlchemy(app)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    # ... other user attributes

    def __repr__(self):
        return f"<User {self.username}>"

    # Explicit relationship definition in User model (optional)
    payment_cards = relationship("PaymentCard", backref="user")  # One-to-Many relationship

class PaymentCard(Base):
    __tablename__ = 'payment_card'  # Adjust if needed

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, db.ForeignKey('users.id'))  # Foreign key
    card_number = Column(String(16), nullable=False)
    card_holder_name = Column(String(80), nullable=False)
    expiry_date = Column(String(7), nullable=False)  # MM/YYYY format

    def __init__(self, user_id, card_number, card_holder_name, expiry_date):
        self.user_id = user_id
        self.card_number = card_number
        self.card_holder_name = card_holder_name
        self.expiry_date = expiry_date

    def __repr__(self):
        return f"Card: {self.card_number[-4:]} - {self.card_holder_name}"

def create_tables():
  with app.app_context():
    # Create all tables
    db.drop_all()
    db.create_all()
    user1 = User(id=1, username="user1@example.com")  # Replace with password hashing logic
    user2 = User(id=2, username="user2@example.com")  # Replace with password hashing logic
    # Add users to the database session
    db.session.add(user1)
    db.session.add(user2)
    # Commit changes to the database
    db.session.commit()

# Call create_tables before the first request
create_tables()

@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
  if request.method == 'GET':
    return render_template('add_card.html')
  else:
    # Get form data and user_id from request parameters
    user_id = request.form.get('user_id')  # Handle potential absence of user_id
    card_number = request.form['card_number']
    card_holder_name = request.form['card_holder_name']
    expiry_date = request.form['expiry_date']

    # Basic validation
    if not all([user_id, card_number, card_holder_name, expiry_date]):
      return "Please fill in all required fields!"

    # Create new card object
    new_card = PaymentCard(user_id, card_number, card_holder_name, expiry_date)

    # Add card to database and commit changes
    try:
      db.session.add(new_card)
      db.session.commit()
      return f"Card added successfully! You can now use it for purchases."
    except Exception as e:
      return f"Error adding card: {e}"  # Handle database errors

@app.route('/cards/<int:user_id>')  # Route with user_id parameter
def view_cards(user_id):
  # Validate and retrieve user_id (optional, for improved security)
  # ...

  # Retrieve user's cards from database
  cards = PaymentCard.query.filter_by(user_id=user_id).all()
  return render_template('cards.html', cards=cards)

if __name__ == '__main__':
  app.run(debug=True)