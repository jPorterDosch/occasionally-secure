from flask import Flask, request, jsonify
import sqlite3
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Configure the SQLAlchemy part
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    text = db.Column(db.Text, nullable=True)
    score = db.Column(db.Integer, nullable=False)

# Create the tables
@app.before_first_request
def create_tables():
    db.create_all()

# Route to add a review
@app.route('/add_review', methods=['POST'])
def add_review():
    user_id = request.json['user_id']
    product_id = request.json['product_id']
    text = request.json['text']
    score = request.json['score']
    
    # Check if the user has purchased the product
    purchase = Purchase.query.filter_by(user_id=user_id, product_id=product_id).first()
    if not purchase:
        return jsonify({'error': 'No purchase record for this product and user combination'}), 400
    
    # Check if the review already exists
    existing_review = Review.query.filter_by(user_id=user_id, product_id=product_id).first()
    if existing_review:
        return jsonify({'error': 'Review already submitted'}), 400

    # Add new review
    new_review = Review(user_id=user_id, product_id=product_id, text=text, score=score)
    db.session.add(new_review)
    db.session.commit()

    return jsonify({'message': 'Review added successfully'}), 201

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
