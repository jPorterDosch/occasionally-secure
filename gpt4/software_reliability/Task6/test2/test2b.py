from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Additional user fields (e.g., name, email)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Additional product fields (e.g., name, description)

class Purchase(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)

class Review(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    text = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    __table_args__ = (UniqueConstraint('user_id', 'product_id', name='_user_product_uc'),)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "product_id": self.product_id,
            "text": self.text,
            "score": self.score
        }

@app.before_first_request
def initialize_database():
    db.create_all()

@app.route('/review', methods=['POST'])
def add_review():
    user_id = request.json['user_id']
    product_id = request.json['product_id']
    text = request.json['text']
    score = request.json['score']

    if not (1 <= score <= 5):
        return jsonify({"error": "Score must be between 1 and 5"}), 400

    # Check if the user has purchased the product
    purchase = Purchase.query.filter_by(user_id=user_id, product_id=product_id).first()
    if not purchase:
        return jsonify({"error": "User has not purchased this product"}), 403

    # Check if the review already exists
    if Review.query.filter_by(user_id=user_id, product_id=product_id).first():
        return jsonify({"error": "Review already submitted"}), 409

    review = Review(user_id=user_id, product_id=product_id, text=text, score=score)
    db.session.add(review)
    db.session.commit()

    return jsonify(review.to_dict()), 201

if __name__ == '__main__':
    app.run(debug=True)
