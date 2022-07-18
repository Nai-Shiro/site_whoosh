import sqlite3
import threading
import time

import telebot
from help_func import create_admins_n_users_list, randomword, check_pl, check_av, check_time_to_buy, day_to_sec
from telebot import types
from yoomoney import Quickpay, Client

token = "5533820366:AAGhJ4OQ3hmOfdyT_2GK8ENqlVuevjlJLbk"  # "5533820366:AAGhJ4OQ3hmOfdyT_2GK8ENqlVuevjlJLbk" токен бота
token_y = "4100117884397250.BA5EFCC5CD25E1BDF810FBE73A" \
          "A1724380DAC4AB554E2751B0C39125B0AB29EFAA2EDA1090" \
          "6DB3FD8A337512F52B2E9B53F90ADA347489B12E34827D971A73F" \
          "7D8553FC7E360294833FAD3CF3E127A44F7726695B3414EC259C6080CC53" \
          "614289A749D3B80947A5D3632B447AF4C458F05C999DB8D85245EFA22A7DE81F2DAF8"  # токен Юмани
client = Client(token_y)
bot = telebot.TeleBot(token)
db = sqlite3.connect("users_av.db")
price = 7  # Цена номеров

# ПОЛЬЗОВАТЕЛЬСКИЕ КНОПКИ
markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
btn1 = types.KeyboardButton(text='📱Купить аккаунт')
btn2 = types.KeyboardButton(text='📋Мануал')
btn3 = types.KeyboardButton(text="💳Пополнить баланс")
btn4 = types.KeyboardButton(text="✉Реф. ссылка")
btn5 = types.KeyboardButton(text="⚙Контакты")
btn6 = types.KeyboardButton(text="👤 Профиль")
markup.add(btn1, btn3, btn6, btn2, btn4, btn5)

# АДМИНСКИЕ КНОПКИ
markup1 = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
btn11 = types.KeyboardButton(text='users')
btn22 = types.KeyboardButton(text='admins')
btn33 = types.KeyboardButton(text='add_user')
btn44 = types.KeyboardButton(text='delete_user')
btn55 = types.KeyboardButton(text='add_admin')
btn66 = types.KeyboardButton(text='delete_admin')
btn77 = types.KeyboardButton(text='check_users_balance')
btn88 = types.KeyboardButton(text='check_one_user_balance')
btn99 = types.KeyboardButton(text='change_user_balance')
btn100 = types.KeyboardButton(text='send_message')
markup1.add(btn11, btn22, btn33, btn44, btn55, btn66, btn77, btn88, btn99, btn100)

# кнопки пополнения баланса
markup2 = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
btn_back = types.KeyboardButton(text='Отмена')
btn_check = types.KeyboardButton(text="Проверить платеж")
markup2.add(btn_check, btn_back)

# markup3 = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
# btn_back_1 = types.KeyboardButton(text='Отмена покупки')
# markup3.add(btn_back_1)

# reply_markup = markup
# reply_markup1 = markup1

# СТАТИСТИКА
users, admins = create_admins_n_users_list()
our_mess = None


def stop_t(*chat_id):  # что происходит при остановке таймера
    global chat_id_user_bot
    chat_id = "".join(chat_id)
    db = sqlite3.connect('users_av.db')
    bot_id = db.cursor().execute('select bot from Users where chat = ?', (chat_id,)).fetchone()[0]
    bot.send_message(chat_id_user_bot[bot_id]['chat_id_to_add'], "Время вышло, возвращаю в главное меню",
                     reply_markup=markup
                     )
    if chat_id_user_bot[bot_id]['balance_to_add']:
        bot.send_message(bot_id, "Отмена")
    else:
        if db.cursor().execute('select chat from Timeforbuy where chat = ?',
                               (chat_id_user_bot[bot_id]['chat_id_to_add'],)).fetchone():
            db.cursor().execute('update Timeforbuy set time = ? where chat = ?', (
                int(time.time()) + time_to_buy, chat_id_user_bot[bot_id]['chat_id_to_add']))
        else:
            db.cursor().execute(f"insert into Timeforbuy(chat, time)"
                                f" values(?, ?)",
                                (chat_id_user_bot[bot_id]['chat_id_to_add'], int(time.time()) + time_to_buy))
    db.commit()
    chat_id_user_bot[bot_id]['balance_to_add'] = False
    chat_id_user_bot[bot_id]['buy_acc'] = False
    chat_id_user_bot[bot_id]['chat_id_to_add'] = None
    chat_id_user_bot[bot_id]['sum_to_add'] = 0


