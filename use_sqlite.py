import os
from dotenv import load_dotenv
import shutil

# Загружаем переменные окружения
load_dotenv()

# Создаем резервную копию config.py
config_path = os.path.join(os.getcwd(), 'config.py')
backup_path = os.path.join(os.getcwd(), 'config.py.bak')

try:
    # Создаем резервную копию
    shutil.copy2(config_path, backup_path)
    print(f"✅ Создана резервная копия config.py")

    # Создаем новый файл config.py с жестко прописанным SQLite
    with open(config_path, 'w', encoding='utf-8') as file:
        file.write("""import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Загружаем переменные из .env, который находится в корневой директории проекта
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    \"\"\"Базовый класс конфигурации.\"\"\"
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

    # Используем SQLite для локальной разработки
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance/site.db')

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
""")
    
    print("✅ Файл config.py обновлен для использования SQLite")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")

print("\nПерезапустите приложение командой:")
print(".\\new_env\\Scripts\\python.exe run.py")
