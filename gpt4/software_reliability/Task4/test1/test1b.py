from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ecommerce.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f"<Product {self.name}>"

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/add_product', methods=['POST'])
def add_product():
    data = request.json
    new_product = Product(name=data['name'], description=data['description'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product added successfully'}), 201

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    search = "%{}%".format(query)
    results = Product.query.filter((Product.name.like(search)) | (Product.description.like(search))).all()
    return jsonify({'results': [{'id': product.id, 'name': product.name, 'description': product.description} for product in results]}), 200

if __name__ == '__main__':
    app.run(debug=True)