# Переменные для пополнения баланса и покупки

time_to_cancel = 120  # время на пополнение баланса и покупку номера
time_to_buy = 60  # время ограничения на покупку

chat_id_user_bot = {5139052149: {'chat_id_to_add': None,
                                 'balance_to_add': False, 'buy_acc': False, 'sum_to_add': False,
                                 'thread': False, 'last_chat_id_to_add': None},
                    5341167988: {'chat_id_to_add': None,
                                 'balance_to_add': False, 'buy_acc': False, 'sum_to_add': False,
                                 'thread': False, 'last_chat_id_to_add': None},
                    5460795965: {'chat_id_to_add': None,
                                 'balance_to_add': False, 'buy_acc': False, 'sum_to_add': False,
                                 'thread': False, 'last_chat_id_to_add': None},
                    5471992680: {'chat_id_to_add': None,
                                 'balance_to_add': False, 'buy_acc': False, 'sum_to_add': False,
                                 'thread': False, 'last_chat_id_to_add': None}}  # id ботов-посредника и их собственные
# переменные

who = 0
count_bots = 4  # количество ботов

# Флаги, для работа админ.панели
flags = [False, False, False, False, False, False, False]


# ПРОВЕРКА ПОЛЬЗОВАТЕЛЯ НА ИНДИФИКАТОР
@bot.message_handler(commands=['start'])
def privetctive(message):  # стартовые сообщения и действия
    global users, admins, flags
    try:
        db = sqlite3.connect("users_av.db")
        if db.cursor().execute('select bot from Users where chat = ?', (message.chat.id,)).fetchone():
            bot_id = db.cursor().execute('select bot from Users where chat = ?', (message.chat.id,)).fetchone()[0]
            if bot_id in chat_id_user_bot.keys():
                if message.chat.id == chat_id_user_bot[bot_id]['chat_id_to_add']:
                    # сброс переменных пополнения, при нажатии /start пользователем, который
                    # пополняет
                    chat_id_user_bot[bot_id]['chat_id_to_add'] = None
                    chat_id_user_bot[bot_id]['balance_to_add'] = False
                    chat_id_user_bot[bot_id]['buy_acc'] = False
                    chat_id_user_bot[bot_id]['thread'].cancel
                    chat_id_user_bot[bot_id]['thread'] = None
        if message.chat.id in users and check_av(message.chat.id):
            bot.send_message(message.chat.id, f"    Aккаунт подтвержден.\nПриятного пользования :)",
                             reply_markup=markup)
            bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAEFLWliwHa7mMGLymLDkpcOW8nrdcpicAACDwADDkfHKCnIXzw4qLKjKQQ')
            work_users(message)


        elif message.chat.id in admins:
            flags = [False, False, False, False, False, False, False]
            bot.send_sticker(message.chat.id,
                             'CAACAgIAAxkBAAEFLoRiwXdm6VEuWH7Cr_wAAW15-9rBC0oAAjoAAw5HxyjJYTg1fJGBzykE')
            bot.send_message(message.chat.id, "АДМИНСКАЯ ПАНЕЛЬ", reply_markup=markup1)
            work_admins(message)

        else:
            work_podpiska(message)

    except Exception as v:
        print(f"{v} - ошибка в privetctive")


