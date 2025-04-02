import os
import logging
from telethon import TelegramClient
import tiktoken
import logging
import tempfile
import asyncio
import requests
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
from mistralai import Mistral      
from dotenv import load_dotenv   
from telegram import Update
from telegram.ext import ContextTypes
import io
from urllib.parse import urlparse, unquote
from pydub import AudioSegment

# Настройка логирования
# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv('.env')
MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]
# Установка токенов
TELEGRAM_BOT_TOKEN = os.environ["BOT_TOKEN"]

# Путь для временных файлов
TEMP_DIR = "temp"

def setup_temp_dir():
    """Создание временной папки"""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        logger.info(f"Создана папка {TEMP_DIR}")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет!")

# Обработчик голосовых сообщений
async def voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик URL"""
    message = update.message
    text = message.text.strip()

    # Проверка URL
    if not text.startswith("http"):
        await message.reply_text("Это не ссылка. Введите URL, начинающийся с http:// или https://")
        return

    # Создаем временную папку
    setup_temp_dir()

    try:
        # Преобразуем ссылку Google Drive (если нужно)
        parsed_url = urlparse(text)
        if "drive.google.com" in parsed_url.netloc and "/file/d/" in parsed_url.path:
            # Преобразуем ссылку вида /view в /uc?export=download
            file_id = parsed_url.path.split("/")[3]  # Извлекаем ID файла
            url = f"https://drive.google.com/uc?export=download&id={file_id}"
        else:
            url = text

        # Загрузка файла
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()

        # Получаем имя файла
        filename = get_filename_from_response(response, url)
        if not filename:
            await message.reply_text("Не удалось определить имя файла. Проверьте URL.")
            return

        # Формируем путь к файлу
        file_path = os.path.join(TEMP_DIR, filename)

        # Скачивание файла
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Отправляем файл обратно
        #with open(file_path, 'rb') as file:
            #await message.reply_audio(audio=file, filename=filename)

        audio_path = file_path
        file_title = "text"
        save_folder_path = "transcribe/"

        transcribe_audio_whisper_chunked(audio_path, file_title, save_folder_path)    

        # Удаляем временный файл
        os.remove(file_path)
        logger.info(f"Файл {filename} успешно обработан и удален")

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при скачивании: {str(e)}")
        await message.reply_text("Не удалось скачать файл. Проверьте ссылку и попробуйте снова.")
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {str(e)}")
        await message.reply_text("Произошла ошибка. Попробуйте позже.")

def get_filename_from_response(response, url):
    """Получаем имя файла из HTTP-заголовков или URL"""
    # Проверяем заголовок Content-Disposition
    content_disposition = response.headers.get('Content-Disposition')
    if content_disposition:
        filename_start = content_disposition.find("filename=")
        if filename_start != -1:
            filename = content_disposition[filename_start + 10:].strip('";')
            return unquote(filename)  # Декодируем URL-кодировку

    # Если заголовок отсутствует, извлекаем имя из URL
    parsed_url = urlparse(url)
    path = unquote(parsed_url.path)
    filename = os.path.basename(path)
    
    # Если имя пустое или не подходит (например, для Google Drive)
    if not filename or filename == "uc":
        # Для Google Drive устанавливаем имя по умолчанию
        if "drive.google.com" in parsed_url.netloc:
            return "audio_file.m4a"  # Используем расширение M4A по умолчанию
        else:
            return None

    return filename

# Функция для обработки ошибок
def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update {update} caused error {context.error}')

from faster_whisper import WhisperModel
import whisper
import os
import torch
from pydub import AudioSegment
from transformers import WhisperProcessor, WhisperForConditionalGeneration

def transcribe_audio_whisper_chunked(audio_path, file_title, save_folder_path, max_duration=5 * 60 * 1000):  # 5 минут
    """
    Функция для транскрибации аудиофайла на части, чтобы соответствовать ограничениям размера API.
    """

    # Создание папки для сохранения результатов, если она ещё не существует
    os.makedirs(save_folder_path, exist_ok=True)

    # Загрузка аудиофайла
    audio = AudioSegment.from_file(audio_path)

    # Создание временной папки для хранения аудио чанков (фрагментов)
    temp_dir = os.path.join(save_folder_path, "temp_audio_chunks")
    os.makedirs(temp_dir, exist_ok=True)

    # Инициализация переменных для обработки аудио чанков
    current_start_time = 0  # Текущее время начала чанка
    chunk_index = 1         # Индекс текущего чанка
    transcriptions = []     # Список для хранения всех транскрибаций

    # Загрузка модели и процессора
    processor = WhisperProcessor.from_pretrained("openai/whisper-large-v3")
    model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-large-v3")

    # Обработка аудиофайла чанками
    while current_start_time < len(audio):
        # Выделение чанка из аудиофайла
        chunk = audio[current_start_time:current_start_time + max_duration]
        # Формирование имени и пути файла чанка
        chunk_name = f"chunk_{chunk_index}.wav"
        chunk_path = os.path.join(temp_dir, chunk_name)
        # Экспорт чанка в формате wav
        chunk.export(chunk_path, format="wav")

        # Проверка размера файла чанка на соответствие лимиту API
        if os.path.getsize(chunk_path) > 26214400:  # 25 MB
            print(f"Chunk {chunk_index} exceeds the maximum size limit for the API. Trying a smaller duration...")
            max_duration = int(max_duration * 0.9)  # Уменьшение длительности чанка на 10%
            os.remove(chunk_path)  # Удаление чанка, превышающего лимит
            continue

        # Загрузка аудио чанка
        chunk_audio = AudioSegment.from_file(chunk_path)
        chunk_audio = chunk_audio.set_frame_rate(16000).set_channels(1)
        audio_array = torch.tensor(chunk_audio.get_array_of_samples(), dtype=torch.float32).unsqueeze(0)

        # Предобработка аудиофайла
        inputs = processor(audio_array.numpy(), sampling_rate=16000, return_tensors="pt")

        # Транскрибирование с переводом на английский
        # Если attention_mask не создается автоматически, создайте его вручную
        if 'attention_mask' not in inputs:
            inputs['attention_mask'] = torch.ones_like(inputs['input_features'])

        # Транскрибирование с переводом на английский
        generated_ids = model.generate(inputs["input_features"], max_length=500, language='ru')
        transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        # Добавление результата транскрибации в список транскрипций
        transcriptions.append(transcription)
        print(transcription)

        # Удаление обработанного файла чанка
        os.remove(chunk_path)
        # Переход к следующему чанку
        current_start_time += max_duration
        chunk_index += 1

    # Удаление временной папки с чанками
    os.rmdir(temp_dir)

    # Сохранение всех транскрипций в один текстовый файл
    result_path = os.path.join(save_folder_path, f"{file_title}.txt")
    with open(os.path.join(save_folder_path, f"{file_title}.txt"), "w") as f:
        f.write("\n".join(transcriptions))
    #with open(result_path, "w") as txt_file:
     #   txt_file.write("\n".join(transcriptions))

    print(f"Transcription saved to {result_path}")    

# Основная функция
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VOICE, voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    #application.add_handler(MessageHandler(filters.AUDIO, handle_audio))

    # Регистрируем обработчик ошибок
    application.add_error_handler(error)

    # Запуск бота
    application.run_polling()