import sqlite3

# Путь к базе данных
DB_PATH = "db/finance.db"

def create_database():
    """Создаёт файл базы данных и необходимые таблицы."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Создаём таблицу пользователей
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            chat_id INTEGER UNIQUE
        );
        """)

        # Создаём таблицу расходов
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            amount REAL,
            date TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)

        # Создаём таблицу бюджета
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            user_id INTEGER PRIMARY KEY,
            monthly_limit REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)

        print("База данных и таблицы успешно созданы!")

if __name__ == "__main__":
    create_database()