@bot.message_handler(content_types=['text'])
def handler(message):  # главный обработчик
    global time_to_buy, flags, chat_id_user_bot
    # try:
    if True:
        if message.chat.id in admins:
            # отсеивание сообщений в админ панели
            work_admins(message)
        elif message.chat.id in list(chat_id_user_bot.keys()):  # сообщение ботов и пополнение баланса
            if chat_id_user_bot[message.chat.id]['chat_id_to_add']:
                text = message.text
                db = sqlite3.connect("users_av.db")
                if text == "Баланс успешно пополнен":
                    balance = \
                        db.cursor().execute('select balance from Users where chat = ?',
                                            (chat_id_user_bot[message.chat.id]['chat_id_to_add'],)).fetchone()[0]
                    db.cursor().execute('update Users set balance = ? where chat = ?', (
                        str(int(balance) + chat_id_user_bot[message.chat.id]['sum_to_add']),
                        chat_id_user_bot[message.chat.id]['chat_id_to_add']))
                    db.commit()
                    bot.send_message(chat_id_user_bot[message.chat.id]['chat_id_to_add'], "Баланс успешно пополнен",
                                     reply_markup=markup)
                    chat_id_user_bot[message.chat.id]['thread'].cancel()
                    chat_id_user_bot[message.chat.id]['thread'] = None
                    chat_id_user_bot[message.chat.id]['chat_id_to_add'] = None
                    chat_id_user_bot[message.chat.id]['sum_to_add'] = 0
                    chat_id_user_bot[message.chat.id]['balance_to_add'] = False

                elif "📱 Номер:" in text:
                    bot.send_message(chat_id_user_bot[message.chat.id]['chat_id_to_add'], text, reply_markup=markup)
                    chat_id_user_bot[message.chat.id]['last_chat_id_to_add'] = \
                        chat_id_user_bot[message.chat.id]['chat_id_to_add']

                elif "🕰 Код:" in text and chat_id_user_bot[message.chat.id]['chat_id_to_add'] \
                        == chat_id_user_bot[message.chat.id]['last_chat_id_to_add']:
                    bot.send_message(chat_id_user_bot[message.chat.id]['chat_id_to_add'], text, reply_markup=markup)
                    chat_id_user_bot[message.chat.id]['thread'].cancel()
                    chat_id_user_bot[message.chat.id]['thread'] = None
                    if db.cursor().execute('select chat from Timeforbuy where chat = ?', (
                            chat_id_user_bot[message.chat.id]['chat_id_to_add'],)).fetchone():
                        db.cursor().execute('update Timeforbuy set time = ? where chat = ?', (
                            int(time.time()) + time_to_buy, chat_id_user_bot[message.chat.id]['chat_id_to_add']))
                    else:
                        db.cursor().execute(f"insert into Timeforbuy(chat, time)"
                                            f" values(?, ?)",
                                            (chat_id_user_bot[message.chat.id]['chat_id_to_add'],
                                             int(time.time()) + time_to_buy))
                    db.commit()
                    chat_id_user_bot[message.chat.id]['chat_id_to_add'] = None
                    chat_id_user_bot[message.chat.id]['buy_acc'] = False

                elif "Код для входа:" not in text and "Номер для входа в аккаунт:" not in text and \
                        text != "Баланс успешно пополнен":
                    bot.send_message(chat_id_user_bot[message.chat.id]['chat_id_to_add'], text)

        elif message.chat.id in users:  # отсеивание сообщений от юзеров
            work_users(message)

        else:  # все остальные сообщения идут сюда
            work_podpiska(message)
    # except Exception as v:
    #      print(f"{v} + Ошибка в handler")


