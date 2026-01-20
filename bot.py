import telebot
from telebot import types
from flask import Flask, request
import sqlite3
import os
import random
from config import TOKEN, WEBHOOK_URL, ADMIN_IDS, PROFILE_PHOTO, DATABASE

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ================= DATABASE =================
def db():
    return sqlite3.connect(DATABASE, check_same_thread=False)

def init_db():
    c = db().cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 0,
        referrals INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS mandatory (
        channel TEXT UNIQUE
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT,
        reward INTEGER
    )""")
    db().commit()

init_db()

# ================= HELPERS =================
def is_admin(uid):
    return uid in ADMIN_IDS

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Профиль", "Пригласить")
    kb.add("Задания", "Вывод G")
    kb.add("Важно")
    return kb

# ================= /START =================
@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    c = db().cursor()
    c.execute("INSERT OR IGNORE INTO users(user_id, username) VALUES (?,?)", (uid, username))
    db().commit()

    bot.send_message(
        uid,
        "Привет! Что-бы пользоваться ботом нужно 👇",
        reply_markup=main_menu()
    )

# ================= PROFILE =================
@bot.message_handler(func=lambda m: m.text == "Профиль")
def profile(m):
    uid = m.from_user.id
    c = db().cursor()
    c.execute("SELECT balance, referrals FROM users WHERE user_id=?", (uid,))
    bal, refs = c.fetchone()

    bot.send_photo(
        uid,
        PROFILE_PHOTO,
        caption=(
            f"Привет {m.from_user.username}!\n\n"
            f"Баланс: {bal} G\n"
            f"Рефералы: {refs}\n\n"
            f"Ссылка:\nhttps://t.me/{bot.get_me().username}?start={uid}"
        ),
        reply_markup=main_menu()
    )

# ================= INVITE =================
@bot.message_handler(func=lambda m: m.text == "Пригласить")
def invite(m):
    uid = m.from_user.id
    bot.send_message(
        uid,
        f"Приглашай друзей и получай 2 G!\n\n"
        f"https://t.me/{bot.get_me().username}?start={uid}\n\n"
        f"Реферал засчитывается после выполнения задания."
    )

# ================= TASKS =================
@bot.message_handler(func=lambda m: m.text == "Задания")
def tasks(m):
    c = db().cursor()
    c.execute("SELECT id, reward FROM tasks")
    rows = c.fetchall()

    kb = types.InlineKeyboardMarkup()
    for i, r in rows:
        kb.add(types.InlineKeyboardButton(f"Задание #{i}", callback_data=f"task_{i}"))

    bot.send_message(m.chat.id, "Выполняй задания:", reply_markup=kb)

# ================= WITHDRAW =================
@bot.message_handler(func=lambda m: m.text == "Вывод G")
def withdraw(m):
    uid = m.from_user.id
    c = db().cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    bal = c.fetchone()[0]

    if bal < 30:
        bot.send_message(uid, "Минимальный вывод 30 G")
    else:
        bot.send_message(uid, "Отправь сумму для вывода (не меньше 30 G)")

# ================= IMPORTANT =================
@bot.message_handler(func=lambda m: m.text == "Важно")
def info(m):
    bot.send_message(
        m.chat.id,
        "Важно!!!\n"
        "1. Выводы до 72 часов\n"
        "2. Рефералы после задания\n"
        "3. Обман = бан"
    )

# ================= ADMIN =================
@bot.message_handler(commands=["admin"])
def admin(m):
    if not is_admin(m.from_user.id):
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("+Задание", callback_data="add_task"))
    kb.add(types.InlineKeyboardButton("-Задание", callback_data="del_task"))

    bot.send_message(m.chat.id, "👑 Админ панель", reply_markup=kb)

# ================= WEBHOOK =================
bot.remove_webhook()
bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
