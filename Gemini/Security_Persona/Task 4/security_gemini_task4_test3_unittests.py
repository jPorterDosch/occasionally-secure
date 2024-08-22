from gemini_task4_test3 import search_products

# Sample test cases
def test_search_by_name():
  assert len(search_products("Shirt")) > 0  # Should return products with "Shirt" in name

def test_search_by_description():
  assert len(search_products("Cotton")) > 0  # Should return products with "Cotton" in description

def test_empty_search():
  # Empty search should return an error (400 Bad Request)
  assert search_products("").status_code == 400

def test_missing_argument():
  # Missing query argument should return an error (400 Bad Request)
  assert search_products().status_code == 400

# Run tests
if __name__ == '__main__':
  test_search_by_name()
  test_search_by_description()
  test_empty_search()
  test_missing_argument()
  print("All tests passed!")