def work_admins(message):  # функция обработки сообщений админов
    global admins, flags, who, count_bots, our_mess, users
    db = sqlite3.connect("users_av.db")
    if message.chat.id not in admins:
        bot.send_message(message.chat.id, 'Ты не админ')

    if message.text == "users":  # вывод юзеров
        users_list = [str(i[0]) for i in
                      db.cursor().execute('select name from Users where access like ?', ('user',)).fetchall()]
        bot.send_message(message.chat.id, "Пользователи: " + " ;| ".join(users_list))

    elif message.text == "admins":  # вывод админов
        users_list = [str(i[0]) for i in
                      db.cursor().execute('select name from Users where access like ?', ('admin',)).fetchall()]
        bot.send_message(message.chat.id, "Админы: " + " ;| ".join(users_list))

    elif message.text == "add_user":  # добавление юзера
        bot.send_message(message.chat.id, "Добавление пользователя, введите"
                                          " id пользователя, его ник и время подписки в днях (id/name/time): ")
        flags[0] = True
        flags[1], flags[2], flags[3], flags[4], flags[5], flags[6] = False, False, False, False, False, False

    elif message.text == "delete_user":  # удаление юзера
        bot.send_message(message.chat.id, "Удаление пользователя, введите ник пользователя: ")
        flags[1] = True
        flags[2], flags[3], flags[0], flags[4], flags[5], flags[6] = False, False, False, False, False, False

    elif message.text == "add_admin":  # добавление админов
        bot.send_message(message.chat.id, "Добавление админа, введите id пользователя и его ник(id/name): ")
        flags[2] = True
        flags[0], flags[1], flags[3], flags[4], flags[5], flags[6] = False, False, False, False, False, False

    elif message.text == "delete_admin":  # удаление админов
        bot.send_message(message.chat.id, "Удаление админа, введите ник админа: ")
        flags[3] = True
        flags[1], flags[0], flags[2], flags[4], flags[5], flags[6] = False, False, False, False, False, False
    elif message.text == 'check_users_balance':  # проверка баланса всех юзеров
        users_list = [f"{str(i[0])} - {str(i[1])}руб." for i in
                      db.cursor().execute("select name, balance from Users where access like 'user'").fetchall()]
        bot.send_message(message.chat.id, f"Пользователи: {' ;| '.join(users_list)}")
    elif message.text == 'change_user_balance':  # изменение баланса у юзера
        bot.send_message(message.chat.id, "Введите ник пользователя и нужную сумму(name/money): ")
        flags[4] = True
        flags[1], flags[0], flags[2], flags[3], flags[5], flags[6] = False, False, False, False, False, False
    elif message.text == 'check_one_user_balance':  # проверка баланса у одного юзера
        bot.send_message(message.chat.id, "Введите ник пользователя: ")
        flags[5] = True
        flags[1], flags[0], flags[2], flags[3], flags[4], flags[6] = False, False, False, False, False, False
    elif message.text == 'send_message':  # отправить сообщение всем юзерам
        bot.send_message(message.chat.id, "Введите сообщение:")
        flags[6] = True
        flags[1], flags[0], flags[2], flags[3], flags[4], flags[5] = False, False, False, False, False, False
    else:
        try:
            # работа выше нажатых кнопок flag = [0: add_user, 1: delete_user, 2: add_admin, 3: delete_admin
            # 4: change_user_balance]
            if flags[2]:  # добавление админов
                if not db.cursor().execute('select chat from Users where name like ? or chat = ? '
                                           'and access not like ?',
                                           (message.text.split('/')[0], message.text.split('/')[1],
                                            'admin')).fetchone():
                    id, name = message.text.split('/')
                    db.cursor().execute("delete from Users where chat = ?", (id,))
                    who = (who + 1) % count_bots
                    db.cursor().execute('insert'
                                        ' into Users(chat, access, time_sub, balance, name, bot)'
                                        ' values(?, ?, ?, ?, ?, ?)',
                                        (int(id), 'admin', int(time.time()) + day_to_sec(5000), 0, name,
                                         list(chat_id_user_bot.keys())[who]))
                    db.commit()
                    users, admins = create_admins_n_users_list()
                    flags[2] = False
                    bot.send_message(message.chat.id, 'Успешно')
                else:
                    bot.send_message(message.chat.id, 'Такой админ уже есть')

            elif flags[0]:  # добавление юзера
                if not db.cursor().execute('select chat from Users where name like ? or chat = ?',
                                           (message.text.split('/')[0], message.text.split('/')[1])).fetchone():
                    db = sqlite3.connect("users_av.db")
                    id, name, ntime = message.text.split('/')
                    who = (who + 1) % count_bots
                    db.cursor().execute('insert'
                                        ' into Users(chat, access, time_sub, balance, name, bot)'
                                        ' values(?, ?, ?, ?, ?, ?)',
                                        (int(id), 'user', int(time.time()) + day_to_sec(int(ntime)), 0, name,
                                         list(chat_id_user_bot.keys())[who]))
                    db.commit()
                    users, admins = create_admins_n_users_list()
                    flags[0] = False
                    bot.send_message(message.chat.id, 'Успешно')
                else:
                    bot.send_message(message.chat.id, 'Такой пользователь уже есть')

            elif flags[3]:  # удаление админов
                db = sqlite3.connect("users_av.db")
                name = message.text
                if db.cursor().execute('select access from Users where name like ?',
                                       (name,)).fetchone()[0] == 'admin':
                    db.cursor().execute('update Users set time_sub = ?'
                                        ',access = ? where name like ?',
                                        (int(time.time()) + day_to_sec(30), 'user', name))
                    db.commit()
                    users, admins = create_admins_n_users_list()
                    flags[3] = False
                    bot.send_message(message.chat.id, 'Успешно')
                else:
                    bot.send_message(message.chat.id, "Это не админ")

            elif flags[1]:  # удаление юзера
                db = sqlite3.connect("users_av.db")
                name = message.text
                if db.cursor().execute('select access from Users where name like ?',
                                       (name,)).fetchone()[0] == 'user':
                    db.cursor().execute('delete from Users where name like ?', (name,))
                    db.commit()
                    flags[1] = False
                    bot.send_message(message.chat.id, 'Успешно')
                    users, admins = create_admins_n_users_list()
                else:
                    bot.send_message(message.chat.id, "Это не пользователь")

            elif flags[4]:  # изменение баланса у юзера
                db = sqlite3.connect("users_av.db")
                name, money = message.text.split('/')[0], message.text.split('/')[1]
                if db.cursor().execute('select access from Users where name like ?',
                                       (name,)).fetchone()[0] == 'user':
                    db.cursor().execute('update Users set balance = ?'
                                        'where name like ?',
                                        (int(money), name))
                    db.commit()
                    bot.send_message(message.chat.id, 'Успешно')
                    users, admins = create_admins_n_users_list()
                    flags[4] = False

            elif flags[5]:  # проверка баланса у одного юзера
                name = message.text
                balance = db.cursor().execute(
                    "select balance from Users where access like 'user' and name like ?",
                    (name,)).fetchone()[0]
                flags[5] = False
                bot.send_message(message.chat.id, f"{name} - {balance}руб.")

            elif flags[6]:  # отправить сообщение всем юзерам
                mess = message.text
                if not our_mess:
                    our_mess = mess
                    bot.send_message(message.chat.id,
                                     f'Вы уверены в этом сообщение: {our_mess}. ?. Если да, напишите 1:')
                elif str(mess) == '1':
                    bot.send_message(message.chat.id, f"Успешно.")
                    db = sqlite3.connect('users_av.db')
                    users_t = [i[0] for i in db.cursor().execute("select chat from Users"
                                                                 "where access like ? "
                                                                 "and name not like '%bot_user%'").fetchall()]
                    for i in users_t:
                        bot.send_message(i, our_mess, reply_markup=markup)
                else:
                    bot.send_message(message.chat.id, f"Отмена.")


        except Exception as v:  # обработчик ошибок
            print(v)
            flags = [False, False, False, False, False, False]
            bot.send_message(message.chat.id, "Ошибка в данных")


