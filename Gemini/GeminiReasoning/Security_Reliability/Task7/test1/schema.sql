DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

DROP TABLE IF EXISTS sessions;
CREATE TABLE sessions (
    session_id TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    expiry_time DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);