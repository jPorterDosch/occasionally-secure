DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT 0
);
INSERT INTO users (username, password, is_admin) VALUES ('admin', 'admin_password', 1);
INSERT INTO users (username, password, is_admin) VALUES ('user', 'user_password', 0);

DROP TABLE IF EXISTS products;
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL
);
INSERT INTO products (name, description, price) VALUES ('Example Product 1', 'This is the first example product.', 25.99);
INSERT INTO products (name, description, price) VALUES ('Example Product 2', 'Another great product.', 49.50);