import telebot
import time
from threading import Thread
from config import YOUR_BOT_TOKEN


bot = telebot.TeleBot(YOUR_BOT_TOKEN)

# Словарь для хранения пользователей, ожидающих прохождения капчи
pending_users = {}

# Функция удаления пользователя, если он не прошёл капчу
def kick_user_after_timeout(chat_id, user_id, message_id, timeout=20):
    time.sleep(timeout)
    if user_id in pending_users and pending_users[user_id]["chat_id"] == chat_id:
        try:
            # Удаляем сообщение с капчей
            bot.delete_message(chat_id, message_id)
            # Исключаем пользователя
            bot.ban_chat_member(chat_id, user_id)
            bot.unban_chat_member(chat_id, user_id)  # Разбан для возможности повторного вступления
            # Уведомляем группу
            bot.send_message(chat_id, f"Пользователь @{pending_users[user_id]['username']} не прошёл капчу и был удалён.")
        except Exception as e:
            print(f"Ошибка при удалении пользователя: {e}")
        finally:
            del pending_users[user_id]

# Обработка нового участника
@bot.message_handler(content_types=['new_chat_members'])
def new_member_handler(message):
    for user in message.new_chat_members:
        chat_id = message.chat.id
        user_id = user.id
        username = user.username or user.first_name

        # Отправляем сообщение с капчей
        captcha_message = bot.send_message(
            chat_id,
            f"Привет, @{username}! Нажмите на кнопку ниже, чтобы подтвердить, что вы не бот.",
            reply_markup=create_captcha_button(user_id)
        )

        # Сохраняем данные о пользователе
        pending_users[user_id] = {
            "chat_id": chat_id,
            "message_id": captcha_message.message_id,
            "username": username
        }

        # Запускаем таймер для удаления пользователя
        Thread(target=kick_user_after_timeout, args=(chat_id, user_id, captcha_message.message_id)).start()

# Создание кнопки капчи
def create_captcha_button(user_id):
    markup = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("Пройти капчу", callback_data=f"captcha:{user_id}")
    markup.add(button)
    return markup

# Обработка нажатия на кнопку капчи
@bot.callback_query_handler(func=lambda call: call.data.startswith("captcha:"))
def captcha_callback_handler(call):
    user_id = int(call.data.split(":")[1])
    chat_id = call.message.chat.id

    # Проверяем, что кнопку нажал тот же пользователь
    if call.from_user.id == user_id:
        try:
            # Удаляем сообщение с капчей
            bot.delete_message(chat_id, call.message.message_id)
            # Удаляем данные пользователя из словаря
            del pending_users[user_id]
            # Приветствуем пользователя
            bot.send_message(chat_id, f"Добро пожаловать, @{call.from_user.username or call.from_user.first_name}!")
        except Exception as e:
            print(f"Ошибка при обработке капчи: {e}")
    else:
        bot.answer_callback_query(call.id, "Это сообщение не для вас!", show_alert=True)

# Запуск бота
if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)
