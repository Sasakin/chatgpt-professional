# СОЗДАНИЕ САЙТА НА БАЗЕ DJANGO

1. Считаем, что у вас установлен Python, редактор VS Code, проект размещен в:
```
c:\Users\User\Python\LessonX\webservise (где User - имя папки вашего пользования системы Windows, X - номер вашего урока)
```

2. Открываем в редакторе VS Code проект webservice.

3. Входим в терминал и запускаем виртуальное окружение:

- создаем виртуальное окружение, если нет папки .venv:
```
python -m venv .venv
```

- входим в виртуальное окружение:
```
.venv\Scripts\activate
```

4. Установим фреймворк Django:

- в файле requirements.txt добавьте строки:
```
# site
django == 5.1.4
django-cors-headers == 4.6.0
```

- в терминале выполните установку:
```
pip install -r requirements.txt
```
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

		
5. Создайте папку website в папке webservice, в ней будет размещен наш проект сайта:
```
mkdir website

```		
		
6. Создаем проект website:
```
django-admin startproject main website
```
- в папке website должны появиться папка main и файл manage.py

7. Перейдем в папку website:
```
cd website
```
	
8. Вкратце о назначении файлов в папке main:
	__pycache__	- служебная папка для кэша
	asgi.py		- настройки для запуска проекта по протоколу ASGI (асинхронный)
	settings.py	- настройки приложения
	urls.py		- маршруты (роутинг)
	wsgi.py		- настройки для запуска проекта по протоколу WSGI (синхронный)
	
9. Применим миграции (нужны для применения настроек по-умолчанию):
```
python manage.py migrate
```

10. Создадим суперпользователя:
```
python manage.py createsuperuser
Username: admin
Email addess: admin@mail.ru
Password: admin
```
		
10. Запустим проект на порту 5000, т.к. порт 8000 у нас занят в предыдущем занятии сервисом api:

- первый способ подойдет для разработки:
```
python manage.py runserver 127.0.0.1:5000
```

- второй способ для производственной среды:
```
uvicorn main.asgi:application --host 0.0.0.0 --port 5000
```

11. Проверим в браузере работу сайта: 

```
http://127.0.0.1:5000
```
- по-умолчанию откроется страница фреймворка Django.
	
```
http://127.0.0.1:5000/admin
```
- откроется панель администратора.


12. Откроем новый терминал

13. В новом терминале опять входим в виртуальное окружение и в папку website:
```
.venv\Scripts\activate
cd website
```

14. Создадим приложение chatbot:
```
python manage.py startapp chatbot
```
- в папке появится папка chatbot с созданным приложением.

15. Назначение файлов и папок в папке chatbot:
	migrations	- каталог, в котором хранятся файлы миграций
	__init__.py	- указывает, что каталог chatbot является пакетом Python
	admin.py	- здесь регистрируются модели приложения для использования в админ-панели
	apps.py		- cодержит конфигурацию приложения
	models.py	- в этом файле определяются модели данных (таблицы базы данных) 
	tests.py	- cодержит тесты для вашего приложения
	views.py	- здесь определяются функции или классы, обрабатывающие HTTP-запросы
	
16.	Изменим стартовую страницу:

- в файле chabot\views.py добавим обработчик вызова главной страницы:
```
from django.http import HttpResponse
def start(request):
	return HttpResponse('Стартовая страница')
```

- в файле main\urls.py добавим импорт и путь в список urlpatterns:
```
from chatbot import views
urlpatterns = [ 
	path('admin/', admin.site.urls),
	path('', views.start, name = 'start'),
]
```

- снова проверим в браузере открытие страницы:
```
http://127.0.0.1:5000/
```
- откроется страница с сообщением "Стартовая страница"

17.	Сделаем произвольную страницу:

- в файле chabot\views.py добавим обработчик вызова тестовой страницы:
```
def test(request):
	return HttpResponse('Тестовая страница')
```
	
