import time

from pyrogram import Client, filters

app = Client("my_account")
addb = False
last_m = None
buy_acc = False


@app.on_message(filters.chat("SMSBest_bot"))
async def check_chat(client, message):
    global addb, last_m, buy_acc
    if message.reply_markup:
        last_m = message
    if message.caption:
        time.sleep(1)
        if 'Заказ завершён.' in message.caption or 'Вы вернулись в меню.' in message.caption:
            pass
        elif '🕰 Код:' in message.caption:
            time.sleep(1)
            last_m.click(0)
            await app.send_message('WhooshScript_bot', message.caption)
            buy_acc = False
            last_m = None
        elif "🌍 Выбранная страна: 🇷🇺 Россия" in message.caption and addb:
            await message.click(1, 0)
        elif '📱 Номер:' in message.caption and buy_acc:
            await app.send_message('WhooshScript_bot', message.caption)
    elif 'Отлично! Для пополнения Вашего баланса на' in message.text and addb:
        time.sleep(1)
        await app.send_message('WhooshScript_bot', await message.click(0))

    elif 'Выберите необходимый сервис из списка ниже.' in message.text and buy_acc:
        time.sleep(1)
        await message.click(0, 0)
    elif 'Заказ завершён.' in message.text or 'Вы вернулись в меню.' in message.text:
        pass
    elif '📱 Номер:' in message.text and buy_acc:
        await app.send_message('WhooshScript_bot', message.text)
    elif '🕰 Код:' in message.text:
        time.sleep(1)
        last_m.click(0)
        await app.send_message('WhooshScript_bot', message.text)
        buy_acc = False
        last_m = None
    elif 'Ваш счет был пополнен на' in message.text and addb:
        await app.send_message('WhooshScript_bot', 'Баланс успешно пополнен')
        addb = False
        last_m = None

    else:
        await app.send_message('WhooshScript_bot', message.text)


@app.on_message(filters.chat("WhooshScript_bot"))
async def check_chat1(client, message):
    global addb, last_m, buy_acc
    if message.text == "📱Купить аккаунт":
        await app.send_message("SMSBest_bot", 'Избранное')
        buy_acc = True
    elif message.text == "💳Пополнить баланс":
        await app.send_message("SMSBest_bot", 'Меню')
        addb = True
    elif message.text == 'Отмена':
        time.sleep(1)
        await last_m.click(len(last_m.reply_markup.inline_keyboard) - 1)
        addb = False
        last_m = None
    elif all([i in "1234567890" for i in list(message.text)]):
        await app.send_message('SMSBest_bot', message.text)
    elif last_m.caption:
        if message.text == 'Проверить платеж' and addb \
                and ('На какую сумму Вы хотите пополнить' not in last_m.caption):
            time.sleep(1)
            await last_m.click(0)
    elif last_m.text:
        if message.text == 'Проверить платеж' and addb \
                and (
                'На какую сумму Вы хотите пополнить' not in last_m.text):
            time.sleep(1)
            await last_m.click(0)


@app.on_edited_message(filters.chat("SMSBest_bot"))
async def check_change(client, update):
    global addb, last_m, buy_acc
    if update.reply_markup:
        last_m = update
        if update.caption:
            time.sleep(1)
            if 'Выберите способ пополнения баланса.' in update.caption and addb:
                await update.click(7)
            elif 'Выбранный сервис: Urent' in update.caption and buy_acc:
                await update.click(0, 0)
        elif 'Выбранный сервис: Urent' in update.text and buy_acc:
            await update.click(0, 0)


app.run()
