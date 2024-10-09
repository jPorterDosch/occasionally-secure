from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)

# Create an engine and tables
engine = create_engine('sqlite:///ecommerce.db')
Base.metadata.create_all(engine)

# Create a Session
Session = sessionmaker(bind=engine)
session = Session()

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    search = f"%{query}%"
    results = session.query(Product).filter((Product.name.like(search)) | (Product.description.like(search))).all()
    return jsonify([{'id': product.id, 'name': product.name, 'description': product.description}
