import telebot, random, sqlite3
from flask import Flask, request
from config import *
from keyboards import *

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)
conn = sqlite3.connect(DATABASE, check_same_thread=False)
cursor = conn.cursor()
USER_STATE = {}

# ===== ФУНКЦИИ =====
def is_admin(uid):
    return uid in ADMIN_IDS

def get_user(uid):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return cursor.fetchone()

def show_main_menu(uid):
    bot.send_message(uid, "✅ Доступ открыт! Выберите действие ниже:", reply_markup=main_menu_kb())

def check_sub(uid, channel):
    try:
        member = bot.get_chat_member(channel, uid)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def all_mandatory_done(uid):
    cursor.execute("SELECT channel FROM mandatory_channels")
    for (ch,) in cursor.fetchall():
        if not check_sub(uid, ch):
            return False
    return True

# ===== START + КАПЧА =====
@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.from_user.id
    args = msg.text.split()
    ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    if not get_user(uid):
        cursor.execute("INSERT INTO users (user_id, username, referrer) VALUES (?,?,?)",
                       (uid, msg.from_user.username, ref))
        conn.commit()

    a, b = random.randint(1, 9), random.randint(1, 9)
    USER_STATE[uid] = {"step": "captcha", "answer": a+b}
    bot.send_message(uid, f"Привет! Чтобы пользоваться ботом нужно 👇\nРеши капчу: <b>{a} + {b}</b>")

@bot.message_handler(func=lambda m: USER_STATE.get(m.from_user.id, {}).get("step") == "captcha")
def captcha_check(msg):
    uid = msg.from_user.id
    if not msg.text.isdigit() or int(msg.text) != USER_STATE[uid]["answer"]:
        bot.send_message(uid, "❌ Неверно, попробуй ещё раз")
        return
    USER_STATE.pop(uid)
    cursor.execute("SELECT channel FROM mandatory_channels")
    channels = [i[0] for i in cursor.fetchall()]
    if channels:
        bot.send_message(uid, "Подпишись на все каналы ниже 👇", reply_markup=mandatory_subscribe_kb(channels))
    else:
        show_main_menu(uid)

# ===== ПРОВЕРКА ПОДПИСКИ =====
@bot.callback_query_handler(func=lambda c: c.data == "check_mandatory_sub")
def check_mandatory(c):
    uid = c.from_user.id
    if not all_mandatory_done(uid):
        bot.answer_callback_query(c.id, "❌ Вы не подписались на все каналы ❌", show_alert=True)
        return
    bot.send_message(uid, "✅ Доступ открыт!")
    show_main_menu(uid)

# ===== МЕНЮ =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("menu_"))
def menu(c):
    uid = c.from_user.id
    user = get_user(uid)

    if c.data == "menu_profile":
        username = c.from_user.username or c.from_user.first_name
        cursor.execute("SELECT COUNT(*) FROM users WHERE referrer=?", (uid,))
        refs = cursor.fetchone()[0]
        bot.send_photo(uid, PROFILE_PHOTO, caption=(
            f"👤 Привет, <b>{username}</b>! Вот твоя информация:\n\n"
            f"💎 Баланс — <b>{user[2]} G</b>\n"
            f"👥 Ваши рефералы — <b>{refs}</b>\n\n"
            f"🔗 Ссылка приглашения:\nhttps://t.me/{BOT_USERNAME}?start={uid}"
        ))
    elif c.data == "menu_invite":
        bot.send_message(uid, f"Привет! Приглашай друзей и получай 2 G за каждого.\n"
                              f"❗ Реферал засчитывается после выполнения задания\n"
                              f"Твоя реферальная ссылка:\nhttps://t.me/{BOT_USERNAME}?start={uid}")
    elif c.data == "menu_info":
        bot.send_message(uid,
        "⚠️ <b>Важно!!!</b>\n"
        "1. Выводы проводятся вручную администратором в течение 72 часов.\n"
        "2. Рефералы засчитываются только после подписки на обязательные каналы и выполнения любого одного задания.\n"
        "3. Любой обман, накрутка или другие нечестные действия приводят к блокировке вашего аккаунта!")
    elif c.data == "menu_tasks":
        cursor.execute("SELECT * FROM tasks")
        tasks = cursor.fetchall()
        if not tasks:
            bot.send_message(uid, "❌ Заданий пока нет")
            return
        bot.send_message(uid, "Привет! Выполняй задания и получай награду!", reply_markup=tasks_list_kb(tasks))
    elif c.data == "menu_withdraw":
        if user[2] < MIN_WITHDRAW:
            bot.send_message(uid, f"Минимальный вывод {MIN_WITHDRAW} G")
            return
        USER_STATE[uid] = {"step": "withdraw_amount"}
        bot.send_message(uid, "Отправь сколько хочешь вывести G (не меньше 30)")

