"""
Скрипт для обновления структуры базы данных
"""
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database():
    """Обновляет структуру базы данных"""
    try:
        # Создаем приложение Flask
        app = Flask(__name__)
        app.config.from_object(Config)
        
        # Инициализируем базу данных
        db = SQLAlchemy(app)
        
        # Импортируем модели
        from app.models import User, LoginHistory
        
        # Создаем миграцию
        migrate = Migrate(app, db)
        
        # Создаем контекст приложения
        with app.app_context():
            # Проверяем подключение к базе данных
            logger.info("Проверяем подключение к базе данных...")
            try:
                db.engine.execute("SELECT 1")
                logger.info("Подключение к базе данных успешно!")
            except Exception as e:
                logger.error(f"Ошибка подключения к базе данных: {str(e)}")
                return False
            
            # Удаляем таблицу login_history и создаем ее заново
            logger.info("Удаляем таблицу login_history...")
            try:
                db.engine.execute("DROP TABLE IF EXISTS login_history")
                logger.info("Таблица login_history удалена!")
            except Exception as e:
                logger.error(f"Ошибка при удалении таблицы login_history: {str(e)}")
                return False
            
            # Создаем таблицу login_history заново
            logger.info("Создаем таблицу login_history заново...")
            try:
                db.engine.execute("""
                CREATE TABLE login_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    timestamp DATETIME,
                    ip_address VARCHAR(45),
                    user_agent VARCHAR(255),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
                """)
                logger.info("Таблица login_history создана!")
            except Exception as e:
                logger.error(f"Ошибка при создании таблицы login_history: {str(e)}")
                return False
            
            logger.info("База данных успешно обновлена!")
            return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении базы данных: {str(e)}")
        return False

if __name__ == "__main__":
    if update_database():
        print("База данных успешно обновлена!")
    else:
        print("Ошибка при обновлении базы данных!")
        sys.exit(1)
