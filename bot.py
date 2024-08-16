import logging
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

logging.basicConfig(level=logging.INFO)

TOKEN = '7415395822:AAFbLJzeX9Q81zsCq76V_Nh0J-AEJgjhv2o'

# Функция для создания таблицы в базе данных
def ensure_table_exists():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            theme TEXT,
            description TEXT,
            order_number INTEGER,
            status TEXT DEFAULT 'Working'  -- Добавляем столбец для состояния заказа
        )
    ''')

    cursor.execute("PRAGMA table_info(orders)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'image' not in columns:
        cursor.execute('ALTER TABLE orders ADD COLUMN image TEXT')

    conn.commit()
    conn.close()


# Функция для начала работы с ботом
async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Правила оформления 📖", callback_data="rules")],
        [InlineKeyboardButton("Оформить заказ 🛒", callback_data="order")],
        [InlineKeyboardButton("Помощь ❓", callback_data="help")],
        [InlineKeyboardButton("Поиск по номеру 🔎", callback_data="search")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text='''
Привет! Я Тестовый бот для помощи в оформлении заказа.
Настоятельно рекомендую перед заказом ознакомиться с правилом оформления заказа, ведь если вы не правильно заполните форму заказа, он не дойдёт до приложения!
Используйте контекстные кнопки ниже для навигации:
''', reply_markup=reply_markup)


# Функция, выводящая правила оформления заказа
async def rules(update, context):
    keyboard = [
        [InlineKeyboardButton("Вернуться в начало", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text='''
ᴛᴇᴋᴄᴛ нужно оɸоᴩʍᴧяᴛь ᴄᴛᴩоᴦо ᴨо ᴨᴩиʍᴇᴩу ᴄнизу.ᐟ
⌞ ᴨᴇᴩʙᴀя ᴄᴛᴩоᴋᴀ⌝
    ╰┈➤ᴛᴇʍᴀ зᴀᴋᴀзᴀ
⌞ ʙᴛоᴩᴀя и ᴨоᴄᴧᴇдующиᴇ ᴄᴛᴩоᴋи⌝
    ╰┈➤оᴨиᴄᴀниᴇ зᴀᴋᴀзᴀ
⌞ ʙᴧожᴇния⌝
   ╰┈➤ɸоᴛоᴦᴩᴀɸии  ✅
   ╰┈➤ᴦоᴧоᴄоʙыᴇ ❌
''', reply_markup=reply_markup)


# Функция для оформления заказа
async def order(update, context):
    keyboard = [
        [InlineKeyboardButton("Вернуться", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Пожалуйста, отправьте сообщение с описанием заказа в формате:\nТема заказа\nОписание заказа\nВы можете прикрепить фото к сообщению.',
                                   reply_markup=reply_markup)
    context.user_data['can_submit_order'] = True  # Разрешаем отправку заказа


# Функция помощи
async def help(update, context):
    keyboard = [
        [InlineKeyboardButton("Вернуться в начало", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text='''
ᴨо ᴛᴇхничᴇᴄᴋиʍ ʙоᴨᴩоᴮᴀʍ
@ᴅᴀɴᴄᴇǫǫ
ᴨо ʙоᴨᴩоᴄᴀʍ зᴀᴋᴀзоʙ 
@ɴᴇsʜᴜᴍɪɪ
''', reply_markup=reply_markup)


# Функция для поиска заказа по номеру
async def search_order(update, context):
    keyboard = [
        [InlineKeyboardButton("Вернуться", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Пожалуйста, введите номер заказа, который вы хотите найти:',
                                   reply_markup=reply_markup)
    context.user_data['waiting_for_order_number'] = True  # Устанавливаем состояние для ожидания ввода номера заказа


# Функция обработки номера заказа
async def handle_order_number(update, context):
    order_number = update.message.text
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_name, theme, description, status FROM orders WHERE order_number = ?', (order_number,))
    order = cursor.fetchone()

    if order:
        user_name, theme, description, status = order
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f'Заказ №{order_number}\n'
                                            f'Пользователь: @{user_name}\n'
                                            f'Тема: {theme}\n'
                                            f'Описание: {description}\n'
                                            f'Статус: {status}')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f'Заказ с номером {order_number} не найден.')

    conn.close()
    context.user_data['waiting_for_order_number'] = False  # Сбрасываем состояние ожидания номера заказа


# Функция для обработки текстовых сообщений
async def handle_message(update, context):
    ensure_table_exists()
    if context.user_data.get('waiting_for_order_number'):
        await handle_order_number(update, context)
    elif context.user_data.get('can_submit_order'):
        text = update.message.text
        user_name = update.message.from_user.username
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()

        # Генерация случайного 5-значного номера заказа
        order_number = random.randint(10000, 99999)

        # Разделение сообщения на тему и описание
        lines = text.split('\n')
        theme = lines[0]
        description = '\n'.join(lines[1:])
        cursor.execute('INSERT INTO orders (user_name, theme, description, order_number) VALUES (?,?,?,?)',
                       (user_name, theme, description, order_number))
        conn.commit()
        conn.close()
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f'Ваш заказ №{order_number} успешно отправлен!')
        context.user_data['can_submit_order'] = False  # Сбрасываем флаг разрешения отправки заказа
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Пожалуйста, нажмите "Оформить заказ", чтобы отправить заказ.')


# Функция для обработки нажатий на кнопки
async def button(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "rules":
        await rules(update, context)
    elif query.data == "order":
        await order(update, context)
    elif query.data == "help":
        await help(update, context)
    elif query.data == "search":
        context.user_data['waiting_for_order_number'] = False  # Убираем флаг ожидания номера заказа, если пользователь вернулся
        await search_order(update, context)
    elif query.data == "start":
        context.user_data['waiting_for_order_number'] = False  # Убираем флаг ожидания номера заказа, если пользователь вернулся
        await start(update, context)


# Основная программа
if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    # Обработчик команды /start
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # Обработчик кнопок
    button_handler = CallbackQueryHandler(button)
    application.add_handler(button_handler)

    # Обработчик текстовых сообщений
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(message_handler)

    # Запуск бота
    application.run_polling()
