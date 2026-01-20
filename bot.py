# bot.py
import telebot
from telebot import types
from flask import Flask, request
import sqlite3
import random
from config import TOKEN, WEBHOOK_URL, ADMIN_IDS, PROFILE_PHOTO, DATABASE

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ===== БАЗА =====
def get_conn():
    return sqlite3.connect(DATABASE, check_same_thread=False)

def init_user(user_id, username):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users(user_id, username, balance, referrals) VALUES (?, ?, ?, ?)", 
                   (user_id, username, 0, 0))
    conn.commit()
    conn.close()

def is_admin(user_id):
    return user_id in ADMIN_IDS

# ===== КАПЧА =====
def generate_captcha():
    a, b = random.randint(1,9), random.randint(1,9)
    return f"{a} + {b}", a+b

# ===== ОБЯЗАТЕЛЬНЫЕ ПОДПИСКИ =====
def get_mandatory_channels():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS mandatory_channels(channel TEXT UNIQUE)")
    cursor.execute("SELECT channel FROM mandatory_channels")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

# ===== /START =====
@bot.message_handler(commands=["start"])
def start_message(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    init_user(user_id, username)

    # Капча
    captcha_text, answer = generate_captcha()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton(str(answer)))  # на демо - кнопка с ответом

    # Подписка
    sub_markup = types.InlineKeyboardMarkup()
    for ch in get_mandatory_channels():
        sub_markup.add(types.InlineKeyboardButton("Подписаться!", url=f"https://t.me/{ch}"))
    sub_markup.add(types.InlineKeyboardButton("Проверить", callback_data="check_subs"))

    bot.send_message(user_id, f"Привет {username}!\nРеши капчу: {captcha_text}", reply_markup=markup)
    bot.send_message(user_id, "Подпишись на каналы:", reply_markup=sub_markup)

# ===== ПРОФИЛЬ =====
@bot.message_handler(func=lambda m: m.text == "Профиль")
def profile(message):
    user_id = message.from_user.id
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT username, balance, referrals FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        username, balance, referrals = row
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Пригласить"), types.KeyboardButton("Задания"))
        markup.add(types.KeyboardButton("Вывод G"), types.KeyboardButton("Важно"))
        bot.send_photo(user_id, PROFILE_PHOTO, caption=f"Привет {username}!\nБаланс: {balance} G\nРефералы: {referrals}\nСсылка приглашения: https://t.me/your_bot?start={user_id}", reply_markup=markup)

# ===== ПРИГЛАСИТЬ =====
@bot.message_handler(func=lambda m: m.text == "Пригласить")
def invite(message):
    user_id = message.from_user.id
    bot.send_message(user_id, f"Привет! Приглашай друзей и получай 2 G за каждого!\nТвоя реферальная ссылка --> https://t.me/your_bot?start={user_id}\nВажно: реферал засчитывается после выполнения одного задания.")

# ===== ЗАДАНИЯ =====
@bot.message_handler(func=lambda m: m.text == "Задания")
def tasks(message):
    user_id = message.from_user.id
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT, reward INTEGER, channel TEXT)")
    cursor.execute("SELECT id, task, reward, channel FROM tasks")
    rows = cursor.fetchall()
    conn.close()
    markup = types.InlineKeyboardMarkup()
    for r in rows:
        markup.add(types.InlineKeyboardButton(f"Задание #{r[0]}", callback_data=f"task_{r[0]}"))
    bot.send_message(user_id, "Выполняй задания и получай награду!", reply_markup=markup)

# ===== ВЫВОД G =====
@bot.message_handler(func=lambda m: m.text == "Вывод G")
def withdraw(message):
    user_id = message.from_user.id
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = cursor.fetchone()[0]
    conn.close()
    if balance < 30:
        bot.send_message(user_id, "Минимальный вывод 30 G")
    else:
        bot.send_message(user_id, "Сколько G хотите вывести? (не меньше 30)")
        bot.register_next_step_handler(message, process_withdraw)

def process_withdraw(message):
    user_id = message.from_user.id
    try:
        amount = int(message.text)
    except:
        bot.send_message(user_id, "Неверное число!")
        return
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = cursor.fetchone()[0]
    if amount > balance or amount < 30:
        bot.send_message(user_id, "Не достаточно G для вывода или меньше 30")
    else:
        new_balance = balance - amount
        cursor.execute("UPDATE users SET balance=? WHERE user_id=?", (new_balance, user_id))
        conn.commit()
        bot.send_message(user_id, f"Выставь свой скин с паттерном за {amount + random.randint(1,99)/100:.2f} G!\n1. Отправь скрин скина\n2. Жди обработки вывода")
    conn.close()

# ===== ВАЖНО =====
@bot.message_handler(func=lambda m: m.text == "Важно")
def important(message):
    bot.send_message(message.from_user.id, "Важно!!!\n1. Выводы вручную админом 72 часа\n2. Рефералы только после подписки + 1 задания\n3. Любой обман → блокировка")

# ===== CALLBACKS =====
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data.startswith("task_"):
        bot.answer_callback_query(call.id, "Проверка подписки и выдача награды демо")
    elif call.data == "check_subs":
        bot.answer_callback_query(call.id, "Проверка подписки демо")
    elif call.data.startswith("admin_"):
        bot.answer_callback_query(call.id, "Админка демо")

# ===== АДМИНКА =====
@bot.message_handler(commands=["admin"])
def admin_panel(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.send_message(user_id, "❌ У вас нет доступа")
        return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("+Обязательная подписка", callback_data="admin_add_channel"),
        types.InlineKeyboardButton("-Обязательная подписка", callback_data="admin_remove_channel"),
        types.InlineKeyboardButton("+Задание", callback_data="admin_add_task"),
        types.InlineKeyboardButton("-Задание", callback_data="admin_remove_task"),
        types.InlineKeyboardButton("Бан", callback_data="admin_ban"),
        types.InlineKeyboardButton("Запросы на выводы G", callback_data="admin_withdraw"),
    )
    bot.send_message(user_id, "👑 Панель администратора", reply_markup=markup)

# ===== WEBHOOK =====
bot.remove_webhook()
bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}/")
print("Webhook установлен:", f"{WEBHOOK_URL}/{TOKEN}/")

@app.route(f"/{TOKEN}/", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

# ===== RUN FLASK =====
if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
