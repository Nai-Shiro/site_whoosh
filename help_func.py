import random
import sqlite3
import string
import time


def randomword(length):
    letters = list(string.ascii_lowercase)
    for i in range(10):
        letters.append(str(i))
    return ''.join(random.choice(letters) for _ in range(length))


def create_admins_n_users_list():  # Пересоздание списка админов и юзеров
    db = sqlite3.connect("users_av.db")
    admins = [i[0] for i in db.cursor().execute("select chat from Users\
                                 where access like ?", ('admin',)).fetchall()]
    users = [i[0] for i in db.cursor().execute("select chat from Users\
                                 where access like ?", ('user',)).fetchall()]
    return users, admins


def check_time_to_buy(user_id):  # Проверка времени до покупки
    try:
        db = sqlite3.connect("users_av.db")
        if db.cursor().execute('select chat from Timeforbuy where chat = ?', (user_id,)).fetchone():
            time_t = db.cursor().execute('select time'
                                         ' from Timeforbuy where chat = ?', (user_id,)).fetchone()[0]
            if int(time_t) - int(time.time()) <= 0:
                return True
            else:
                return False
        else:
            return True
    except Exception as v:
        print(f"{v} + Ошибка в check_time_to_buy")


def check_pl(user_id):  # сколько действителен платеж, и его удаление в случаи просрочки
    try:
        db = sqlite3.connect("users_av.db")
        time_sub = db.cursor().execute("select time from Plat where chat = ?", (user_id,)).fetchone()
        if time_sub:
            time_now = int(time.time())
            ost = time_sub[0] - time_now
            if ost <= 0:
                db.cursor().execute('delete from Plat where chat = ?', (user_id,))
                db.commit()
                return False
            else:
                return True
        else:
            return False
    except Exception as v:
        print(f"{v} + Ошибка в check_pl")


def check_av(user_id):  # сколько действительна подписка, и её отмена в случаи просрочки
    try:
        db = sqlite3.connect("users_av.db")
        time_sub = db.cursor().execute("select time_sub from Users where chat = ?", (user_id,)).fetchone()
        if time_sub:
            time_now = int(time.time())
            ost = time_sub[0] - time_now
            if ost <= 0:
                db.cursor().execute('delete from Users where chat = ?', (user_id,))
                db.commit()
                create_admins_n_users_list()
                return False
            else:
                return True
        else:
            return False
    except Exception as v:
        print(f"{v} + Ошибка в check_av")


def day_to_sec(days):  # дни в секунды
    return days * 24 * 60 * 60
