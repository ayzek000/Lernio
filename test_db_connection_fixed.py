import os
from dotenv import load_dotenv
import psycopg2

# Загружаем переменные окружения из .env
load_dotenv()

# Получаем строку подключения к базе данных
database_url = os.environ.get('DATABASE_URL')
print(f"Оригинальная строка подключения: {database_url}")

# Разбираем строку подключения на компоненты
# Формат: postgresql://username:password@host:port/dbname
try:
    # Извлекаем компоненты из строки подключения
    if database_url and database_url.startswith('postgresql://'):
        # Убираем протокол
        db_info = database_url.replace('postgresql://', '')
        
        # Разделяем учетные данные и хост
        credentials_host = db_info.split('@')
        
        if len(credentials_host) >= 2:
            # Получаем учетные данные (username:password)
            credentials = credentials_host[0].split(':')
            username = credentials[0]
            password = credentials[1] if len(credentials) > 1 else ''
            
            # Получаем хост, порт и имя базы данных
            host_info = credentials_host[1].split('/')
            host_port = host_info[0].split(':')
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '5432'
            
            # Имя базы данных и параметры
            dbname_params = host_info[1].split('?') if len(host_info) > 1 else ['postgres', '']
            dbname = dbname_params[0]
            
            print(f"\nРазобранные параметры подключения:")
            print(f"Хост: {host}")
            print(f"Порт: {port}")
            print(f"База данных: {dbname}")
            print(f"Пользователь: {username}")
            print(f"Пароль: {'*' * len(password)}")
            
            try:
                # Подключаемся с использованием отдельных параметров
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=dbname,
                    user=username,
                    password=password,
                    client_encoding='utf8'  # Явно указываем кодировку
                )
                
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
                print(f"\n❌ Ошибка при подключении к базе данных с отдельными параметрами: {e}")
        else:
            print("\n❌ Неверный формат строки подключения: отсутствует разделитель '@'")
    else:
        print("\n❌ Строка подключения не начинается с 'postgresql://'")
        
except Exception as e:
    print(f"\n❌ Ошибка при разборе строки подключения: {e}")
