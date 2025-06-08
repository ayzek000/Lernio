import os
import sys
from app import db, create_app
from app.models import *
from flask_migrate import upgrade

def fix_database():
    """Функция для проверки и исправления базы данных"""
    print("\n[1/4] Инициализация приложения...")
    app = create_app()
    
    with app.app_context():
        # Проверяем путь к базе данных
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"\n[2/4] Используемая база данных: {db_uri}")
        
        # Проверяем структуру таблицы materials
        print("\n[3/4] Проверка структуры таблицы materials...")
        try:
            # Проверяем наличие таблицы materials
            tables = db.engine.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='materials';").fetchall()
            if not tables:
                print("Таблица materials не найдена! Возможно, нужно выполнить миграции.")
                return
            
            # Проверяем наличие поля order
            columns = db.engine.execute("PRAGMA table_info(materials);").fetchall()
            column_names = [col[1] for col in columns]
            
            if 'order' in column_names and 'position' in column_names:
                print("Найдены оба поля: 'order' и 'position'. Переносим данные из 'position' в 'order'...")
                # Копируем данные из position в order
                db.engine.execute("UPDATE materials SET \"order\" = position WHERE position IS NOT NULL AND \"order\" IS NULL;")
                print("Данные перенесены.")
            elif 'order' in column_names:
                print("Поле 'order' найдено. Все в порядке.")
            elif 'position' in column_names:
                print("Найдено только поле 'position', но не 'order'. Создаем поле 'order'...")
                # Создаем поле order
                db.engine.execute("ALTER TABLE materials ADD COLUMN \"order\" INTEGER DEFAULT 0;")
                # Копируем данные из position в order
                db.engine.execute("UPDATE materials SET \"order\" = position WHERE position IS NOT NULL;")
                print("Поле 'order' создано и данные перенесены.")
            else:
                print("Ни поле 'order', ни поле 'position' не найдены. Создаем поле 'order'...")
                # Создаем поле order
                db.engine.execute("ALTER TABLE materials ADD COLUMN \"order\" INTEGER DEFAULT 0;")
                print("Поле 'order' создано.")
            
            # Проверяем данные в таблице materials
            print("\n[4/4] Проверка данных в таблице materials...")
            materials = db.engine.execute("SELECT id, title, type, lesson_id, \"order\" FROM materials LIMIT 5;").fetchall()
            if materials:
                print("Первые 5 записей в таблице materials:")
                for material in materials:
                    print(f"ID: {material[0]}, Title: {material[1]}, Type: {material[2]}, Lesson ID: {material[3]}, Order: {material[4]}")
            else:
                print("Таблица materials пуста.")
            
            print("\nПроверка базы данных завершена.")
            
        except Exception as e:
            print(f"Ошибка при проверке базы данных: {str(e)}")

if __name__ == "__main__":
    fix_database()
