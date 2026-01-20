from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("👤 Профиль", callback_data="menu_profile"))
    kb.add(InlineKeyboardButton("🔗 Пригласить", callback_data="menu_invite"))
    kb.add(InlineKeyboardButton("🎯 Задания", callback_data="menu_tasks"))
    kb.add(InlineKeyboardButton("💰 Вывод G", callback_data="menu_withdraw"))
    kb.add(InlineKeyboardButton("⚠️ Важно", callback_data="menu_info"))
    return kb

def mandatory_subscribe_kb(channels):
    kb = InlineKeyboardMarkup(row_width=1)
    for ch in channels:
        kb.add(InlineKeyboardButton("Подписаться!", url=f"https://t.me/{ch.replace('@','')}"))
    kb.add(InlineKeyboardButton("Проверить ✅", callback_data="check_mandatory_sub"))
    return kb

def tasks_list_kb(tasks):
    kb = InlineKeyboardMarkup(row_width=1)
    for t in tasks:
        kb.add(InlineKeyboardButton(f"Задание #{t[0]}", callback_data=f"task_open:{t[0]}"))
    return kb

def task_check_kb(task_id):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Проверить ✅", callback_data=f"task_check:{task_id}"))
    return kb

def admin_menu_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("+Обязательная подписка", callback_data="admin_add_mandatory"),
        InlineKeyboardButton("-Обязательная подписка", callback_data="admin_del_mandatory")
    )
    kb.add(
        InlineKeyboardButton("+Задание", callback_data="admin_add_task"),
        InlineKeyboardButton("-Задание", callback_data="admin_del_task")
    )
    kb.add(
        InlineKeyboardButton("Бан", callback_data="admin_ban"),
        InlineKeyboardButton("Запросы на вывод", callback_data="admin_withdraws")
    )
    kb.add(InlineKeyboardButton("Проверка рефералов", callback_data="admin_check_refs"))
    return kb

def admin_withdraw_kb(req_id):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("Подтвердить вывод", callback_data=f"withdraw_accept:{req_id}"),
        InlineKeyboardButton("Отменить вывод", callback_data=f"withdraw_decline:{req_id}")
    )
    return kb
