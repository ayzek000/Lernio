import os
from dotenv import load_dotenv
import psycopg2

# Загружаем переменные окружения из .env
load_dotenv()

# Получаем строку подключения к базе данных
database_url = os.environ.get('DATABASE_URL')

print(f"Строка подключения: {database_url}")

try:
    # Пробуем подключиться к базе данных
    conn = psycopg2.connect(database_url)
    
    # Создаем курсор
    cursor = conn.cursor()
    
    # Выполняем простой запрос
    cursor.execute("SELECT current_database(), current_user")
    
    # Получаем результат
    result = cursor.fetchone()
    
    print(f"\n✅ Успешное подключение к базе данных!")
    print(f"База данных: {result[0]}")
    print(f"Пользователь: {result[1]}")
    
    # Проверяем наличие таблиц
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    tables = cursor.fetchall()
    
    print("\nТаблицы в базе данных:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Закрываем соединение
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Ошибка при подключении к базе данных: {e}")
