from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    review_text = db.Column(db.Text, nullable=True)
    review_score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref=db.backref('reviews', lazy=True))
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))

@app.before_first_request
def create_tables():
    db.create_all()
    # Optional: Add a test user and product
    if not User.query.filter_by(username='testuser').first():
        db.session.add(User(username='testuser'))
        db.session.add(Product(name='Sample Product'))
        db.session.commit()

# Endpoints
@app.route('/add_review', methods=['POST'])
def add_review():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    review_text = request.json.get('review_text')
    review_score = request.json.get('review_score')

    if review_score < 1 or review_score > 5:
        return jsonify({'error': 'Score must be between 1 and 5'}), 400

    review = Review(user_id=user_id, product_id=product_id, review_text=review_text, review_score=review_score)
    db.session.add(review)
    db.session.commit()

    return jsonify({'message': 'Review added successfully'}), 200

@app.route('/reviews/<int:product_id>')
def get_reviews(product_id):
    reviews = Review.query.filter_by(product_id=product_id).all()
    return jsonify([
        {
            'user_id': review.user_id,
            'review_text': review.review_text,
            'review_score': review.review_score,
            'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for review in reviews
    ]), 200

if __name__ == '__main__':
    app.run(debug=True)
