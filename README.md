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

## API Endpoints

### Аутентификация
- `POST /api/register/` - Регистрация нового пользователя.
- `POST /api/token/` - Получение JWT токена.

### Задачи (`/api/tasks/`)
- `GET /api/tasks/` - Получить список задач.
- `POST /api/tasks/` - Создать новую задачу (автоматически становитесь владельцем).
- `GET /api/tasks/{id}/` - Получить одну задачу.
- `PATCH /api/tasks/{id}/` - Обновить задачу (только для владельца).

### Участники задачи (`/api/tasks/{task_id}/users/`)
- `GET /api/tasks/{task_id}/users/` - Список участников задачи.
- `POST /api/tasks/{task_id}/users/` - Добавить участника в задачу (только для владельца).
- `PATCH /api/tasks/{task_id}/users/{user_task_id}/` - Изменить роль участника (только для владельца).

### Ветки (`/api/tasks/{task_id}/branches/`)
- `GET /api/tasks/{task_id}/branches/` - Список веток задачи.
- `POST /api/tasks/{task_id}/branches/` - Создать ветку (любой участник).

### Рабочее время
- `POST /api/tasks/{task_id}/users/{user_task_id}/log_time/` - Залогировать время (только для самого себя).

