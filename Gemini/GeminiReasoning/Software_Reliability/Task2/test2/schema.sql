DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS carts;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    -- Add other user information as needed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE carts (
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (product_id) REFERENCES products (id),
    PRIMARY KEY (user_id, product_id) -- Ensure a user can't have the same product multiple times in the cart
);

-- Insert some sample data for testing
INSERT INTO users (username) VALUES ('user1');
INSERT INTO users (username) VALUES ('user2');

INSERT INTO products (name, description, price, stock) VALUES ('Awesome T-Shirt', 'A comfortable and stylish t-shirt.', 25.99, 100);
INSERT INTO products (name, description, price, stock) VALUES ('Cool Mug', 'A ceramic mug for your favorite beverages.', 12.50, 50);
INSERT INTO products (name, description, price, stock) VALUES ('Fancy Notebook', 'A high-quality notebook for your ideas.', 18.75, 75);
INSERT INTO products (name, description, price, stock) VALUES ('Out of Stock Item', 'This item is currently out of stock.', 9.99, 0);