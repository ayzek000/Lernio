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

    # Путь к папке загрузок внутри папки 'app'
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')
    # Максимальный размер загружаемого файла (16 MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Определяем среду выполнения: локальная разработка или production (Render)
    IS_PRODUCTION = os.environ.get('RENDER') == 'true'
    
    # Настройка подключения к базе данных
    if IS_PRODUCTION:
        # В продакшене всегда используем Supabase PostgreSQL
        print("Запуск в production: используем Supabase PostgreSQL")
        
        # Получаем параметры Supabase
        SUPABASE_URL = os.environ.get('SUPABASE_URL')
        SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')
        
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("КРИТИЧЕСКАЯ ОШИБКА: Не установлены переменные окружения SUPABASE_URL или SUPABASE_SERVICE_KEY")
            print("Приложение не может быть запущено без этих параметров в production-режиме")
            sys.exit(1)
            
        # Формируем строку подключения к PostgreSQL в Supabase
        # Формат URL: postgresql://postgres:[password]@db.[project_ref].supabase.co:5432/postgres
        # Извлекаем проект из URL
        project_ref = SUPABASE_URL.split('.')[-2].split('/')[-1]
        SQLALCHEMY_DATABASE_URI = f"postgresql://postgres:{SUPABASE_SERVICE_KEY}@db.{project_ref}.supabase.co:5432/postgres?client_encoding=utf8"
    else:
        # При локальной разработке используем SQLite
        print("Запуск в режиме разработки: используем SQLite")
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance/site.db')
            print(f"Запуск на {CURRENT_OS}: используем PostgreSQL в Supabase")
        else:
            # Резервный вариант
            SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance/site.db')
            print(f"Запуск на {CURRENT_OS}: используем SQLite (DATABASE_URL не найден)")

    # Настройка часового пояса Ташкента (UTC+5)
    TIMEZONE = 'Asia/Tashkent'
    TIMEZONE_OFFSET = 5  # Часовой пояс Ташкента UTC+5
    
    # Здесь можно добавить другие настройки, например, для почты
    # MAIL_SERVER = os.environ.get('MAIL_SERVER')
    # MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    # MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # ADMINS = ['your-email@example.com']
