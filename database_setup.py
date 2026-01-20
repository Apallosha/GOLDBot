import sqlite3
from config import DATABASE

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0,
    referrer INTEGER,
    ref_rewarded INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS mandatory_channels(
    channel TEXT PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT,
    reward INTEGER,
    description TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS completed_tasks(
    user_id INTEGER,
    task_id INTEGER,
    PRIMARY KEY(user_id, task_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS withdraw_requests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    screenshot TEXT
)
""")

conn.commit()
conn.close()
print("✅ Все таблицы созданы!")