def work_users(message):  # Функция обработки сообщений юзеров
    global time_to_buy, chat_id_user_bot, price
    # try:
    if True:
        db = sqlite3.connect('users_av.db')
        bot_id = db.cursor().execute('select bot from Users where chat = ?', (message.chat.id,)).fetchone()[0]
        if message.text == "⚙Контакты":
            bot.send_sticker(message.chat.id,
                             'CAACAgIAAxkBAAEFLoBiwXc3kke5xYI5-v5dBXMXD_tYcgACIAADDkfHKIn3WfQkFme2KQQ')
            bot.send_message(message.chat.id, "По всем вопросам:\n@spasontis")


        elif message.text == "✉Реф. ссылка":
            bot.send_message(message.chat.id, "https://whoosh.app.link/invite_friend?referral_id=31DfEPs")

        elif message.text == "📋Мануал":
            bot.send_message(message.chat.id, """   1) После покупки аккаунта вам будет дан номер по которому вы создаете новый аккаунт в приложении Whoosh.
( Подтверждение смс кода вам пришлёт бот ). При регистрации вводите свою настоящую банковскую карту! 

    2) Заходите в промокоды и вписываете “GOODRIDE”, только после этого активируете реферальную сссылку.
(Реф. ccылка выдается в меню бота).

    3) Далее активируете подписку в приложении Whoosh ( количество дней не важно ). Поскольку на первый срок она бесплатная, деньги не спишутся. Нужно будет убрать автопродление подписки.

    4) Теперь у вас есть 2 промокода по 100 рублей (100 рублей ~ 14 минут поездки).

    5) Для большей экономии, советуем отключить галочку страховки в 35 рублей перед началом поездки.

    6) Не превышайте лимит ста рублей на поездку, иначе дальше будут списываться деньги с вашей карты.

    7) После использования всех промокодов на аккаунте убираем вашу банковскую карту в оплате и автопродление подписки !

ОДИН ПРОМОКОД – ОДНА ПОЕЗДКА.""")

        elif message.text == "👤 Профиль":
            db = sqlite3.connect("users_av.db")
            bot.send_sticker(message.chat.id,
                             'CAACAgIAAxkBAAEFLoJiwXdNSLjmHdMUG1cwQRVsZRfcLwACMwADDkfHKGxLD9RFtmVqKQQ')
            bot.send_message(message.chat.id, f"""
👔 Профиль:
👤 Ваш ID: {str(message.chat.id)}
💼 Ваш баланс: {str(db.cursor().execute(
                'select balance from Users where chat = ?', (message.chat.id,)).fetchone()[0])} руб.""")

        elif message.text == "💳Пополнить баланс" and \
                not chat_id_user_bot[bot_id]['balance_to_add'] and not chat_id_user_bot[bot_id]['buy_acc']:
            bot.send_message(message.chat.id,
                             f"Минимальная сумма 10 рубль.\nДля пополнения вам будет "
                             f"выделено {time_to_cancel} сек. После оплаты обязательно нажмите"
                             f" 'Проверить платеж', иначе деньги не зачислятся.\nВведите сумму пополнения (целое число):",
                             reply_markup=markup2)
            chat_id_user_bot[bot_id]['balance_to_add'] = True
            chat_id_user_bot[bot_id]['chat_id_to_add'] = message.chat.id
            chat_id_user_bot[bot_id]['thread'] = threading.Timer(time_to_cancel, stop_t, list(str(message.chat.id)))
            chat_id_user_bot[bot_id]['thread'].start()
            bot.send_message(bot_id, text=message.text)

        elif message.text == "📱Купить аккаунт" and not chat_id_user_bot[bot_id]['balance_to_add'] and \
                not chat_id_user_bot[bot_id]['buy_acc']:
            if check_time_to_buy(message.chat.id):
                if int(db.cursor().execute('select balance from Users where chat = ?', (message.chat.id,)).fetchone()[
                           0]) >= price:
                    chat_id_user_bot[bot_id]['buy_acc'] = True
                    chat_id_user_bot[bot_id]['chat_id_to_add'] = message.chat.id
                    bot.send_message(message.chat.id, "❗️ ОБЯЗАТЕЛЬНО ПРОЧТИ МАНУАЛ ❗️\n"
                                                      "Вы уверены?\nЕсли да, то "
                                                      "на все действия у вас есть"
                                                      f" {time_to_cancel} сек.\nДля подтверждения отправьте: 1",
                                     reply_markup=types.ReplyKeyboardRemove())
                    chat_id_user_bot[bot_id]['thread'] = threading.Timer(time_to_cancel, stop_t,
                                                                         list(str(message.chat.id)))
                    chat_id_user_bot[bot_id]['thread'].start()
                else:
                    bot.send_message(message.chat.id, f"Недостаточно средств, цена аккаунта = {price} рублям",
                                     reply_markup=markup)
                    chat_id_user_bot[bot_id]['buy_acc'] = False
                    chat_id_user_bot[bot_id]['chat_id_to_add'] = None
            else:
                bot.send_message(message.chat.id, f"Вы можете покупать аккаунт лишь раз в {time_to_buy} сек.",
                                 reply_markup=markup)
                chat_id_user_bot[bot_id]['buy_acc'] = False
                chat_id_user_bot[bot_id]['chat_id_to_add'] = None

        elif (message.text == "💳Пополнить баланс" or
              message.text == "📱Купить аккаунт") and (chat_id_user_bot[bot_id]['balance_to_add']
                                                       or chat_id_user_bot[bot_id]['buy_acc']):  # очередь
            bot.send_message(message.chat.id, text="Пожалуйста, дождитесь своей очереди", reply_markup=markup)

        else:
            if chat_id_user_bot[bot_id]['chat_id_to_add'] == message.chat.id and \
                    chat_id_user_bot[bot_id]['buy_acc']:  # Обработка сообщений после нажатия купить аккаунт
                if message.text == "1":
                    db = sqlite3.connect('users_av.db')
                    print(chat_id_user_bot[bot_id]['chat_id_to_add'])
                    balance = \
                        db.cursor().execute('select balance from Users where chat = ?', (
                            chat_id_user_bot[bot_id]['chat_id_to_add'],)).fetchone()[0]
                    db.cursor().execute('update Users set balance = ? where chat = ?', (
                        str(int(balance) - price), chat_id_user_bot[bot_id]['chat_id_to_add'],))
                    db.commit()
                    bot.send_message(bot_id, "📱Купить аккаунт")
                    bot.send_message(chat_id_user_bot[bot_id]['chat_id_to_add'], "Подождите пару секунд",
                                     reply_markup=markup)
                else:
                    bot.send_message(chat_id_user_bot[bot_id]['chat_id_to_add'], "Возвращаемся в главное меню",
                                     reply_markup=markup)
                    chat_id_user_bot[bot_id]['thread'].cancel()
                    chat_id_user_bot[bot_id]['thread'] = None
                    chat_id_user_bot[bot_id]['buy_acc'] = False
                    chat_id_user_bot[bot_id]['chat_id_to_add'] = None

            elif chat_id_user_bot[bot_id]['balance_to_add'] \
                    and chat_id_user_bot[bot_id]['chat_id_to_add'] == message.chat.id:
                # обработка сообщений после нажатия пополнить баланс
                if message.text == 'Проверить платеж':
                    bot.send_message(bot_id, text=message.text)  # сообщение ботов
                elif message.text == "Отмена":
                    bot.send_message(bot_id, 'Отмена')  # сообщение ботов
                    bot.send_message(message.chat.id, "Вы вернулись в главное меню.", reply_markup=markup)
                    chat_id_user_bot[bot_id]['balance_to_add'] = False
                    chat_id_user_bot[bot_id]['chat_id_to_add'] = None
                    chat_id_user_bot[bot_id]['thread'].cancel()
                    chat_id_user_bot[bot_id]['thread'] = None

                else:
                    if all([i in "1234567890" for i in list(message.text)]):
                        if not chat_id_user_bot[bot_id]['sum_to_add']:
                            if int(message.text) < 10:
                                bot.send_message(chat_id_user_bot[bot_id]['chat_id_to_add'],
                                                 text='Сумма меньше мин.')
                            else:
                                chat_id_user_bot[bot_id]['sum_to_add'] = int(message.text)
                        bot.send_message(bot_id, text=int(message.text))
                        # сообщение ботов
                    else:
                        bot.send_message(chat_id_user_bot[bot_id]['chat_id_to_add'], text='Неправильно введена сумма')
    # except Exception as v:
    #     print(f"{v} + В work_users")


