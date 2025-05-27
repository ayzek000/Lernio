import os
import sys

# Добавляем путь к проекту в sys.path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Устанавливаем переменные окружения для Vercel
os.environ['FLASK_ENV'] = 'production'
os.environ['VERCEL'] = 'true'

# Создаем необходимые папки
instance_dir = os.path.join(path, 'instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

uploads_dir = os.path.join(path, 'app', 'static', 'uploads')
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

# Импортируем приложение
from app import create_app
from config import Config

# Создаем экземпляр приложения
app = create_app(Config)

# Для Vercel
app.config.update(
    SERVER_NAME=None,
    PREFERRED_URL_SCHEME='https'
)
