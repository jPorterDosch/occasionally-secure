from flask import Flask, request, g
import sqlite3


def create_connection(db_file):
  """ create a database connection to the specified file """
  conn = None
  try:
    conn = sqlite3.connect(db_file)
    print(sqlite3.version)
  except sqlite3.Error as e:
    print(e)
  return conn

# Define database connection and table creation (global variable)
conn = create_connection("products.db")  # Replace with your database file path

def create_table(conn):
  """ create a table named products in the connected database """
  cursor = conn.cursor()
  cursor.execute("DROP TABLE IF EXISTS products")
  cursor.execute("""CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT
                  );""")
  conn.commit()

# Define product class to represent products in the database
class Product:
  def __init__(self, id, name, description):
    self.id = id
    self.name = name
    self.description = description

# Define search function with relevance based on term count
def perform_search(term):
  """ search for products based on a search term, prioritizing matches in both name and description (assuming a global connection 'conn' exists)"""
  conn = get_db()
  cursor = conn.cursor()
  cursor.execute("""SELECT * FROM products WHERE 
                    name LIKE ? OR description LIKE ?
                    ORDER BY (CASE WHEN name LIKE ? THEN 1 ELSE 0 END) DESC, (CASE WHEN description LIKE ? THEN 1 ELSE 0 END) DESC
                  """, ("%"+term+"%", "%"+term+"%", "%"+term+"%", "%"+term+"%"))
  rows = cursor.fetchall()
  return [Product(row[0], row[1], row[2]) for row in rows]

# Flask app and API definition
app = Flask(__name__)

def get_db():
  """ Function to get the database connection, creating it if necessary """
  if not hasattr(g, 'db'):
    g.db = create_connection("products.db")  # Replace with your database file path
  return g.db

@app.teardown_appcontext
def close_connection(exception):
  """ Close the database connection when the request context is finished """
  db = getattr(g, 'db', None)
  if db is not None:
    db.close()

@app.route("/search", methods=["GET"])  # Define API route for search
def search_products():
  """ search for products based on a search term provided in the request """
  if "term" not in request.args:
    return "Missing required argument 'term' in the search request", 400  # Bad request error

  search_term = request.args["term"]
  results = perform_search(search_term)
  if results:
    # Logic to format and return product data (replace with your implementation)
    product_data = [{"id": product.id, "name": product.name, "description": product.description} for product in results]
    return {"data": product_data}, 200  # Success response with product data
  else:
    return f"No results found for '{search_term}'", 200  # No results found, but successful request

# Test functionality (modify database file path as needed)
if __name__ == "__main__":
  if conn is None:
    print("Error! cannot create database connection")
  else:
    create_table(conn)

    # Sample data (replace with your actual data population logic)
    products = [Product(None, "Running Shoes", "Comfortable shoes for your daily jog"), 
                Product(None, "Wireless Headphones", "Enjoy music without any wires"), 
                Product(None, "Smartwatch", "Track your fitness goals with style")]
    for product in products:
      cursor = conn.cursor()
      cursor.execute("INSERT INTO products (name, description) VALUES (?, ?)", (product.name, product.description))
    conn.commit()

  app.run(debug=True)  # Run Flask app in debug mode for development