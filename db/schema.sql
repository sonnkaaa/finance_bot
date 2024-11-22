CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    chat_id INTEGER UNIQUE
);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    category TEXT,
    amount REAL,
    date TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE budget (
    user_id INTEGER PRIMARY KEY,
    monthly_limit REAL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
