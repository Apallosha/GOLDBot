from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# ================== ОБЯЗАТЕЛЬНАЯ ПОДПИСКА ==================

def mandatory_subscribe_kb(channels: list):
    kb = InlineKeyboardMarkup(row_width=1)

    for ch in channels:
        kb.add(
            InlineKeyboardButton(
                text="Подписаться!",
                url=f"https://t.me/{ch.replace('@', '')}"
            )
        )

    kb.add(
        InlineKeyboardButton(
            text="Проверить",
            callback_data="check_mandatory_sub"
        )
    )
    return kb


# ================== ГЛАВНОЕ МЕНЮ ==================

def main_menu_kb():
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton("Профиль", callback_data="menu_profile"),
        InlineKeyboardButton("Пригласить", callback_data="menu_invite")
    )
    kb.add(
        InlineKeyboardButton("Задания", callback_data="menu_tasks"),
        InlineKeyboardButton("Вывод G", callback_data="menu_withdraw")
    )
    kb.add(
        InlineKeyboardButton("Важно", callback_data="menu_info")
    )

    return kb


# ================== ЗАДАНИЯ ==================

def tasks_list_kb(tasks: list):
    kb = InlineKeyboardMarkup(row_width=1)

    for task in tasks:
        task_id, channel, reward, text = task
        kb.add(
            InlineKeyboardButton(
                text=f"Задание #{task_id}",
                callback_data=f"task_open:{task_id}"
            )
        )

    return kb


def task_check_kb(task_id: int):
    kb = InlineKeyboardMarkup(row_width=1)

    kb.add(
        InlineKeyboardButton(
            text="Проверить",
            callback_data=f"task_check:{task_id}"
        )
    )

    return kb


# ================== ВЫВОД ==================

def withdraw_confirm_kb():
    kb = InlineKeyboardMarkup(row_width=1)

    kb.add(
        InlineKeyboardButton(
            text="Отменить",
            callback_data="withdraw_cancel"
        )
    )

    return kb


# ================== АДМИН ПАНЕЛЬ ==================

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
        InlineKeyboardButton("Запросы на вывод G", callback_data="admin_withdraws")
    )

    kb.add(
        InlineKeyboardButton("Проверка", callback_data="admin_check_refs")
    )

    return kb


def admin_withdraw_kb(withdraw_id: int):
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton(
            text="Подтвердить вывод",
            callback_data=f"withdraw_accept:{withdraw_id}"
        ),
        InlineKeyboardButton(
            text="Отменить вывод",
            callback_data=f"withdraw_decline:{withdraw_id}"
        )
    )

    return kb
