from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configure database connection (replace with your details)
engine = create_engine('sqlite:///products.db')  # In-memory database by default
Base = declarative_base()

# Define product model
class Product(Base):
  __tablename__ = 'products'
  id = Column(Integer, primary_key=True)
  name = Column(String(255))
  description = Column(Text)

  @staticmethod
  def insert_sample_data(session):
    products = [
        {"name": "Red Baseball Hat", "description": "A classic red baseball hat"},
        {"name": "Blue T-Shirt", "description": "A comfortable blue t-shirt"},
        {"name": "Winter Gloves", "description": "Warm gloves for winter weather"},
    ]
    for product in products:
      new_product = Product(name=product["name"], description=product["description"])
      session.add(new_product)
    session.commit()
    print("Sample data inserted!")  # Print confirmation for testing

# Create database tables (one-time setup)
Base.metadata.create_all(engine)

# Initialize Flask app
app = Flask(__name__)

# Create database session (important for queries)
Session = sessionmaker(bind=engine)
session = Session()

# Search function (metric: prioritize exact matches)
def search_products(term):
  # Access query method from the session object
  results = session.query(Product).filter(
      Product.name.ilike("%" + term + "%") | Product.description.ilike("%" + term + "%")
  ).order_by(Product.name.like(term)).all()  # Prioritize exact matches in name
  return results

# Search API endpoint
@app.route('/api/search', methods=['GET'])
def search():
  term = request.args.get('term')
  if not term:
    return jsonify({'error': 'Missing search term'}), 400
  products = search_products(term)
  if not products:
    return jsonify({'message': 'No results found'})
  return jsonify({'products': [p.serialize() for p in products]})

# Product serialization for JSON response
def serialize(self):
  return {
      'id': self.id,
      'name': self.name,
      'description': self.description
  }

# Add serialize method to Product class
Product.serialize = serialize

# Run the Flask app (for manual testing)
if __name__ == '__main__':
  # Insert sample data during app launch (optional)
  # Product.insert_sample_data(session)  # Uncomment for automatic sample data

  app.run(debug=True)