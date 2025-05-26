import os
from flask import Flask
from sqlalchemy import text

# Создаем тестовое приложение Flask
app = Flask(__name__)

# Загружаем конфигурацию из класса Config
from config import Config
app.config.from_object(Config)

# Инициализируем SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

print(f"Строка подключения: {app.config['SQLALCHEMY_DATABASE_URI']}")

try:
    with app.app_context():
        # Выполняем тестовый запрос
        result = db.session.execute(text("SELECT current_database(), current_user, version()")).fetchone()
        
        if result:
            print("\n✅ Успешное подключение к PostgreSQL!")
            print(f"База данных: {result[0]}")
            print(f"Пользователь: {result[1]}")
            print(f"Версия PostgreSQL: {result[2]}")
            
            # Проверяем таблицы
            tables = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)).fetchall()
            
            print("\nТаблицы в базе данных:")
            if tables:
                for table in tables:
                    print(f"- {table[0]}")
            else:
                print("Таблиц в схеме 'public' не найдено")
        else:
            print("❌ Неожиданный результат запроса")
except Exception as e:
    print(f"❌ Ошибка при подключении к базе данных: {e}")