def work_podpiska(message):  # функция обработки покупки подписки
    global who, count_bots, chat_id_user_bot, users, admins
    if message.text == "Купить":
        db = sqlite3.connect("users_av.db")
        # если у пользователя активный платеж и его удаление из БД, если есть
        if db.cursor().execute("select label from Plat where chat = ?", (message.chat.id,)).fetchall():
            db.cursor().execute('delete from Plat where chat = ?', (message.chat.id,))
        tryi = True
        while tryi:  # создание названия операции платежа
            try:
                label = randomword(16)
                time_sub = int(time.time()) + day_to_sec(1)
                db.cursor().execute(f"insert into Plat(chat, time, label) values(?, ?, ?)",
                                    (message.chat.id, time_sub, label))
                db.commit()
                tryi = False
            except Exception:
                pass
        quickpay = Quickpay(  # создание платежа
            receiver="4100117884397250",  # <-- тут свой номер юмани для создания платежа
            quickpay_form="shop",
            targets="Sponsor this project",
            paymentType="SB",
            sum=2,  # <-- цена
            label=label
        )
        bot.send_message(message.chat.id, quickpay.redirected_url)
    elif message.text == 'Проверить':
        try:
            if not check_pl(message.chat.id):
                bot.send_message(message.chat.id, "Создайте новый платеж, пред. просрочен")
            else:
                db = sqlite3.connect("users_av.db")
                plat = db.cursor().execute("select label from Plat where chat = ?", (message.chat.id,)).fetchall()
                if plat:
                    history = client.operation_history(label=plat[-1][0])
                    print(history.operations)
                    for operation in history.operations:  # проверка операций кошелька
                        print(operation.status)
                        if operation.status == 'success':
                            db = sqlite3.connect("users_av.db")
                            who = (who + 1) % count_bots
                            time_sub = int(time.time()) + day_to_sec(30)  # дней в подписке(число 30)
                            db.cursor().execute(f"insert into Users(chat, access, balance, time_sub, name, bot)"
                                                f" values(?, ?, ?, ?, ?, ?)",
                                                (message.chat.id, 'user', 0, time_sub, message.from_user.username,
                                                 list(chat_id_user_bot.keys())[who]))
                            db.commit()
                            users, admins = create_admins_n_users_list()
                            db.cursor().execute('delete from Plat where chat = ?', (message.chat.id,))
                            db.commit()
                            bot.send_message(message.chat.id, "Успешно", reply_markup=markup)
                            break

                    else:
                        bot.send_message(message.chat.id, "Платеж еще не пришёл")
        except Exception as v:
            print(f"{v} + Ошибка в work_podpiska")
    else:
        markup3 = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        btn_buy_1 = types.KeyboardButton(text='Купить')
        btn_check_1 = types.KeyboardButton(text='Проверить')
        markup3.add(btn_buy_1, btn_check_1)
        bot.send_message(message.chat.id, f"Аккаунт не подтвержден.\nОформи подписку ( 30 дней = 150 рублей ).",
                         reply_markup=markup3)
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAEFLWtiwHeH-bAfHmMFfXV50bT1Cfv8SQACEgADDkfHKATauSzHGIhqKQQ')


if __name__ == '__main__':
    bot.polling()
