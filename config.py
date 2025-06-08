import os
import platform
import sys
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Загружаем переменные из .env, который находится в корневой директории проекта
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Базовый класс конфигурации."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-default-fallback-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Настройки CSRF-защиты
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # Время жизни токена в секундах (1 час)
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_HEADERS = ['X-CSRFToken', 'X-CSRF-Token']

    # Путь к папке загрузок
    if os.environ.get('RENDER') == 'true':
        # На Render используем постоянное хранилище
        UPLOAD_FOLDER = '/opt/render/project/src/uploads'
    else:
        # Локально используем папку внутри проекта
        UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')
    # Максимальный размер загружаемого файла (16 MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Определяем среду выполнения: локальная разработка или production (Vercel/Render)
    IS_PRODUCTION = os.environ.get('VERCEL') == 'true' or os.environ.get('RENDER') == 'true'
    
    # Используем SQLite для всех сред
    print(f"Используем SQLite в качестве базы данных")
    
    # Проверяем наличие переменной окружения DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    
    # Определяем путь к базе данных
    if database_url:
        # Используем переменную окружения, если она есть
        SQLALCHEMY_DATABASE_URI = database_url
        print(f"Используем базу данных из переменной окружения")
    elif IS_PRODUCTION:
        # В продакшене используем папку instance
        instance_dir = os.path.join(basedir, 'instance')
        # Создаем папку, если она не существует
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir)
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(instance_dir, 'site.db')
        print(f"Путь к базе данных (продакшен): {SQLALCHEMY_DATABASE_URI}")
    else:
        # При локальной разработке используем instance папку
        instance_dir = os.path.join(basedir, 'instance')
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir)
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(instance_dir, 'site.db')
        print(f"Путь к базе данных (разработка): {SQLALCHEMY_DATABASE_URI}")

    # Настройка часового пояса Ташкента (UTC+5)
    TIMEZONE = 'Asia/Tashkent'
    TIMEZONE_OFFSET = 5  # Часовой пояс Ташкента UTC+5
    
    # Настройки Firebase Storage
    USE_FIREBASE_STORAGE = os.environ.get('USE_FIREBASE_STORAGE', 'false').lower() == 'true'
    FIREBASE_CREDENTIALS_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH')
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET')
    
    # Проверяем наличие настроек Firebase
    if USE_FIREBASE_STORAGE and (not FIREBASE_CREDENTIALS_PATH or not FIREBASE_STORAGE_BUCKET):
        print("WARNING: Firebase Storage включен, но не указаны необходимые настройки (FIREBASE_CREDENTIALS_PATH или FIREBASE_STORAGE_BUCKET)")
        USE_FIREBASE_STORAGE = False
    
    # Здесь можно добавить другие настройки, например, для почты
    # MAIL_SERVER = os.environ.get('MAIL_SERVER')
    # MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    # MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # ADMINS = ['your-email@example.com']
