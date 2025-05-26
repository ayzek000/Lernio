import os
import urllib.parse
from dotenv import load_dotenv
import psycopg2

# Загружаем переменные окружения из .env
load_dotenv()

# Получаем строку подключения к базе данных
database_url = os.environ.get('DATABASE_URL')
print(f"Оригинальная строка подключения: {database_url}")

# Создаем новую строку подключения с URL-кодированием
try:
    # Параметры подключения
    host = "db.hgyboeyjlkvjtavlqavv.supabase.co"
    port = "5432"
    dbname = "postgres"
    user = "postgres"
    password = "Aziz7340015"  # Используем простой пароль без специальных символов
    
    # URL-кодируем пароль
    encoded_password = urllib.parse.quote_plus(password)
    
    # Формируем новую строку подключения
    connection_string = f"host={host} port={port} dbname={dbname} user={user} password={password} client_encoding=utf8"
    
    print(f"\nИспользуем строку подключения с параметрами: {connection_string}")
    
    try:
        # Подключаемся с использованием строки с параметрами
        conn = psycopg2.connect(connection_string)
        
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
        
        # Если подключение успешно, обновляем .env файл
        if result:
            # Создаем новый .env файл с правильной строкой подключения
            env_path = os.path.join(os.getcwd(), '.env')
            env_content = ""
            
            try:
                with open(env_path, 'r', encoding='utf-8') as file:
                    env_content = file.read()
                
                # Заменяем строку DATABASE_URL
                lines = env_content.split('\n')
                new_lines = []
                
                for line in lines:
                    if line.startswith("DATABASE_URL="):
                        new_lines.append(f"DATABASE_URL={connection_string}")
                    else:
                        new_lines.append(line)
                
                new_content = '\n'.join(new_lines)
                
                # Записываем обновленный файл .env
                with open(env_path + '.fixed', 'w', encoding='utf-8') as file:
                    file.write(new_content)
                
                print(f"\n✅ Создан новый файл .env.fixed с рабочей строкой подключения")
                print("Пожалуйста, замените существующий файл .env на .env.fixed")
                
            except Exception as e:
                print(f"\n❌ Ошибка при обновлении файла .env: {e}")
        
    except Exception as e:
        print(f"\n❌ Ошибка при подключении к базе данных с параметрами: {e}")
        
except Exception as e:
    print(f"\n❌ Ошибка при создании строки подключения: {e}")
