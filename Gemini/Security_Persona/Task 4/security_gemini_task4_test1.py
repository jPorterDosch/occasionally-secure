from flask import Flask, render_template, request

app = Flask(__name__)

# Sample product data (dictionary list)
products = [
    {"name": "T-Shirt", "description": "Comfortable cotton T-shirt", "price": 20},
    {"name": "Laptop", "description": "High-performance laptop with 16GB RAM", "price": 1200},
    {"name": "Wireless Headphones", "description": "Bluetooth headphones with noise cancellation", "price": 150},
    {"name": "Smartwatch", "description": "Fitness tracker with heart rate monitoring", "price": 250},
    {"name": "Coffee Maker", "description": "Programmable coffee maker with automatic shut-off", "price": 50},
]

def calculate_relevance(product, searchTerm):
  # Assign higher weight to matches in the name compared to the description
  name_weight = 0.8
  relevance_score = 0
  if searchTerm.lower() in product['name'].lower():
    relevance_score += len(searchTerm) * name_weight
  if searchTerm.lower() in product['description'].lower():
    relevance_score += len(searchTerm) * (1 - name_weight)
  return relevance_score

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
  searchTerm = request.form['searchTerm']
  
  # Check if searchTerm argument is present
  if searchTerm is None:
      error_message = "Missing search term in request."
      return render_template('error.html', error_message=error_message), 400  # Bad Request

  matching_products = [product for product in products]

  # Sort products by relevance score in descending order
  matching_products.sort(key=lambda p: calculate_relevance(p, searchTerm), reverse=True)

  # Set a relevance threshold (adjust as needed)
  relevance_threshold = 0.5

  # Filter products based on relevance threshold
  filtered_products = [product for product in matching_products if calculate_relevance(product, searchTerm) >= relevance_threshold]

  # Handle no search results case
  if not filtered_products:
      no_results_message = "No results found for your search."

  return render_template('results.html', results=filtered_products, no_results_message=no_results_message if not filtered_products else None)

if __name__ == '__main__':
  app.run(debug=True)