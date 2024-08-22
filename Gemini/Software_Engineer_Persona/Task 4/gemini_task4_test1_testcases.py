from gemini_task4_test1 import Product, engine, search_products  # Import from your main app file
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create a new session for testing
session = sessionmaker(bind=engine)()

# Clear existing data (optional)
# Product.query.delete()  # Assuming this is intended (clear before inserting sample data)
# session.commit()

# Insert sample data (ensures data for tests)
Product.insert_sample_data(session)

def test_search():
  products = search_products("hat")  # Only pass the search term
  assert len(products) > 0  # Assert some results found
  assert products[0].name == "Red Baseball Hat"  # Assert prioritized exact match

  products = search_products("xyz")  # Test no results case
  assert not products  # Assert empty list

# Run tests (replace with your testing framework)
if __name__ == '__main__':
  test_search()