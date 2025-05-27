"""
Скрипт для исправления таблицы login_history
"""
import os
import sqlite3
import sys
from config import Config

def fix_login_history():
    """Исправляет таблицу login_history, добавляя каскадное удаление"""
    try:
        # Определяем путь к базе данных
        db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
        print(f"Путь к базе данных: {db_path}")
        
        # Проверяем, существует ли файл базы данных
        if not os.path.exists(db_path):
            print(f"Файл базы данных не найден: {db_path}")
            return False
        
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Создаем временную таблицу для сохранения данных
        print("Создаем временную таблицу...")
        cursor.execute("""
        CREATE TABLE login_history_temp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp DATETIME,
            ip_address VARCHAR(45),
            user_agent VARCHAR(255)
        )
        """)
        
        # Копируем данные из старой таблицы
        print("Копируем данные...")
        cursor.execute("""
        INSERT INTO login_history_temp
        SELECT id, user_id, timestamp, ip_address, user_agent
        FROM login_history
        """)
        
        # Удаляем старую таблицу
        print("Удаляем старую таблицу...")
        cursor.execute("DROP TABLE login_history")
        
        # Создаем новую таблицу с каскадным удалением
        print("Создаем новую таблицу с каскадным удалением...")
        cursor.execute("""
        CREATE TABLE login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp DATETIME,
            ip_address VARCHAR(45),
            user_agent VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """)
        
        # Копируем данные обратно
        print("Копируем данные обратно...")
        cursor.execute("""
        INSERT INTO login_history
        SELECT id, user_id, timestamp, ip_address, user_agent
        FROM login_history_temp
        """)
        
        # Удаляем временную таблицу
        print("Удаляем временную таблицу...")
        cursor.execute("DROP TABLE login_history_temp")
        
        # Сохраняем изменения
        conn.commit()
        conn.close()
        
        print("Таблица login_history успешно исправлена!")
        return True
    except Exception as e:
        print(f"Ошибка при исправлении таблицы login_history: {str(e)}")
        return False

if __name__ == "__main__":
    if fix_login_history():
        print("База данных успешно обновлена!")
    else:
        print("Ошибка при обновлении базы данных!")
        sys.exit(1)
