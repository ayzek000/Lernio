import os
import psycopg2
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Параметры подключения
host = "db.hgyboeyjlkvjtavlqavv.supabase.co"
port = "5432"
dbname = "postgres"
user = "postgres"
password = "Aziz7340015"

# Попытка подключения напрямую через psycopg2
try:
    print("Попытка подключения к базе данных напрямую через psycopg2...")
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )
    
    # Создаем курсор
    cursor = conn.cursor()
    
    # Выполняем запрос
    cursor.execute("SELECT current_database(), current_user, version()")
    result = cursor.fetchone()
    
    print("\n✅ Успешное подключение к PostgreSQL!")
    print(f"База данных: {result[0]}")
    print(f"Пользователь: {result[1]}")
    print(f"Версия PostgreSQL: {result[2]}")
    
    # Проверяем таблицы
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    
    print("\nТаблицы в базе данных:")
    if tables:
        for table in tables:
            print(f"- {table[0]}")
    else:
        print("Таблиц в схеме 'public' не найдено")
    
    # Теперь обновляем config.py для использования прямого подключения
    config_path = os.path.join(os.getcwd(), 'config.py')
    
    # Создаем новый config.py
    with open(config_path, 'w', encoding='utf-8') as file:
        file.write(f"""import os
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

    # Подключение к PostgreSQL с использованием прямой строки без кодировки URL
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:{password}@{host}:{port}/{dbname}"

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
    
    print("\n✅ Файл config.py обновлен с использованием прямой строки подключения")
    
    # Закрываем соединение
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Ошибка при подключении: {e}")
    
    # Создаем файл app/__init__.py, который будет инициализировать базу данных напрямую
    init_path = os.path.join(os.getcwd(), 'app', '__init__.py')
    
    with open(init_path, 'r', encoding='utf-8') as file:
        init_content = file.read()
    
    # Создаем обновленную версию __init__.py с прямым подключением к базе данных
    with open(init_path, 'w', encoding='utf-8') as file:
        # Заменяем строки импорта и инициализации базы данных
        updated_content = init_content.replace(
            "from flask_sqlalchemy import SQLAlchemy",
            """from flask_sqlalchemy import SQLAlchemy
import psycopg2
import sqlalchemy"""
        )
        
        # Добавляем код для прямого подключения к базе данных
        if "db = SQLAlchemy()" in updated_content:
            updated_content = updated_content.replace(
                "db = SQLAlchemy()",
                """db = SQLAlchemy()

# Для прямого доступа к базе данных PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        host="db.hgyboeyjlkvjtavlqavv.supabase.co",
        port=5432,
        dbname="postgres",
        user="postgres",
        password="Aziz7340015"
    )
    conn.autocommit = True
    return conn"""
            )
        
        file.write(updated_content)
    
    print("\n✅ Файл app/__init__.py обновлен для прямого подключения к базе данных")
    
    # Предлагаем использовать SQLite для разработки и тестирования
    print("\nРекомендация: для локальной разработки и тестирования используйте SQLite")
    print("Для продакшена настройте базу данных напрямую на сервере без Windows")
    print("Для работы файлового хранилища продолжайте использовать Supabase Storage")
    
print("\nПерезапустите приложение командой:")
print(".\\new_env\\Scripts\\python.exe run.py")
