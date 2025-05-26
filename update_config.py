import os
import re
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Путь к файлу config.py
config_path = os.path.join(os.getcwd(), 'config.py')

try:
    # Читаем содержимое файла config.py
    with open(config_path, 'r', encoding='utf-8') as file:
        config_content = file.read()
    
    # Новый код для подключения к базе данных с использованием DSN
    new_db_code = '''    # Используем PostgreSQL в Supabase с DSN форматом для Windows или SQLite локально
    database_dsn = os.environ.get('DATABASE_DSN')
    database_url = os.environ.get('DATABASE_URL')
    
    if database_dsn:
        # Используем DSN строку для подключения к PostgreSQL в Windows
        SQLALCHEMY_DATABASE_URI = f"postgresql://{database_dsn}"
    elif database_url and database_url.startswith('postgresql'):
        # Добавляем параметры кодировки для PostgreSQL через URI
        if '?' not in database_url:
            database_url += '?client_encoding=utf8'
        else:
            database_url += '&client_encoding=utf8'
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Резервный вариант - SQLite
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance/site.db')'''
    
    # Ищем блок настройки SQLALCHEMY_DATABASE_URI и заменяем его
    pattern = r'# Используем PostgreSQL.*?SQLALCHEMY_DATABASE_URI = .*?\'sqlite:///\'.*?\'instance/site\.db\'\)'
    updated_content = re.sub(pattern, new_db_code, config_content, flags=re.DOTALL)
    
    # Записываем обновленный файл config.py
    with open(config_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    print("✅ Файл config.py успешно обновлен для использования DSN-формата подключения к PostgreSQL")
    
except Exception as e:
    print(f"❌ Ошибка при обновлении файла config.py: {e}")
