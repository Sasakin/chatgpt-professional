import os
import logging
from telethon import TelegramClient
import tiktoken
import asyncio
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from mistralai import Mistral      
from dotenv import load_dotenv   
from telegram import Update
from telegram.ext import ContextTypes
import io

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

load_dotenv('.env')
MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]
# Установка токенов
TELEGRAM_BOT_TOKEN = os.environ["BOT_TOKEN"]

api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')

client = TelegramClient('session_name', api_id, api_hash)

def split_text_into_chunks(text: str, max_tokens: int, model_name: str = "gpt-3.5-turbo") -> list:
    """
    Разделяет текст на части, каждая из которых содержит не более max_tokens.
    """
    # Инициализация токенизатора
    tokenizer = tiktoken.encoding_for_model(model_name)

    # Токенизация текста
    tokens = tokenizer.encode(text)

    # Разбиение на части
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)

    return chunks

# Функция для получения постов из канала за последний месяц
async def fetch_channel_posts(channel_username: str):
    try:
        # Подключаемся к Telegram
        await client.start()

        # Получаем текущую дату и дату месяц назад с учетом часового пояса
        now = datetime.now(timezone.utc)  # Текущее время в UTC
        one_month_ago = now - timedelta(days=30)

        # Список для хранения постов
        posts = []

                # Получаем последние сообщения из канала
        async for message in client.iter_messages(channel_username, reverse=False, limit=1000):
            # Проверяем дату сообщения
            if message.date >= one_month_ago:
                # Добавляем текст сообщения, если он существует
                if message.text:
                    posts.append(message.text)
            else:
                break  # Если сообщение старше месяца, прекращаем сбор

        # Явная проверка перед возвратом
        if not posts:
            logging.warning("Не найдено ни одного поста за последний месяц.")
        
        return posts

    except Exception as e:
        logging.error(f"Ошибка при получении постов: {e}")
        return []
    finally:
        logging.info("Завершение функции fetch_channel_posts")

# Функция для отправки запроса в LLM-модель
def generate_investment_recommendation(posts_text: str, max_tokens_per_chunk: int = 20000) -> str:
    """
    Генерирует инвестиционную рекомендацию, разбивая текст на части и объединяя результаты.
    """
    # Разбиваем текст на части
    chunks = split_text_into_chunks(posts_text, max_tokens=max_tokens_per_chunk)

    # Список для хранения ответов модели
    responses = []

    # Отправляем каждую часть в модель
    for i, chunk in enumerate(chunks):
        logging.info(f"Обработка части {i + 1} из {len(chunks)}")
        prompt = f"""
                На основе следующих постов из инвестиционного канала за последний месяц, составь краткую инвестиционную рекомендацию:
                {chunk}
                """
        clientMistral = Mistral(MISTRAL_API_KEY)

        try:
            response = clientMistral.chat.complete(
                model="mistral-small-latest",   
                messages=[
                    {"role": "system", "content": "Ты финансовый аналитик. Твоя задача — анализировать текстовые данные и давать инвестиционные рекомендации."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0 
            )
            responses.append(response.choices[0].message.content)
        except Exception as e:
            logging.error(f"Ошибка при работе с OpenAI: {e}")
            responses.append("Не удалось получить рекомендацию для части.")

    # Объединяем результаты
    final_recommendation = "\n".join(responses)
    return final_recommendation

def generate_summary(text: str) -> str:
    """
    Генерирует краткую сводку (summary) из текста.
    """
    clientMistral = Mistral(MISTRAL_API_KEY)
    try:
        response = clientMistral.chat.complete(
            model="mistral-small-latest",  
            messages=[
                {"role": "system", "content": "Проанализируй текст и объедини его в единое сообщение не больше 4000 символов"},
                {"role": "user", "content": text}
            ],
            max_tokens=4000
        )
        summary = response.choices[0].message.content
        return summary
    except Exception as e:
        logging.error(f"Ошибка при создании сводки: {e}")
        return "Не удалось создать сводку."


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправьте мне ссылку на инвестиционный канал, чтобы я мог проанализировать его посты за последний месяц.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_username = update.message.text.strip()

    # Проверяем, что это ссылка на канал
    if not channel_username.startswith('@'):
        await update.message.reply_text("Пожалуйста, отправьте корректное имя канала, начинающееся с '@'.")
        return

    await update.message.reply_text(f"Анализирую посты из канала {channel_username} за последний месяц...")

    # Получаем посты
    posts = await fetch_channel_posts(channel_username)
    if not posts:
        await update.message.reply_text("Не удалось найти посты за последний месяц.")
        return

    # Объединяем текст постов
    posts_text = "\n".join(posts)

    # Генерируем рекомендацию
    recommendation = generate_investment_recommendation(posts_text)

    # Проверяем длину текста
    if len(recommendation) > 4096:
        # Если текст слишком длинный, отправляем его в виде файла
        await send_text_as_file(update, context, recommendation, filename="summary.txt")
        await update.message.reply_text("Сводка была отправлена в виде текстового файла.")
    else:
        summary = generate_summary(recommendation)
        # Иначе отправляем текстовое сообщение
        await update.message.reply_text(f"Краткая инвестиционная рекомендация:\n\n{summary}")

async def send_text_as_file(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, filename: str = "recommendation.txt"):
    """
    Отправляет текст пользователю в виде текстового файла.
    """
    # Создаем файловый объект в памяти
    file = io.BytesIO(text.encode('utf-8'))
    file.name = filename  # Устанавливаем имя файла

    # Отправляем файл пользователю
    await update.message.reply_document(document=file)

# Основная функция
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()