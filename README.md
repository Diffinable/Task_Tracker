## Установка:
1. Клонирование репозитория
```bash
git clone https://github.com/Diffinable/Task_Tracker.git
cd Task_Tracker
```
2. Создание и активация виртуального окружения
```bash
python -m venv venv
source venv/bin/activate # Linux/MacOS
venv\Scripts\activate    # Windows
```
3. Установка зависимостей
```bash
pip install -r requirements.txt
```
4. Настройка окружения и базы данных
- Установите PostgreSQL 
- Создате базу данных time_tracker_db и пользователя для нее
- Создате в корне проекта файл .env на основе файла .env.example
- Заполните .env вашими данными для подключеня к базе данных
5. Применение миграций и запуск сервера
```bash
python manage.py migrate
python manage.py runserver
```
