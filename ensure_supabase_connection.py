import os
import sys
import psycopg2
from dotenv import load_dotenv
import time

# Загружаем переменные окружения
load_dotenv()

# Получаем параметры Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')
RENDER = os.environ.get('RENDER')

print(f"Проверка переменных окружения:")
print(f"SUPABASE_URL установлен: {'Да' if SUPABASE_URL else 'Нет'}")
print(f"SUPABASE_SERVICE_KEY установлен: {'Да' if SUPABASE_SERVICE_KEY else 'Нет'}")
print(f"RENDER установлен: {'Да' if RENDER else 'Нет'}")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("КРИТИЧЕСКАЯ ОШИБКА: Не найдены переменные окружения SUPABASE_URL или SUPABASE_SERVICE_KEY")
    sys.exit(1)

# Извлекаем project_ref из URL
try:
    project_ref = SUPABASE_URL.split('.')[-2].split('/')[-1]
    print(f"Определен project_ref: {project_ref}")
except Exception as e:
    print(f"Ошибка при извлечении project_ref из URL: {e}")
    sys.exit(1)

# Формируем строку подключения к PostgreSQL
connection_string = f"postgresql://postgres:{SUPABASE_SERVICE_KEY}@db.{project_ref}.supabase.co:5432/postgres"
print(f"Строка подключения сформирована.")

def check_connection():
    """Проверяем соединение с базой данных Supabase."""
    print("\nПроверка соединения с Supabase PostgreSQL...")
    
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(connection_string)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Соединение установлено успешно!")
            print(f"Версия PostgreSQL: {version}")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Ошибка соединения: {e}")
            retries -= 1
            if retries > 0:
                print(f"Повторная попытка через 5 секунд... (осталось попыток: {retries})")
                time.sleep(5)
            else:
                print("Исчерпаны все попытки подключения к базе данных.")
                return False

def create_tables():
    """Создаем необходимые таблицы в базе данных."""
    print("\nСоздание таблиц в базе данных...")
    
    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        
        # Создаем таблицу пользователей, если она не существует
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(64) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            role VARCHAR(20) DEFAULT 'student',
            full_name VARCHAR(100),
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );
        """)
        
        # Создаем таблицу уроков, если она не существует
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id SERIAL PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            content TEXT,
            author_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Добавьте другие таблицы по необходимости...
        
        conn.commit()
        print("✅ Таблицы успешно созданы!")
        
        # Проверяем существование администратора
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin';")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            # Создаем администратора, если он не существует
            # Хеш пароля "password123"
            password_hash = "pbkdf2:sha256:150000$tMexkcBn$e40c6c6bc80d7a3a15f210ebcc9f69ba8924f48174a4d0c8a7b3f38f33de4c33"
            
            cursor.execute("""
            INSERT INTO users (username, password_hash, role, full_name)
            VALUES ('admin', %s, 'admin', 'Администратор Системы');
            """, (password_hash,))
            
            conn.commit()
            print("✅ Администратор успешно создан!")
            print("\nДанные для входа:")
            print("Логин: admin")
            print("Пароль: password123")
        else:
            print("✅ Администратор уже существует.")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

def check_tables():
    """Проверяем существование и структуру таблиц."""
    print("\nПроверка таблиц в базе данных...")
    
    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        
        # Проверяем существование таблицы пользователей
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
        );
        """)
        
        users_exists = cursor.fetchone()[0]
        
        if users_exists:
            print("✅ Таблица users существует.")
            
            # Проверяем структуру таблицы
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users';")
            columns = [row[0] for row in cursor.fetchall()]
            print(f"Столбцы таблицы users: {', '.join(columns)}")
            
            # Проверяем количество записей
            cursor.execute("SELECT COUNT(*) FROM users;")
            count = cursor.fetchone()[0]
            print(f"Количество пользователей в таблице: {count}")
        else:
            print("❌ Таблица users не существует!")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке таблиц: {e}")
        return False

if __name__ == "__main__":
    print("=== ПРОВЕРКА НАСТРОЙКИ SUPABASE ===")
    
    # Проверяем соединение
    if check_connection():
        # Создаем таблицы
        if create_tables():
            # Проверяем структуру и данные
            check_tables()
            print("\n✅ Настройка Supabase успешно завершена!")
        else:
            print("\n❌ Не удалось создать необходимые таблицы.")
            sys.exit(1)
    else:
        print("\n❌ Не удалось установить соединение с Supabase.")
        sys.exit(1)
