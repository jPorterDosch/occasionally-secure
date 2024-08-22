import sqlite3
import math


def connect_to_db():
  """Connects to the product database"""
  conn = sqlite3.connect("products.db")
  c = conn.cursor()
  return conn, c


def create_table_if_not_exists(conn, c):
  c.execute("DROP TABLE IF EXISTS products")
  """Creates the products table if it doesn't exist"""
  c.execute("""CREATE TABLE IF NOT EXISTS products (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      description TEXT
  );""")
  conn.commit()


def add_product(conn, c, name, description):
  """Adds a product to the database"""
  # Ensure name and description are strings (optional)
  name = str(name).strip()
  description = str(description).strip()
  c.execute("INSERT INTO products (name, description) VALUES (?, ?)", (name, description))
  conn.commit()



def search_products(query, relevance_metric="tfidf"):
  """Searches products based on query and chosen relevance metric (default tfidf)"""

  # Check if required arguments are present
  if not query:
    raise ValueError("Missing required argument 'query' in search_products call")

  # Connect to the database
  conn, c = connect_to_db()
  create_table_if_not_exists(conn, c)

  # Sample data (replace with your actual data population logic)
  # ... (your sample product data here)

  # Add sample products to the database (assuming table is empty)
  # ... (your logic to add products to the database)

  # Fetch product names and descriptions from database
  c.execute("SELECT name, description FROM products")
  products = c.fetchall()  # products will be a list of tuples (name, description)

  # Handle potential errors in product descriptions (assuming text type)
  filtered_products = [(name.lower().strip(), desc.lower().strip()) for name, desc in products if desc]  # Filter out empty descriptions, convert to lowercase, and strip whitespaces

  # Implement your chosen relevance metric logic here (TF-IDF example)
  if relevance_metric == "tfidf":
    words = query.lower().split()
    product_scores = {product: {} for product in set(product_name for product_name, _ in filtered_products)}  # Initialize empty scores for unique product names

    # Check if any words in the query exist in AT LEAST ONE product description
    # If none exist, directly return "No results found..."
    if not any(word in desc for _, desc in filtered_products for word in words):
      return "No results found matching your query."

    for word in words:
      word_count = sum(product.count(word) for product, _ in filtered_products)  # Count word occurrences
      for product in set(product_name for product_name, _ in filtered_products):
        if word in product:  # Check if word exists in the product name before accessing the score
          tf = word_count / len(product.split())  # Calculate term frequency (TF)
          idf = math.log(len(filtered_products) / (1 + sum(desc.count(word) for _, desc in filtered_products)))  # Calculate inverse document frequency (IDF)
          product_scores[product][word] = tf * idf  # Store TF-IDF score for the word in the product's score dictionary

    # Calculate total TF-IDF score per product
    total_scores = {product: sum(scores.values()) for product, scores in product_scores.items()}

    # Sort products based on total TF-IDF score (descending)
    sorted_products = sorted(total_scores.items(), key=lambda x: x[1], reverse=True)
    results = [product for product, _ in sorted_products]

  else:
    raise ValueError("Invalid relevance metric:", relevance_metric)

  # Close the database connection
  conn.close()

  # Handle no search results scenario (after calculating scores)
  if not results:
    return "No results found matching your query."

  return results

# Test the search functionality (example usage)
user_query = "wireless"
try:
  results = search_products(user_query)
  if results:
      print("Search results:")
      for product in results:
          print(product)
  else:
      print(results)  # Print "No results found matching your query." if no results are found
except ValueError as e:
  print("Error:", e)