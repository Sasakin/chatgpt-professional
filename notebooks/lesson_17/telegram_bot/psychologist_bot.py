import os
from dotenv import load_dotenv   
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

load_dotenv('.env')
MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]
TOKEN = os.environ["BOT_TOKEN"]

# Создание папки для хранения записей
if not os.path.exists("appointments"):
    os.makedirs("appointments")

# Главное меню
MAIN_MENU = {
    "ru": {
        "greeting": "Добро пожаловать! Я помогу вам записаться на консультацию к психологу.",
        "buttons": [
            {"text": "О психологе", "callback_data": "about"},
            {"text": "Услуги", "callback_data": "services"},
            {"text": "Записаться", "callback_data": "book"},
            {"text": "Контакты", "callback_data": "contacts"},
        ],
    },
}

# Информация о психологе
ABOUT_PSYCHOLOGIST = {
    "ru": (
        "👩‍💼 О психологе:\n"
        "Имя: Анна Иванова\n"
        "Опыт: 10 лет\n"
        "Специализация: стресс, тревожность, отношения.\n"
        "Образование: Московский государственный университет."
    ),
}

# Услуги
SERVICES = {
    "ru": (
        "📋 Наши услуги:\n"
        "1. Индивидуальная консультация — 2000 рублей\n"
        "2. Пара-консультация — 3000 рублей\n"
        "3. Групповая терапия — 1500 рублей"
    ),
}

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(button["text"], callback_data=button["callback_data"])]
        for button in MAIN_MENU["ru"]["buttons"]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(MAIN_MENU["ru"]["greeting"], reply_markup=reply_markup)

# Обработчик нажатия на кнопки главного меню
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "about":
        await query.edit_message_text(text=ABOUT_PSYCHOLOGIST["ru"])
    elif query.data == "services":
        await query.edit_message_text(text=SERVICES["ru"])
    elif query.data == "book":
        await query.edit_message_text(text="Выберите дату и время:")
        # Здесь можно добавить inline-кнопки с доступными слотами времени
    elif query.data == "contacts":
        await query.edit_message_text(text="📞 Контакты:\nТелефон: +7-XXX-XXX-XXXX\nEmail: example@example.com")

# Обработчик текстовых сообщений
async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я не понимаю ваш запрос. Пожалуйста, используйте кнопки меню.")

def main():
    # Создание приложения
    application = ApplicationBuilder().token(TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(menu_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))

    # Запуск бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()