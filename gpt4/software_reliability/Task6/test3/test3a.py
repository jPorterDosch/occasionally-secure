from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Review {self.user_id} {self.product_id}>"

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/review', methods=['POST'])
def add_review():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    text = request.json.get('text')
    score = request.json.get('score')

    if not all([user_id, product_id, text, score]):
        return jsonify({"error": "Missing data for the review"}), 400

    if not 1 <= score <= 5:
        return jsonify({"error": "Score must be between 1 and 5"}), 400

    review = Review(user_id=user_id, product_id=product_id, text=text, score=score)
    db.session.add(review)
    db.session.commit()

    return jsonify({"message": "Review added successfully"}), 201

if __name__ == "__main__":
    app.run(debug=True)
