# Пример игры №2

# импорт модулей
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
import os
import requests
import aiohttp
import base64
import json

# загружаем переменные окружения
load_dotenv()

# токен бота
TOKEN = os.getenv('TG_TOKEN')

# создание клавиатуры "Продолжить"
buttons_cont = [
    InlineKeyboardButton('Продолжить', callback_data = 'cont')
]
frame_cont = [[buttons_cont[0]]]
inline_cont = InlineKeyboardMarkup(frame_cont)

# создание клавиатуры ответа
buttons_menu = [
    InlineKeyboardButton('Правда', callback_data = 'yes'),
    InlineKeyboardButton('Не правда', callback_data = 'no')
]
frame_menu = [[buttons_menu[0], buttons_menu[1]]]
inline_menu = InlineKeyboardMarkup(frame_menu)

# функция-обработчик команды /start
async def start(update, context):

    # сообщение пользователю
    message  = 'Привет! Это игра, в которой бот задает вопрос,'
    message += ' участник отвечает - правда это или нет'
    message += ' Для начала игры введите /game.'
    await update.message.reply_text(message)
    
# функция-обработчик команды /game
async def game(update, context):

    # очистка истории 
    user_id = update.message.from_user.id
    context.bot_data[user_id] = {}
    context.bot_data[user_id]['answers'] = []
    context.bot_data[user_id]['history'] = []
    
    # сообщение пользователю
    first_message = await update.message.reply_text('Минуту...')    
    
    # формирование вопроса
    quest = await query_api([]) 

    # сообщение пользователю
    context.bot_data[user_id]['answers'].append(quest['answer'])
    context.bot_data[user_id]['history'].append(quest['question'])
    await first_message.edit_text(quest['question'], reply_markup=inline_menu)    
                   
# Функция обращается к API с запросом
#   history - история диалога в виде списка
# Возвращает ответ от API в виде словаря {'question': str, 'answer': bool}
async def query_api(history):
    
    # формируем промпт
    system = 'Ты задаешь вопросы участникам чата'
    hist = ' '.join(history)
    user = 'Придумай один шуточный или серьезный вопрос для викторины на предмет "правда или ложь". Пользователи чата должны угадать правда это или нет. '
    user += 'Но вопросы не должны быть слишком очевидными (например очевидный: человек умеет летать?).\n'
    user += 'Не начинай вопрос с "В некоторых странах"'
    user += 'Верни результат в формате JSON: {"question": str, "answer": bool}'
    user += f'Не повторяй слова из истории: {hist}.\n'

    # обращение к API
    param = {
        'system': system,
        'user': user,
        'temperature': 0.5,
        'format': { "type": "json_object" }
    }    
    async with aiohttp.ClientSession() as session:
        async with session.post('http://127.0.0.1:8000/request', json = param) as response:
            # получение ответа от API
            answer = await response.json()
            # ответ пользователю
            return json.loads(answer['message'])
        
# функция-обработчик нажатий на кнопки
async def button(update: Update, context):

    # получаем callback query из update
    query = update.callback_query  
    user_id = query.from_user.id
        
    # обработка кнопок "Правда", "Не правда"
    if query.data in {'yes', 'no'}:
    
        # проверка ответа
        answer_user = True if query.data == 'yes' else False
        answer_right = context.bot_data[user_id]['answers'][-1]
        message = 'Вы совершенно правы!' if answer_user == answer_right else 'Вы не угадали'
        
        # сообщение пользователю
        await context.bot.send_message(chat_id=user_id, text = message, reply_markup=inline_cont)    
        
        # завершение обработки callback
        await query.answer()        
        
        # выход
        return
    
    # обработка кнопки "Продолжить"
    if query.data == 'cont':

        # отправляем сообщение об ожидании
        first_message = await context.bot.send_message(chat_id=user_id, text='Минуту...')
              
        # формирование вопроса
        quest = await query_api(context.bot_data[user_id]['history'])    

        # сообщение пользователю
        context.bot_data[user_id]['answers'].append(quest['answer'])
        context.bot_data[user_id]['history'].append(quest['question'])
        await first_message.edit_text(quest['question'], reply_markup=inline_menu)
        
        # Завершение обработки callback
        await query.answer()        
        
        # выход
        return 

# функция "Запуск бота"
def main():

    # создаем приложение и передаем в него токен
    application = Application.builder().token(TOKEN).build()

    # добавляем обработчик команды /start
    application.add_handler(CommandHandler('start', start))
    
    # добавляем обработчик команды /game
    application.add_handler(CommandHandler('game', game))    
    
    # добавляем CallbackQueryHandler (для inline кнопок)
    application.add_handler(CallbackQueryHandler(button))    

    # запускаем бота (нажать Ctrl-C для остановки бота)
    print('Бот запущен...')    
    application.run_polling()
    print('Бот остановлен')

# проверяем режим запуска модуля
if __name__ == "__main__":      # если модуль запущен как основная программа

    # запуск бота
    main()