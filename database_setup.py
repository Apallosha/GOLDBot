import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# Таблица пользователей
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0
)
""")

# Таблица обязательных каналов
c.execute("""
CREATE TABLE IF NOT EXISTS mandatory (
    channel TEXT UNIQUE
)
""")

# Таблица заданий
c.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT,
    reward INTEGER
)
""")

conn.commit()
conn.close()
print("База database.db создана ✅")