- в файле main\urls.py добавим путь в список urlpatterns:
```
urlpatterns = [ 
	path('admin/', admin.site.urls),
	path('', views.start, name = 'start'),
	path('test/', views.test, name = 'test'),
]
```

- проверим в браузере открытие тестовой страницы:
```
http://127.0.0.1:5000/test
```
- откроется страница с сообщением "Тестовая страница"
		
18.	Скачайте в любую другую папку архив с материалами к занятию и распакуйте его.

19. Из распакованного архива скопируйте из папки website папки templates и static в папку проекта website.

20.	Добавим обработчик вызова страницы chatbot и заменим обработчик start:
```
def start(request):
	return render(request, 'chatbot/start.html')
def chatbot(request):
	return render(request, 'chatbot/chatbot.html')
```

21. Добавим путь в файле main\urls.py путь к странице chatbot:
```
urlpatterns = [ 
	path('admin/', admin.site.urls),
	path('', views.start, name = 'start'),
	path('test/', views.test, name = 'test'),			
	path('chatbot/', views.chatbot, name = 'chatbot'),
]	
```
		
22.	Пропишем настройки в файле main\settings.py:

- добавляем приложения chatbot и corsheaders:
```
INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'chatbot',
	'corsheaders',
]
```
		
- включаем обработчик заголовков cors:
```
CORS_ALLOW_ALL_ORIGINS = True
```

- прописываем путь к шаблонам:
```
TEMPLATES = [				
	{                                                                                                                 
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [BASE_DIR / 'templates'],	
		...
```

- прописываем путь к статическим файлам:
```
STATICFILES_DIRS = [
	BASE_DIR / 'static'
]
```

23. Проверим проверим работу сайта:

- стартовая страница:
```
http://127.0.0.1:5000
```

- страница чат-бота:
```
http://127.0.0.1:5000/chatbot
```

24. Запустим наш API с предыдущей встречи:

- добавьте в файл api\main.py поддержку cors:
```
# дополнение для CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  
	allow_credentials=True,
	allow_methods=["*"],  
	allow_headers=["*"],  
)
```

- в файле api/.env введите свой ключ от сервис openai:
```
OPENAI_API_KEY = ваш_ключ_api_openai
```

- в открытом ранее терминале перейдите в каталог api:
```
cd ../api
```

- запустите сервис API:
```
uvicorn main:app --reload
```
	
25.	Проверьте работу чат-бота:
```
http://127.0.0.1:5000/chatbot
```


# ДОПОЛНЕНИЕ 1 "Размещение проекта в облаке"

## Хостинг:
- адрес https://beget.com/p1023067
- регистрация - выбираем VPS
- скачиваем и устанавливаем Putty: https://putty.org.ru/download
- с помощью PyTTYgen создаем приватный и публичный ключ
- публичный указываем при создании VPS, сохраняем к себе на компьютер
- приватный экспортируем в формате OpenSSH тоже к себе на компьютер
- создание символической ссылки для Ubuntu 24:
	sudo ln -s /usr/bin/python3.12 /usr/bin/python

## В VS Code:
- установим расширение "Remote - SSH (разработчик Microsoft)"
- откройте командную палитру (Ctrl+Shift+P)
- выбираем "Add New SSH Host"
- вводим команду для подключения:
	ssh user@hostname
- копируем приватный ключ в папку c:\users\user\.ssh под именем английскими буквами
- редактируем файл конфигурации в c:\users\user\.ssh\config


# ДОПОЛНЕНИЕ 2 "Установка Jupyter Lab"

## Установка Jupyter Notebook с помощью (при необходимости)

- установка docker:	
	sudo apt install podman-docker
	sudo apt install docker.io 

- запуск докера:
	docker run --restart always -p 8888:8888  -p 8000:8000 -p 5000:5000 -v /root/webservice:/home/jovyan -e JUPYTER_ENABLE_LAB=yes -d jupyter/base-notebook
	
