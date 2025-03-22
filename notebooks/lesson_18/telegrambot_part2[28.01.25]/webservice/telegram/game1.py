# Пример игры №1

# импорт модулей
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
import os
import requests
import aiohttp
import base64

# загружаем переменные окружения
load_dotenv()

# токен бота
TOKEN = os.getenv('TG_TOKEN')

# создание клавиатуры для старта игры
buttons_start = [InlineKeyboardButton('Загадал', callback_data = 'start')]
frame_start = [[buttons_start[0]]]
inline_start = InlineKeyboardMarkup(frame_start)

# создание клавиатуры для игры
buttons_menu = [
    InlineKeyboardButton('Да', callback_data = 'yes'),
    InlineKeyboardButton('Ты угадал', callback_data = 'ready'),
    InlineKeyboardButton('Сначала', callback_data = 'begin'),
    InlineKeyboardButton('Нет', callback_data = 'no')
]
frame_menu = [[buttons_menu[0], buttons_menu[1], buttons_menu[2], buttons_menu[3]]]
inline_menu = InlineKeyboardMarkup(frame_menu)

# функция-обработчик команды /start
async def start(update, context):

    # сообщение пользователю
    message  = 'Привет! Это игра, в которой бот угадывает слово.'
    message += ' Для начала игры нажмите /game.'
    message += ' Игра заканчивается, когда бот угадает слово'
    await update.message.reply_text(message)
    
# функция-обработчик команды /game
async def game(update, context):

    # очистка истории сообщений
    user_id = update.message.from_user.id
    context.bot_data[user_id] = {}
    context.bot_data[user_id]['is_start'] = True
    context.bot_data[user_id]['history'] = ''

    # сообщение пользователю
    await update.message.reply_text('Игра началась! Загадайте слово', reply_markup=inline_start)    

# функция-обработчик текстовых сообщений
async def text(update, context):

    # если игра не началась
    user_id = update.message.from_user.id
    is_start = False
    if 'is_start' in context.bot_data[user_id]:
        if context.bot_data[user_id]['is_start']: is_start = True
    if not is_start:
        message += ' Для начала игры нажмите /game.'
        await update.message.reply_text(message)
        
    # сообщение пользователю
    first_message = await update.message.reply_text('Минуту...')

    # запрос в API
    context.bot_data[user_id]['history'] += '\nUser: ' + update.message.text
    answer = await query_api(context.bot_data[user_id]['history'])
    
    # ответ пользователю
    context.bot_data[user_id]['history'] += '\nBot: ' + answer
    await first_message.edit_text(answer, reply_markup=inline_menu)
                    
# Функция обращается к API с запросом
#   history - история диалога
# Возвращает ответ от API
async def query_api(history):
    
    # формируем промпт
    system = 'ты угадываешь слова по наводящим вопросам'
    user = f'''
        Ты пытаешься угадать слово, загаданное пользователем.\n
        Если ты готов назвать слово, то назови, иначе задай наводящий вопрос.\n
        Вот ваш диалог {history}.\n
    '''
    print(f'\n{history}\n')
    # обращение к API
    param = {
        'system': system,
        'user': user,
        'temperature': 0.5
    }    
    async with aiohttp.ClientSession() as session:
        async with session.post('http://127.0.0.1:8000/request', json = param) as response:
            # получение ответа от API
            answer = await response.json()
            # ответ пользователю
            return answer['message']
        
# функция-обработчик нажатий на кнопки
async def button(update: Update, context):

    # получаем callback query из update
    query = update.callback_query  
    user_id = query.from_user.id
        
    # обработка кнопок "Загадал", "Да", "Нет", "Ты угадал"
    if query.data in {'yes', 'no', 'ready', 'start'}:
    
        # отправляем сообщение об ожидании
        first_message = await context.bot.send_message(chat_id=user_id, text='Минуту...')        
                
        # запрос в API
        message = ''
        if query.data == 'yes': message = 'Да'
        if query.data == 'no': message = 'Нет'
        if query.data == 'ready': message = 'Ты угадал слово!'
        if query.data == 'start': message = 'Я загадал слово!'        
        context.bot_data[user_id]['history'] += '\nUser: ' + message
        answer = await query_api(context.bot_data[user_id]['history'])        
        
        # ответ пользователю
        context.bot_data[user_id]['history'] += '\nBot: ' + answer
        await first_message.edit_text(answer, reply_markup=inline_menu)
        
        # Завершение обработки callback
        await query.answer()        
        
        # выход
        return
    
    # обработка кнопки "С начала"
    if query.data == 'begin':
        
        # очистка истории сообщений
        context.bot_data[user_id] = {}
        context.bot_data[user_id]['is_start'] = True
        context.bot_data[user_id]['history'] = ''

        # сообщение пользователю
        await context.bot.send_message(chat_id=user_id, text = 'Игра началась! Загадайте слово', reply_markup=inline_start)   
        
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

    # добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT, text))

    # запускаем бота (нажать Ctrl-C для остановки бота)
    print('Бот запущен...')    
    application.run_polling()
    print('Бот остановлен')

# проверяем режим запуска модуля
if __name__ == "__main__":      # если модуль запущен как основная программа

    # запуск бота
    main()