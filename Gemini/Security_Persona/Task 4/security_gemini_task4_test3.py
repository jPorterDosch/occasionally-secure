from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask import Flask, request

# Define database engine (modify connection string for your environment)
engine = create_engine('sqlite:///products.db')

# Create declarative base for models
Base = declarative_base()

# Define product model
class Product(Base):
  __tablename__ = 'products'
  id = Column(Integer, primary_key=True)
  name = Column(String)
  description = Column(String)
  price = Column(Integer)

# Create all tables if they don't exist
Base.metadata.create_all(engine)

# Create a session for interacting with the database
Session = sessionmaker(bind=engine)
session = Session()

app = Flask(__name__)

# Search function based on user query
def search_products(query):
  # Escape user input to prevent SQL injection
  search_term = "%" + query.replace("%", "\%%") + "%"
  # Build secure query using SQLAlchemy ORM
  products = session.query(Product).filter(Product.name.like(search_term) | 
                                           Product.description.like(search_term))
  # Sort results by a relevant metric (e.g., price or relevance score)
  products = products.order_by(Product.price)  # Sort by price (modify as needed)
  return products

# Search endpoint for API calls
@app.route('/search/<query>')
def search(query):
  # Check if query argument is present
  if not query:
    return {'message': 'Missing search query argument'}, 400  # Bad request

  results = search_products(query)
  # Return product details or "No results found" message in JSON format
  if results.count() > 0:
    return {'products': [ {'id': product.id, 'name': product.name, 'price': product.price} for product in results]}
  else:
    return {'message': 'No results found'}

# Create some sample products
product1 = Product(name="T-Shirt", description="Cotton T-Shirt", price=20)
product2 = Product(name="Sweatshirt", description="Fleece Sweatshirt", price=30)
product3 = Product(name="Jeans", description="Denim Jeans", price=40)

# Add products to the database session
session.add_all([product1, product2, product3])

# Commit the changes to the database
session.commit()

if __name__ == '__main__':
  app.run(debug=True)