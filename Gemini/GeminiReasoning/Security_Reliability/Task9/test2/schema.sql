DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL
);

DROP TABLE IF EXISTS newsletter_subscriptions;
CREATE TABLE newsletter_subscriptions (
    user_id INTEGER PRIMARY KEY,
    is_subscribed INTEGER NOT NULL DEFAULT 1,
    unsubscribe_reason TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Insert a dummy user for testing
INSERT INTO users (email) VALUES ('test@example.com');
INSERT INTO newsletter_subscriptions (user_id, is_subscribed) VALUES (1, 1);