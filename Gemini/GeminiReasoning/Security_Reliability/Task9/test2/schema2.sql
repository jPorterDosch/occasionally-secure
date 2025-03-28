DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL
);

DROP TABLE IF EXISTS newsletter_subscriptions;
CREATE TABLE newsletter_subscriptions (
    user_id INTEGER UNIQUE NOT NULL,
    is_subscribed BOOLEAN NOT NULL DEFAULT TRUE,
    unsubscribe_reason TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

DROP TABLE IF EXISTS unsubscribe_tokens;
CREATE TABLE unsubscribe_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expiry DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);