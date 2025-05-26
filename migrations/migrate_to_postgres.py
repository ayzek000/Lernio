import sys
import os
import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Добавляем родительскую директорию в путь импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import db, create_app

def migrate_to_postgres():
    """
    Миграция данных из SQLite в PostgreSQL
    """
    print("Начинаем миграцию данных из SQLite в PostgreSQL...")
    
    # Путь к файлу SQLite
    sqlite_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance/site.db')
    
    # Проверяем, существует ли файл SQLite
    if not os.path.exists(sqlite_db_path):
        print(f"Ошибка: Файл базы данных SQLite не найден по пути: {sqlite_db_path}")
        return False
    
    # Подключение к SQLite
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # Получаем список таблиц из SQLite
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = sqlite_cursor.fetchall()
    table_names = [table['name'] for table in tables if not table['name'].startswith('sqlite_')]
    
    print(f"Найдено {len(table_names)} таблиц в SQLite: {', '.join(table_names)}")
    
    # Подключение к PostgreSQL
    try:
        # Параметры подключения к PostgreSQL
        pg_params = {
            'host': 'localhost',
            'port': '5432',
            'user': 'postgres',
            'password': 'Aziz7340015'
        }
        
        # Сначала подключаемся к postgres для создания базы данных
        pg_conn = psycopg2.connect(**pg_params, database='postgres')
        pg_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        pg_cursor = pg_conn.cursor()
        
        # Проверяем, существует ли база данных lernio
        pg_cursor.execute("SELECT 1 FROM pg_database WHERE datname='lernio'")
        exists = pg_cursor.fetchone()
        
        if not exists:
            print("Создаем базу данных lernio...")
            pg_cursor.execute("CREATE DATABASE lernio")
        
        pg_conn.close()
        
        # Подключаемся к базе данных lernio
        pg_params['database'] = 'lernio'
        pg_conn = psycopg2.connect(**pg_params)
        pg_cursor = pg_conn.cursor()
        
        # Создаем схему базы данных в PostgreSQL с помощью Flask-SQLAlchemy
        print("Создаем схему базы данных в PostgreSQL...")
        app = create_app()
        with app.app_context():
            db.create_all()
            
            # Создаем таблицу alembic_version вручную, если она не создана автоматически
            try:
                pg_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alembic_version (
                        version_num VARCHAR(32) NOT NULL, 
                        PRIMARY KEY (version_num)
                    )
                """)
                pg_conn.commit()
                print("Таблица alembic_version создана успешно")
            except Exception as e:
                print(f"Ошибка при создании таблицы alembic_version: {str(e)}")
                pg_conn.rollback()
        
        # Мигрируем данные из каждой таблицы
        for table_name in table_names:
            try:
                print(f"Миграция данных из таблицы {table_name}...")
                
                # Проверяем, существует ли таблица в PostgreSQL
                try:
                    # Используем то же имя таблицы, что и в SQLite
                    # Таблицы уже созданы с помощью create_schema.py
                    pg_cursor.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                    pg_conn.commit()
                except Exception as e:
                    print(f"Таблица {table_name} не существует в PostgreSQL, пропускаем: {str(e)}")
                    pg_conn.rollback()
                    continue
                
                # Получаем структуру таблицы
                sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
                columns = sqlite_cursor.fetchall()
                column_names = [column['name'] for column in columns]
                
                # Получаем данные из SQLite
                sqlite_cursor.execute(f"SELECT * FROM {table_name}")
                rows = sqlite_cursor.fetchall()
                
                if not rows:
                    print(f"Таблица {table_name} пуста, пропускаем...")
                    continue
                
                # Очищаем таблицу перед вставкой данных
                try:
                    pg_cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE")
                    pg_conn.commit()
                    print(f"Таблица {table_name} очищена")
                except Exception as e:
                    print(f"Ошибка при очистке таблицы {table_name}: {str(e)}")
                    pg_conn.rollback()
                
                # Вставляем данные в PostgreSQL
                success_count = 0
                print(f"Найдено {len(rows)} записей в таблице {table_name} для миграции")
                
                for i, row in enumerate(rows):
                    try:
                        # Создаем словарь значений
                        values = {column: row[column] for column in row.keys()}
                        
                        # Формируем SQL-запрос для вставки
                        columns_str = ', '.join(values.keys())
                        placeholders = ', '.join(['%s'] * len(values))
                        
                        # Выполняем запрос
                        pg_cursor.execute(
                            f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                            list(values.values())
                        )
                        success_count += 1
                        
                        # Печатаем прогресс каждые 10 записей или для последней записи
                        if (i + 1) % 10 == 0 or i == len(rows) - 1:
                            print(f"  Прогресс: {i + 1}/{len(rows)} записей обработано")
                    except Exception as e:
                        print(f"  Ошибка при вставке записи {i + 1}/{len(rows)} в таблицу {table_name}: {str(e)}")
                        pg_conn.rollback()
                        continue
                
                pg_conn.commit()
                print(f"Успешно перенесено {success_count} из {len(rows)} записей из таблицы {table_name}")
            except Exception as e:
                print(f"Ошибка при миграции таблицы {table_name}: {str(e)}")
                pg_conn.rollback()
        
        print("Миграция данных успешно завершена!")
        return True
    
    except Exception as e:
        print(f"Ошибка при миграции данных: {str(e)}")
        return False
    
    finally:
        # Закрываем соединения
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == "__main__":
    migrate_to_postgres()
