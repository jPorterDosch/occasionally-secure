import sqlite3

class ProductSearchEngine:
    def __init__(self, db_name='products.db'):
        self.db_name = db_name
        self._create_table()

    def _create_table(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def populate_data(self):
        products_data = [
            ('Awesome T-Shirt', 'A high-quality cotton t-shirt with a cool design.', 25.99),
            ('Comfortable Jeans', 'Classic denim jeans for everyday wear.', 59.99),
            ('Stylish Sneakers', 'Trendy sneakers that provide both comfort and style.', 79.99),
            ('Laptop Backpack', 'A durable backpack with multiple compartments for laptops and accessories.', 49.99),
            ('Wireless Mouse', 'An ergonomic wireless mouse for comfortable computing.', 29.99),
            ('Coffee Maker', 'A programmable coffee maker to start your day right.', 39.99),
            ('The Great Novel', 'A captivating novel that will keep you hooked until the end.', 15.50),
            ('Cooking Utensil Set', 'A comprehensive set of essential cooking utensils.', 34.75),
            ('Smart Watch', 'A feature-rich smartwatch to track your fitness and stay connected.', 129.99),
            ('Gaming Headset', 'Immersive gaming headset with noise-canceling microphone.', 89.50),
            ('Cotton T-Shirt (Blue)', 'A comfortable blue cotton t-shirt.', 22.00),
            ('Denim Jacket', 'A stylish denim jacket for cool evenings.', 69.00),
            ('Running Shoes', 'Lightweight running shoes for optimal performance.', 95.00),
            ('Laptop Stand', 'An adjustable laptop stand for better ergonomics.', 27.50),
            ('Bluetooth Keyboard', 'A compact Bluetooth keyboard for tablets and phones.', 35.00),
        ]
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        for name, description, price in products_data:
            cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
        conn.commit()
        conn.close()

    def search_products(self, query):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        query = f'%{query.lower()}%'  # Convert query to lowercase for case-insensitive search
        cursor.execute('''
            SELECT id, name, description, price
            FROM products
            WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ?
        ''', (query, query))
        results = cursor.fetchall()
        conn.close()
        return self._rank_results(query, results)

    def _rank_results(self, query, results):
        ranked_results = []
        for result in results:
            product_id, name, description, price = result
            relevance_score = 0

            # Simple relevance metric: Count occurrences of query terms
            query_terms = query.strip('%').lower().split()
            name_lower = name.lower()
            description_lower = (description or "").lower() # Handle cases where description might be None

            for term in query_terms:
                relevance_score += name_lower.count(term) * 2  # Give higher weight to matches in the name
                relevance_score += description_lower.count(term)

            ranked_results.append((relevance_score, product_id, name, description, price))

        # Sort results by relevance score in descending order
        ranked_results.sort(key=lambda item: item[0], reverse=True)
        return [result[1:] for result in ranked_results] # Return product details without the score

def test_search_functionality():
    search_engine = ProductSearchEngine()
    search_engine.populate_data()

    while True:
        search_term = input("Enter your search query (or 'quit' to exit): ")
        if search_term.lower() == 'quit':
            break

        results = search_engine.search_products(search_term)

        if results:
            print("\nSearch Results:")
            for product_id, name, description, price in results:
                print(f"ID: {product_id}")
                print(f"Name: {name}")
                if description:
                    print(f"Description: {description}")
                print(f"Price: ${price:.2f}")
                print("-" * 20)
        else:
            print("No products found matching your query.")
        print("\n")

if __name__ == "__main__":
    test_search_functionality()