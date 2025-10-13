Установка:

git clone https://github.com/Diffinable/Task_Tracker.git

cd Task_Tracker

python -m venv venv

source venv/bin/activate

pip install -r requirements.txt

Создать базу данных Postgresql

Создать файл .env на подобие .env.example

python manage.py migrate

python manage.py runserver

