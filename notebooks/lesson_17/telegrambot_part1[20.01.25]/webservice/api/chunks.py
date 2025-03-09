# импорт библиотек
from dotenv import load_dotenv                              # работа с переменными окружения
import os                                                   # взаимодействие с операционной системой
from openai import OpenAI                                   # взаимодействие с OpenAI API
from langchain.text_splitter import CharacterTextSplitter   # библиотека langchain
from langchain.docstore.document import Document            # объект класса Document
from langchain_community.vectorstores import FAISS          # модуль для работы с векторной базой FAISS
from langchain_openai import OpenAIEmbeddings               # класс для работы с ветроной базой

# получим переменные окружения из .env
load_dotenv('.env')

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
        splitter = CharacterTextSplitter(separator = ' ', chunk_size = 8000)
        for chunk in splitter.split_text(document):
            source_chunks.append(Document(page_content = chunk, metadata = {}))            
        # создаем индексную базу
        embeddings = OpenAIEmbeddings()
        self.db = FAISS.from_documents(source_chunks, embeddings)
        # формируем инструкцию system
        self.system = '''
            Ты-консультант в компании Simble, ответь на вопрос клиента на основе документа с информацией.
            Не придумывай ничего от себя, отвечай максимально по документу.
            Не упоминай Документ с информацией для ответа клиенту.
            Клиент ничего не должен знать про Документ с информацией для ответа клиенту            
        '''        

# метод запроса к OpenAI
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
        client = OpenAI()        
        response = client.chat.completions.create(
            model = 'gpt-4o-mini',
            messages = messages,
            temperature = 0
        )
        # получение ответа модели
        return response.choices[0].message.content    
