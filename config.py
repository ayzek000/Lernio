import os
import platform
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

    # Определяем операционную систему
    CURRENT_OS = platform.system()
    
    # На Windows используем SQLite, на Linux/Unix - PostgreSQL
    if CURRENT_OS == 'Windows':
        print("Запуск на Windows: используем SQLite для избежания проблем с кодировкой")
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance/site.db')
    else:
        # На Linux/Unix используем PostgreSQL
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith('postgresql'):
            # Дополнительные параметры подключения для надежности
            if '?' not in database_url:
                database_url += '?client_encoding=utf8'
            else:
                database_url += '&client_encoding=utf8'
            SQLALCHEMY_DATABASE_URI = database_url
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
