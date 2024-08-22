from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords

def calculate_relevance(product, search_term):
  # Create a TF-IDF vectorizer
  vectorizer = TfidfVectorizer(stop_words=stopwords.words('english'))  # Remove stopwords

  # Prepare documents (cleaned product details and search term)
  cleaned_product_text = f"{product.name.lower()} {product.description.lower()}"  # Combine and lowercase
  documents = [cleaned_product_text, search_term.lower()]  # Lowercase search term

  # Fit the vectorizer to the documents
  vectorizer.fit_transform(documents)

  # Get TF-IDF scores for the search term
  tfidf_scores = vectorizer.idf_

  # Calculate relevance score (improved example)
  score = 0
  for word in search_term.split():
    if word in tfidf_scores:
      score += tfidf_scores[word]

  # Consider additional factors for relevance (optional)
  # - Title match bonus (if search term appears in product name)
  # - Exact phrase match bonus
  # - ... (tailor these based on your needs)

  # Use serialize_product function to get product data
  product_data = serialize_product(product)

  return score, product_data  # Return both score and product data

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'  # Replace with your connection string
db = SQLAlchemy(app)

# Define product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)

# Secure search function using ORM query
@app.route('/search', methods=['POST'])
def search_products():
    search_term = request.json.get('term')
    if search_term:
        # Escape user input (already done when using ORM)
        query = Product.query.filter(
            or_(Product.name.like('%' + search_term + '%'), Product.description.like('%' + search_term + '%'))
        )
        results = query.all()  # Fetch all matching products

        # Handle case with no search results
        if not results:
            return jsonify({'message': 'No results found for your search term.'}), 404

        # Calculate relevance scores and product data for each product (if results found)
        relevance_scores, product_data_list = zip(*[calculate_relevance(product) for product in results])

        # Combine products and scores into a list of dictionaries
        search_results = [
            {'product': product_data, 'relevance_score': score}
            for product_data, score in zip(product_data_list, relevance_scores)
        ]

        # Sort results by relevance score (descending order)
        search_results.sort(key=lambda x: x['relevance_score'], reverse=True)

        # Return only top N results (adjust N as needed)
        top_results = search_results[:10]  # Return top 10 by default
        return jsonify({'products': top_results})
    else:
        return jsonify({'error': 'Search term required'}), 400

# Helper method to serialize product objects (optional)
def serialize_product(product):
    return {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
    }


# Insert sample data (modify as needed)
with app.app_context():
    db.drop_all()
    db.create_all()  # Create tables if they don't exist
    sample_data = [
        ("Red Running Shoes", "Comfortable running shoes for all terrains", 79.99),
        ("Blue Basketball", "High-performance basketball for competitive games", 59.99),
        ("Wireless Headphones", "High-quality wireless headphones with long battery life", 149.99),
        ("Black Backpack", "Spacious backpack for everyday use", 49.99),
        ("White T-Shirt", "Basic white t-shirt in various sizes", 14.99),
    ]
    for name, description, price in sample_data:
        product = Product(name=name, description=description, price=price)
        db.session.add(product)
    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)