import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import YOUR_BOT_TOKEN, YOUR_BOT_URL
import threading

# Замените 'YOUR_BOT_TOKEN' на токен вашего бота
bot = telebot.TeleBot(YOUR_BOT_TOKEN)

# Словарь для хранения информации о пользователях, ожидающих капчу
user_data = {}

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id

    # Кнопка "Пройти капчу"
    captcha_button = InlineKeyboardMarkup()
    captcha_button.add(InlineKeyboardButton("Пройти капчу", callback_data="captcha"))

    # Сообщение с кнопкой
    captcha_message = bot.send_message(
        chat_id,
        "Для продолжения необходимо пройти капчу. Нажмите на кнопку ниже в течение 20 секунд.",
        reply_markup=captcha_button
    )

    # Сохранение информации о пользователе
    user_data[chat_id] = {
        "captcha_message_id": captcha_message.message_id,
        "passed": False
    }

    # Запуск таймера на 20 секунд
    threading.Timer(20, check_captcha_timeout, args=(chat_id,)).start()

# Проверка нажатия кнопки "Пройти капчу"
@bot.callback_query_handler(func=lambda call: call.data == "captcha")
def handle_captcha(call):
    chat_id = call.message.chat.id
    user = user_data.get(chat_id)

    if user and not user["passed"]:
        # Пользователь успел пройти капчу
        bot.delete_message(chat_id, user["captcha_message_id"])
        bot.send_message(chat_id, "Вы успешно прошли капчу!")

        # Кнопка "Вступить в группу"
        group_button = InlineKeyboardMarkup()
        group_button.add(InlineKeyboardButton("Вступить в группу", url=YOUR_BOT_URL))

        bot.send_message(chat_id, "Нажмите на кнопку ниже, чтобы вступить в группу.", reply_markup=group_button)

        # Отметить, что пользователь прошёл капчу
        user_data[chat_id]["passed"] = True

# Функция проверки таймера
def check_captcha_timeout(chat_id):
    user = user_data.get(chat_id)

    if user and not user["passed"]:
        # Удалить сообщение с кнопкой
        bot.delete_message(chat_id, user["captcha_message_id"])

        # Сообщение о том, что время истекло
        bot.send_message(chat_id, "Вы не успели пройти капчу. Попробуйте снова, нажав /start.")

        # Удалить пользователя из данных
        user_data.pop(chat_id, None)

# Запуск бота
bot.polling()
