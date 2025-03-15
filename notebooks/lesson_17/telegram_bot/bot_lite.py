from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv   

# получим переменные окружения из .env
load_dotenv('.env')
MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]
TOKEN = os.environ["BOT_TOKEN"]

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать, мой дорогой друг!")

# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Этот бот предназначен для обучения! ⚠️")

# Обработчик текстовых сообщений
async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Текст, текст, текст…")

def main():
    # Создание приложения
    application = ApplicationBuilder().token(TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))

    # Запуск бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()