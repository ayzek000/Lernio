import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# Загружаем переменные окружения
load_dotenv()

# Создаем тестовое приложение Flask
app = Flask(__name__)

# Загружаем конфигурацию из класса Config
from config import Config
app.config.from_object(Config)

# Инициализируем SQLAlchemy
db = SQLAlchemy(app)

# Выводим информацию о подключении к базе данных
print("\n=== Информация о подключении к базе данных ===")
print(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Проверяем подключение к базе данных
try:
    with app.app_context():
        # Выполняем простой запрос для проверки подключения
        result = db.session.execute(text("SELECT 1")).scalar()
        
        if result == 1:
            print("\n✅ Успешное подключение к базе данных!")
            
            # Определяем тип базы данных
            db_type = "SQLite" if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite') else "PostgreSQL"
            print(f"Тип базы данных: {db_type}")
            
            # Если PostgreSQL, проверяем доступные таблицы
            if db_type == "PostgreSQL":
                tables = db.session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)).fetchall()
                
                print("\nТаблицы в базе данных PostgreSQL:")
                if tables:
                    for table in tables:
                        print(f"- {table[0]}")
                else:
                    print("В базе данных нет таблиц в схеме 'public'")
            else:
                # Для SQLite получаем список таблиц
                tables = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
                
                print("\nТаблицы в базе данных SQLite:")
                if tables:
                    for table in tables:
                        print(f"- {table[0]}")
                else:
                    print("В базе данных нет таблиц")
        else:
            print("\n❌ Неожиданный результат запроса к базе данных")
except Exception as e:
    print(f"\n❌ Ошибка при подключении к базе данных: {e}")
