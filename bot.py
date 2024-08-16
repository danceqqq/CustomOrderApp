import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import sqlite3

logging.basicConfig(level=logging.INFO)

TOKEN = '7415395822:AAFbLJzeX9Q81zsCq76V_Nh0J-AEJgjhv2o'


async def start(update, context):
    keyboard = [
        [{"text": "Правила оформления", "callback_data": "rules"}],
        [{"text": "Оформить заказ", "callback_data": "order"}],
        [{"text": "Помощь", "callback_data": "help"}]
    ]
    await context.bot.send_message(chat_id=update.effective_chat.id, text='''
Привет! Я Тестовый бот для помощи в оформлении заказа.
Настоятельно рекомендую перед заказом ознакомиться с правилом оформления заказа, ведь если вы не правильно заполните форму заказа, он не дойдёт до приложения!
Используйте контекстные кнопки ниже, Для навигации :
''', reply_markup={"inline_keyboard": keyboard})


async def rules(update, context):
    keyboard = [
        [{"text": "Вернуться в начало", "callback_data": "start"}]
    ]
    await context.bot.send_message(chat_id=update.effective_chat.id, text='''
ᴛᴇᴋᴄᴛ нужно оɸоᴩʍᴧяᴛь ᴄᴛᴩоᴦо ᴨо ᴨᴩиʍᴇᴩу ᴄнизу.ᐟ
⌞ ᴨᴇᴩʙᴀя ᴄᴛᴩоᴋᴀ⌝
    ╰┈➤ᴛᴇʍᴀ зᴀᴋᴀзᴀ
⌞ ʙᴛоᴩᴀя и ᴨоᴄᴧᴇдующиᴇ ᴄᴛᴩоᴋи⌝
    ╰┈➤оᴨиᴄᴀниᴇ зᴀᴋᴀзᴀ
⌞ ʙᴧожᴇния⌝
   ╰┈➤ɸоᴛоᴦᴩᴀɸии  ✅
   ╰┈➤ᴦоᴧоᴄоʙыᴇ ❌
''', reply_markup={"inline_keyboard": keyboard})


async def order(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Пожалуйста, отправьте сообщение с описанием заказа в формате:\nТема заказа\nОписание заказа\nВы можете прикрепить фото к сообщению.')


async def help(update, context):
    keyboard = [
        [{"text": "Вернуться в начало", "callback_data": "start"}]
    ]
    await context.bot.send_message(chat_id=update.effective_chat.id, text='''
ᴨо ᴛᴇхничᴇᴄᴋиʍ ʙоᴨᴩоᴮᴀʍ
@ᴅᴀɴᴄᴇǫǫ
ᴨо ʙоᴨᴩоᴮᴀʍ зᴀᴋᴀзоʙ 
@ɴᴇsʜᴜᴍɪɪ
''', reply_markup={"inline_keyboard": keyboard})


async def button(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "rules":
        await rules(update, context)
    elif query.data == "order":
        await order(update, context)
    elif query.data == "help":
        await help(update, context)
    elif query.data == "start":
        await start(update, context)


def ensure_table_exists():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    # Создаем таблицу orders, если ее нет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            theme TEXT,
            description TEXT,
            order_number INTEGER
        )
    ''')

    # Проверяем, есть ли столбец image, и добавляем его, если нет
    cursor.execute("PRAGMA table_info(orders)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'image' not in columns:
        cursor.execute('ALTER TABLE orders ADD COLUMN image TEXT')

    conn.commit()
    conn.close()


async def handle_message(update, context):
    ensure_table_exists()
    text = update.message.text
    user_name = update.message.from_user.username
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(order_number) FROM orders')
    max_order_number = cursor.fetchone()[0]
    if max_order_number is None:
        order_number = 1
    else:
        order_number = max_order_number + 1
    lines = text.split('\n')
    theme = lines[0]
    description = '\n'.join(lines[1:])
    cursor.execute('INSERT INTO orders (user_name, theme, description, order_number) VALUES (?,?,?,?)',
                   (user_name, theme, description, order_number))
    conn.commit()
    conn.close()
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f'Ваш заказ №{order_number} успешно отправлен!')


async def handle_photo_and_text(update, context):
    ensure_table_exists()
    user_name = update.message.from_user.username

    # Инициализация переменной для хранения имени изображения
    image_name = None

    # Сохранение изображения
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        user_folder = os.path.join('orders', user_name)
        os.makedirs(user_folder, exist_ok=True)
        image_name = f'photo_{update.message.message_id}.jpg'
        photo_path = os.path.join(user_folder, image_name)
        await photo_file.download_to_drive(photo_path)
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Изображение успешно сохранено!')

    # Обработка текста, если он есть в сообщении
    if update.message.caption:
        text = update.message.caption
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(order_number) FROM orders')
        max_order_number = cursor.fetchone()[0]
        if max_order_number is None:
            order_number = 1
        else:
            order_number = max_order_number + 1
        lines = text.split('\n')
        theme = lines[0]
        description = '\n'.join(lines[1:])
        cursor.execute('INSERT INTO orders (user_name, theme, description, order_number, image) VALUES (?,?,?,?,?)',
                       (user_name, theme, description, order_number, image_name))
        conn.commit()
        conn.close()
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f'Ваш заказ №{order_number} успешно отправлен!')


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO | (filters.PHOTO & filters.TEXT), handle_photo_and_text))
    app.run_polling()


if __name__ == '__main__':
    main()
