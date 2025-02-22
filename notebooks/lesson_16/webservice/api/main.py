# импорт библиотек
from fastapi import FastAPI                         # библиотека FastAPI
from fastapi.responses import FileResponse          # метод для отправки файла
from pydantic import BaseModel                      # модуль для объявления структуры данных
from chunks import Chunk                            # модуль для работы с OpenAI
from fastapi.middleware.cors import CORSMiddleware  # поддержка cors

# создаем объект приложения FastAPI
app = FastAPI()

# поддержка cors
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  
	allow_credentials=True,
	allow_methods=["*"],  
	allow_headers=["*"],  
)

# создадим объект для работы с OpenAI
chunk = Chunk()

# класс с типами данных параметров 
class Item(BaseModel):
    name: str
    description: str
    old: int
    
# класс параметров калькулятора
class ModelCalc(BaseModel):
    a: float
    b: float        

# класс с типами данных для метода get_answer
class ModelAnswer(BaseModel):
    text: str    

# обработчик маршрута '/'
# полный путь запроса http://127.0.0.1:8000/
@app.get("/")
def root(): 
    return {"message": "Hello FastAPI"}

# маршрут для favicon.ico
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse('static/favicon.ico')

# обработчик маршрута '/about'
@app.get("/about")
def about():
    return {"message": "Страница с описанием проекта"}

# обработчик маршрута '/users/{id}'
@app.get("/users/{id}")
def users(id):
    return {"Вы ввели user_id": id}  

# функция-обработчик post запроса с параметрами пользователя
@app.post('/users')
def post_users(item: Item):
    return {'answer': f'Пользователь {item.name} - {item.description}, возраст {item.old} лет'}  

# функция-обработчик post запроса с параметрами для калькулятора
@app.post('/add')
def post_add(item:ModelCalc):
    result = item.a + item.b
    return {'result': result}

# функция обработки запроса к нейро-консультанту
@app.post('/get_answer')
def get_answer(question: ModelAnswer):
    answer = chunk.get_answer(query = question.text)
    return {'message': answer}