# ===== ЗАДАНИЯ =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("task_"))
def task_callbacks(c):
    uid = c.from_user.id
    if c.data.startswith("task_open:"):
        task_id = int(c.data.split(":")[1])
        cursor.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        task = cursor.fetchone()
        cursor.execute("SELECT 1 FROM completed_tasks WHERE user_id=? AND task_id=?", (uid, task_id))
        if cursor.fetchone():
            bot.answer_callback_query(c.id, "❌ Задание уже выполнено", show_alert=True)
            return
        bot.send_message(uid, f"{task[3]}\nНаграда: <b>{task[2]} G</b>", reply_markup=task_check_kb(task_id))
    elif c.data.startswith("task_check:"):
        task_id = int(c.data.split(":")[1])
        cursor.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        task = cursor.fetchone()
        if not check_sub(uid, task[1]):
            bot.answer_callback_query(c.id, "❌ Вы не подписались", show_alert=True)
            return
        cursor.execute("INSERT OR IGNORE INTO completed_tasks VALUES (?,?)", (uid, task_id))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (task[2], uid))
        cursor.execute("SELECT referrer, ref_rewarded FROM users WHERE user_id=?", (uid,))
        ref, rewarded = cursor.fetchone()
        if ref and rewarded == 0:
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (REF_BONUS, ref))
            cursor.execute("UPDATE users SET ref_rewarded = 1 WHERE user_id=?", (uid,))
        conn.commit()
        bot.send_message(uid, f"✅ Задание выполнено! +{task[2]} G")

# ===== ВЫВОД G =====
@bot.message_handler(func=lambda m: USER_STATE.get(m.from_user.id, {}).get("step") == "withdraw_amount")
def withdraw_amount(msg):
    uid = msg.from_user.id
    if not msg.text.isdigit():
        bot.send_message(uid, "Отправь число")
        return
    amount = int(msg.text)
    user = get_user(uid)
    if amount < MIN_WITHDRAW or amount > user[2]:
        bot.send_message(uid, "❌ Недостаточно G для вывода")
        return
    price = round(amount + random.uniform(0.01, 0.99), 2)
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, uid))
    conn.commit()
    USER_STATE[uid] = {"step": "withdraw_screen", "amount": price}
    bot.send_message(uid, f"Выставь свой скин с паттерном за <b>{price} G</b>!")
    bot.send_message(uid, "1. Выставь скин за указанную цену\n2. Отправь скриншот\n3. Ожидай вывод")

@bot.message_handler(content_types=["photo"], func=lambda m: USER_STATE.get(m.from_user.id, {}).get("step") == "withdraw_screen")
def withdraw_screen(msg):
    uid = msg.from_user.id
    price = USER_STATE[uid]["amount"]
    cursor.execute("INSERT INTO withdraw_requests (user_id, amount, screenshot) VALUES (?,?,?)",
                   (uid, price, msg.photo[-1].file_id))
    conn.commit()
    USER_STATE.pop(uid)
    bot.send_message(uid, "✅ Запрос на вывод отправлен!")

# ===== АДМИНКА =====
@bot.message_handler(commands=["admin"])
def admin(msg):
    uid = msg.from_user.id
    if not is_admin(uid):
        bot.send_message(uid, "❌ Это доступно только администратору")
        return
    bot.send_message(uid, "🛠 <b>Админ панель</b>", reply_markup=admin_menu_kb())
    USER_STATE[uid] = {"step": "admin"}

# ===== CALLBACK АДМИНКИ =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_") or c.data.startswith("withdraw_"))
def admin_callbacks(c):
    uid = c.from_user.id
    if not is_admin(uid):
        return

    data = c.data
    # + Обязательная подписка
    if data == "admin_add_mandatory":
        USER_STATE[uid]["step"] = "add_mandatory"
        bot.send_message(uid, "Пришли @канал для добавления в обязательные подписки")
    elif data == "admin_del_mandatory":
        USER_STATE[uid]["step"] = "del_mandatory"
        bot.send_message(uid, "Пришли @канал для удаления из обязательных подписок")
    elif data == "admin_add_task":
        USER_STATE[uid]["step"] = "add_task"
        bot.send_message(uid, "Пришли задание в формате: @канал|Награда|Описание")
    elif data == "admin_del_task":
        USER_STATE[uid]["step"] = "del_task"
        bot.send_message(uid, "Пришли ID задания для удаления")
    elif data == "admin_ban":
        USER_STATE[uid]["step"] = "ban_user"
        bot.send_message(uid, "Пришли @username для бана")
    elif data == "admin_withdraws":
        cursor.execute("SELECT * FROM withdraw_requests")
        reqs = cursor.fetchall()
        if not reqs:
            bot.send_message(uid, "❌ Нет запросов на вывод")
        else:
            for r in reqs:
                bot.send_message(uid, f"ID: {r[0]}\nUser: {r[1]}\nСумма: {r[2]} G", reply_markup=admin_withdraw_kb(r[0]))
    elif data == "admin_check_refs":
        cursor.execute("SELECT user_id, username FROM users WHERE referrer IS NOT NULL")
        rows = cursor.fetchall()
        text = "Рефералы:\n"
        for u, name in rows:
            text += f"{name} → {u}\n"
        bot.send_message(uid, text)
    elif data.startswith("withdraw_accept:"):
        req_id = int(data.split(":")[1])
        cursor.execute("DELETE FROM withdraw_requests WHERE id=?", (req_id,))
        conn.commit()
        bot.answer_callback_query(c.id, "✅ Вывод подтвержден")
    elif data.startswith("withdraw_decline:"):
        req_id = int(data.split(":")[1])
        cursor.execute("DELETE FROM withdraw_requests WHERE id=?", (req_id,))
        conn.commit()
        bot.answer_callback_query(c.id, "❌ Вывод отменён")

# ===== WEBHOOK =====
@app.route(f"/bot/{TOKEN}/", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

# ===== ЗАПУСК =====
if __name__=="__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}/")
    app.run(host="0.0.0.0", port=5000)
