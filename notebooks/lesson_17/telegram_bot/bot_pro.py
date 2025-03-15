import os
from dotenv import load_dotenv   
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

load_dotenv('.env')
MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]
TOKEN = os.environ["BOT_TOKEN"]

# Создание папки для сохранения фотографий
if not os.path.exists("photos"):
    os.makedirs("photos")

# Словарь для хранения языковых настроек пользователей
user_language = {}

# Языковые настройки
LANGUAGES = {
    "ru": {
        "start_message": "Выберите язык интерфейса:",
        "text_received": "Текстовое сообщение получено!",
        "voice_received": "Голосовое сообщение получено",
        "photo_saved": "Фотография сохранена",
    },
    "en": {
        "start_message": "Choose interface language:",
        "text_received": "We’ve received a message from you!",
        "voice_received": "We’ve received a voice message from you!",
        "photo_saved": "Photo saved!",
    },
}

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Русский", callback_data="ru")],
        [InlineKeyboardButton("English", callback_data="en")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(LANGUAGES["ru"]["start_message"], reply_markup=reply_markup)

# Обработчик нажатия на inline-кнопку
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    selected_language = query.data

    # Сохраняем выбранный язык
    user_language[user_id] = selected_language
    await query.answer()

    # Отправляем подтверждение выбора языка
    lang = LANGUAGES[selected_language]
    await query.edit_message_text(text=f"{lang['text_received']}")

# Обработчик текстовых сообщений
async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = LANGUAGES[user_language.get(user_id, "ru")]  # По умолчанию русский язык
    await update.message.reply_text(lang["text_received"])

# Обработчик голосовых сообщений
async def voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = LANGUAGES[user_language.get(user_id, "ru")]  # По умолчанию русский язык

    # Отправляем картинку с подписью
    photo_path = "photos/AQADge4xGxwIgUp-.jpg"  # Укажите путь к вашей картинке
    with open(photo_path, "rb") as photo:
        await update.message.reply_photo(photo, caption=lang["voice_received"])

# Обработчик фотографий
async def photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = LANGUAGES[user_language.get(user_id, "ru")]  # По умолчанию русский язык

    # Сохраняем фотографию в папку photos
    photo_file = await update.message.photo[-1].get_file()
    file_name = f"photos/{photo_file.file_unique_id}.jpg"
    await photo_file.download_to_drive(file_name)

    # Отправляем подтверждение
    await update.message.reply_text(lang["photo_saved"])

def main():
    # Создание приложения
    application = ApplicationBuilder().token(TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    application.add_handler(MessageHandler(filters.VOICE, voice_message))
    application.add_handler(MessageHandler(filters.PHOTO, photo_message))

    # Запуск бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()