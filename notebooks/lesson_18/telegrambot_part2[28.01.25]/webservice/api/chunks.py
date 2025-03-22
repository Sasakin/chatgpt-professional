# импорт библиотек
from dotenv import load_dotenv                              # работа с переменными окружения
import os                                                   # взаимодействие с операционной системой
from openai import OpenAI                                   # взаимодействие с OpenAI API
from openai import AsyncOpenAI                              # асинхронное взаимодействие с OpenAI API
from langchain.text_splitter import CharacterTextSplitter   # библиотека langchain
from langchain.docstore.document import Document            # объект класса Document
from langchain_community.vectorstores import FAISS          # работа с векторной базой FAISS
from langchain.embeddings import HuggingFaceEmbeddings      # класс для работы с ветроной базой
from sentence_transformers import SentenceTransformer
from fastapi import HTTPException                           # для генерации исключений
from fastapi import status                                  # проверка статуса
import aiohttp
import time
import json

# получим переменные окружения из .env
load_dotenv()

os.environ['CURL_CA_BUNDLE'] = ''

BASE_URL = "https://openrouter.ai/api/v1"
API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = "deepseek/deepseek-r1-distill-qwen-32b:free"

# класс для работы с OpenAI
class Chunk():
    
    # МЕТОД: инициализация
    def __init__(self):
        # загружаем базу знаний
        self.base_load()
        
    # МЕТОД: загрузка базы знаний
    def base_load(self):
        # читаем текст базы знаний
        with open('base/Simble.txt', 'r', encoding='utf-8') as file:
            document = file.read()
        # создаем список чанков
        source_chunks = []
        splitter = CharacterTextSplitter(separator = ' ', chunk_size = 2000)
        for chunk in splitter.split_text(document):
            source_chunks.append(Document(page_content = chunk, metadata = {}))            
        # создаем индексную базу
        embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.db = FAISS.from_documents(source_chunks, embeddings_model)
        # формируем инструкцию system
        self.system = '''
            Ты-консультант в компании Simble, ответь на вопрос клиента на основе документа с информацией.
            Не придумывай ничего от себя, отвечай максимально по документу.
            Не упоминай Документ с информацией для ответа клиенту.
            Клиент ничего не должен знать про Документ с информацией для ответа клиенту            
        '''        

    # МЕТОД: запрос к OpenAI синхронный
    def get_answer(self, query: str):
        # получаем релевантные отрезки из базы знаний
        docs = self.db.similarity_search(query, k=4)
        message_content = '\n'.join([f'{doc.page_content}' for doc in docs])
        # формируем инструкцию user
        user = f'''
            Ответь на вопрос клиента. Не упоминай документ с информацией для ответа клиенту в ответе.
            Документ с информацией для ответа клиенту: {message_content}\n\n
            Вопрос клиента: \n{query}
        '''
        # готовим промпт
        messages = [
            {'role': 'system', 'content': self.system},
            {'role': 'user', 'content': user}
        ]
        # обращение к OpenAI
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)        
        response = client.chat.completions.create(
            model = 'deepseek/deepseek-r1-distill-qwen-32b:free',
            messages = messages,
            temperature = 0
        )
        # получение ответа модели
        return response.choices[0].message.content    

    # МЕТОД: запрос к OpenAI
    #   system  - инструкция system
    #   user    - инструкция user
    #   model   - название модели
    #   temp    - температура 
    #   format  - формат ответа
    async def request(self, system, user, model = 'deepseek/deepseek-r1-distill-qwen-32b:free', temp = None, format: dict = None):

        # подготовка параметров запроса
        client = AsyncOpenAI(base_url=BASE_URL)

        messages = [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user}
        ]
                
        # запрос в OpenAI
        try:
        
            # выполнение запроса
            response = await client.chat.completions.create(
                model = model,
                messages = messages,
                temperature = temp,
                response_format = format
            )
            
            # проверка результата запроса
            if response.choices:
                return response.choices[0].message.content
            else:
                print('Не удалось получить ответ от модели.')
                raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    detail = 'Не удалось получить ответ от модели.')
        
        except Exception as e:
            # обработка ошибок и исключений
            print(f'Ошибка при запросе в OpenAI: {e}')
            raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail = f'Ошибка при запросе в OpenAI: {e}')        

    # МЕТОД: запрос к OpenAI асинхронный
    async def get_answer_async(self, query: str):
        
        # получаем релевантные отрезки из базы знаний
        docs = self.db.similarity_search(query, k=4)
        message_content = '\n'.join([f'{doc.page_content}' for doc in docs])
        
        # формируем инструкцию user
        user = f'''
            Ответь на вопрос клиента. Не упоминай документ с информацией для ответа клиенту в ответе.
            Документ с информацией для ответа клиенту: {message_content}\n\n
            Вопрос клиента: \n{query}
        '''

        # получение ответа модели        
        answer = await self.request(self.system, user, MODEL, 0)

        # возврат ответа
        return answer

    # МЕТОД: распознавание изображения
    #   param = {
    #       image  - картинка в формате base64
    #       text   - текст для роли 'user'
    #   }    
    # Возвращает текст
    async def ocr_image(self, param: dict):

        # заголовок
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {os.environ.get("OPENAI_API_KEY")}'
        }
        
        # промпт
        payload = {
            'model': 'deepseek/deepseek-r1-distill-qwen-32b:free',
            'messages': [
                {
                    'role': 'user', 
                    'content': [
                        { 'type': 'text', 'text': param['text'] },
                        {
                            'type': 'image_url', 'image_url': {
                                'url': f'data:image/jpeg;base64, {param["image"]}'
                            }
                        }
                    ]
                }
            ]
        }

        # выполнение запроса
        async with aiohttp.ClientSession() as session:
            async with session.post(
                BASE_URL,
                headers = headers,
                json = payload
            ) as response:
                try:
                
                    # получение результата
                    result = await response.json()
                    
                    # обработка заголовков ограничения скорости
                    rate_limit_headers = {
                        'limit_requests': int(response.headers.get('x-ratelimit-limit-requests')),
                        'limit_tokens': int(response.headers.get('x-ratelimit-limit-tokens')),
                        'remaining_requests': int(response.headers.get('x-ratelimit-remaining-requests')),
                        'remaining_tokens': int(response.headers.get('x-ratelimit-remaining-tokens')),
                        'reset_tokens': int(response.headers.get('x-ratelimit-reset-tokens').replace('ms', '')),
                        'reset_requests': int(float(response.headers.get('x-ratelimit-reset-requests').replace('s', '')) * 1000)
                    }
                                       
                    # проверка оставшихся запросов и токенов
                    if rate_limit_headers['remaining_requests'] and rate_limit_headers['remaining_requests'] <= 0:
                        reset_time = rate_limit_headers['reset_requests'].replace('s', '')
                        time.sleep(reset_time)  # Задержка до сброса лимита

                    if rate_limit_headers['remaining_tokens'] and rate_limit_headers['remaining_tokens'] <= 0:
                        reset_time = rate_limit_headers['reset_tokens'].replace('s', '')
                        time.sleep(reset_time)  # Задержка до сброса лимита

                    # проверка на наличие ошибок в ответе
                    if 'error' in result:
                        message = result['error']['message']
                        print(message)
                        raise HTTPException(status_code = 400, detail = message)

                    # получение ответа
                    if 'choices' in result:                                           
                        # ответ в формате текста
                        return result['choices'][0]['message']['content']
                    else:
                        message = 'Response does not contain "choices"'
                        print(message)
                        raise HTTPException(status_code = 500, detail = message)

                except aiohttp.ContentTypeError as e:
                    message = f'ContentTypeError: {str(e)}'
                    print(message)
                    raise HTTPException(status_code = 500, detail = message)
                except json.JSONDecodeError as e:
                    message = f'JSONDecodeError: {str(e)}'
                    print(message)
                    raise HTTPException(status_code = 500, detail = message)        
        