import telebot
from telebot import types
from flask import Flask, request
import sqlite3, random, os
from config import TOKEN, WEBHOOK_URL, ADMIN_IDS, PROFILE_PHOTO, DATABASE

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ================= DATABASE =================
def conn():
    return sqlite3.connect(DATABASE, check_same_thread=False)

def init_db():
    c = conn().cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 0,
        referrals INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS mandatory (channel TEXT UNIQUE)""")
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT,
        reward INTEGER
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS withdrawals (
        user_id INTEGER,
        amount INTEGER,
        status TEXT
    )""")
    conn().commit()

init_db()

# ================= HELPERS =================
def is_admin(uid):
    return uid in ADMIN_IDS

def main_menu(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Профиль", "Пригласить")
    kb.add("Задания", "Вывод G")
    kb.add("Важно")
    if is_admin(uid):
        kb.add("👑 Админка")
    return kb

# ================= START =================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    c = conn().cursor()
    c.execute("INSERT OR IGNORE INTO users(user_id, username) VALUES (?,?)", (uid, username))
    conn().commit()
    bot.send_message(uid, "Привет! Что-бы пользоваться ботом нужно 👇", reply_markup=main_menu(uid))

# ================= PROFILE =================
@bot.message_handler(func=lambda m: m.text == "Профиль")
def profile(m):
    uid = m.from_user.id
    c = conn().cursor()
    c.execute("SELECT balance, referrals FROM users WHERE user_id=?", (uid,))
    bal, refs = c.fetchone()
    bot.send_photo(
        uid,
        PROFILE_PHOTO,
        caption=f"Привет {m.from_user.username}!\nБаланс: {bal} G\nРефералы: {refs}\nСсылка: https://t.me/{bot.get_me().username}?start={uid}",
        reply_markup=main_menu(uid)
    )

# ================= INVITE =================
@bot.message_handler(func=lambda m: m.text == "Пригласить")
def invite(m):
    uid = m.from_user.id
    bot.send_message(
        uid,
        f"Приглашай друзей и получай 2 G!\nСсылка: https://t.me/{bot.get_me().username}?start={uid}\nРеферал засчитывается после задания."
    )

# ================= TASKS =================
@bot.message_handler(func=lambda m: m.text == "Задания")
def tasks(m):
    c = conn().cursor()
    c.execute("SELECT id, channel, reward FROM tasks")
    rows = c.fetchall()
    kb = types.InlineKeyboardMarkup()
    for i, ch, r in rows:
        kb.add(types.InlineKeyboardButton(f"Задание #{i}", callback_data=f"task_{i}"))
    bot.send_message(m.chat.id, "Выполняй задания!", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("task_"))
def task_click(call):
    task_id = int(call.data.split("_")[1])
    c = conn().cursor()
    c.execute("SELECT channel, reward FROM tasks WHERE id=?", (task_id,))
    row = c.fetchone()
    if not row:
        bot.answer_callback_query(call.id, "Задание не найдено")
        return
    channel, reward = row
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Подписаться", url=f"https://t.me/{channel}"))
    kb.add(types.InlineKeyboardButton("Проверить", callback_data=f"checktask_{task_id}"))
    bot.send_message(call.message.chat.id, f"Подпишись на @{channel}\nНаграда: {reward} G", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("checktask_"))
def task_reward(call):
    task_id = int(call.data.split("_")[1])
    uid = call.from_user.id
    c = conn().cursor()
    c.execute("SELECT reward FROM tasks WHERE id=?", (task_id,))
    reward = c.fetchone()[0]
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (reward, uid))
    conn().commit()
    bot.answer_callback_query(call.id, f"+{reward} G начислено")

# ================= WITHDRAW =================
@bot.message_handler(func=lambda m: m.text == "Вывод G")
def withdraw(m):
    uid = m.from_user.id
    c = conn().cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    bal = c.fetchone()[0]
    if bal < 30:
        bot.send_message(uid, "Минимальный вывод 30 G")
    else:
        bot.send_message(uid, "Отправь сумму для вывода (не меньше 30 G)")
        bot.register_next_step_handler(m, process_withdraw)

def process_withdraw(m):
    uid = m.from_user.id
    try:
        amount = int(m.text)
    except:
        bot.send_message(uid, "Нужно число")
        return
    c = conn().cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    bal = c.fetchone()[0]
    if amount < 30 or amount > bal:
        bot.send_message(uid, "Недостаточно G")
        return
    price = amount + random.randint(1, 99)/100
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, uid))
    c.execute("INSERT INTO withdrawals VALUES (?,?,?)", (uid, amount, "wait"))
    conn().commit()
    bot.send_message(uid, f"Выставь скин за {price:.2f} G\n1. Выставь скин\n2. Отправь скрин\n3. Ожидай вывод")

# ================= IMPORTANT =================
@bot.message_handler(func=lambda m: m.text == "Важно")
def important(m):
    bot.send_message(m.chat.id, "Важно!!!\n1. Выводы до 72 часов\n2. Рефералы после задания\n3. Обман = бан")

# ================= ADMIN =================
@bot.message_handler(func=lambda m: m.text == "👑 Админка")
def admin(m):
    if not is_admin(m.from_user.id):
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("+Задание", callback_data="add_task"))
    kb.add(types.InlineKeyboardButton("Запросы на вывод", callback_data="admin_withdraws"))
    bot.send_message(m.chat.id, "👑 Админ панель", reply_markup=kb)

# ================= WEBHOOK =================
bot.remove_webhook()
bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
