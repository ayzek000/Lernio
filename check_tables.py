import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем URL и ключ Supabase из переменных окружения
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")  # Используем сервисный ключ для административных операций

print("\n=== Проверка таблиц в Supabase ===\n")

if not supabase_url or not supabase_key:
    print("❌ Отсутствуют необходимые переменные окружения для Supabase")
    exit(1)

try:
    # Создаем клиент Supabase с сервисным ключом
    supabase = create_client(supabase_url, supabase_key)
    print("✅ Подключение к Supabase установлено")
    
    # Список необходимых таблиц
    required_tables = [
        "users",
        "lessons",
        "materials",
        "tests",
        "questions",
        "submissions",
        "glossary_items",
        "chat_conversations",
        "chat_participants",
        "chat_messages"
    ]
    
    # Проверяем наличие таблиц
    print("\nПроверка наличия таблиц:")
    
    # Получаем список существующих таблиц
    response = supabase.table("pg_tables").select("tablename").eq("schemaname", "public").execute()
    
    if response.error:
        print(f"❌ Ошибка при получении списка таблиц: {response.error}")
        exit(1)
    
    existing_tables = [table["tablename"] for table in response.data]
    print(f"Найдено таблиц: {len(existing_tables)}")
    
    if existing_tables:
        print(f"Существующие таблицы: {', '.join(existing_tables)}")
    
    # Проверяем, какие таблицы отсутствуют
    missing_tables = [table for table in required_tables if table not in existing_tables]
    
    if missing_tables:
        print(f"\n❌ Отсутствуют следующие таблицы: {', '.join(missing_tables)}")
        print("\nНеобходимо создать отсутствующие таблицы в Supabase.")
        print("Вы можете создать их через интерфейс Supabase или с помощью SQL-запросов.")
        
        # Примеры SQL-запросов для создания таблиц
        print("\nПримеры SQL-запросов для создания таблиц:")
        
        # Пример для таблицы users
        if "users" in missing_tables:
            print("""
-- Создание таблицы users
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    full_name VARCHAR(100),
    registration_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Создание политик RLS для таблицы users
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Политика для чтения: пользователи могут видеть только свои данные, учителя могут видеть данные своих учеников, админы видят всё
CREATE POLICY "Users can view their own data" ON users
    FOR SELECT USING (auth.uid() = id OR auth.jwt() ->> 'role' = 'teacher' OR auth.jwt() ->> 'role' = 'admin');

-- Политика для создания: только админы могут создавать пользователей
CREATE POLICY "Only admins can create users" ON users
    FOR INSERT WITH CHECK (auth.jwt() ->> 'role' = 'admin');

-- Политика для обновления: пользователи могут обновлять только свои данные, админы могут обновлять любые данные
CREATE POLICY "Users can update their own data" ON users
    FOR UPDATE USING (auth.uid() = id OR auth.jwt() ->> 'role' = 'admin');

-- Политика для удаления: только админы могут удалять пользователей
CREATE POLICY "Only admins can delete users" ON users
    FOR DELETE USING (auth.jwt() ->> 'role' = 'admin');
            """)
    else:
        print("\n✅ Все необходимые таблицы существуют в Supabase")
    
    # Проверяем наличие бакетов в Storage
    print("\n=== Проверка бакетов в Supabase Storage ===\n")
    
    try:
        storage_response = supabase.storage.list_buckets()
        
        if storage_response.error:
            print(f"❌ Ошибка при получении списка бакетов: {storage_response.error}")
        else:
            existing_buckets = [bucket["name"] for bucket in storage_response.data]
            print(f"Найдено бакетов: {len(existing_buckets)}")
            
            if existing_buckets:
                print(f"Существующие бакеты: {', '.join(existing_buckets)}")
            
            # Список необходимых бакетов
            required_buckets = ['materials', 'images', 'videos', 'avatars', 'attachments']
            
            # Проверяем, какие бакеты отсутствуют
            missing_buckets = [bucket for bucket in required_buckets if bucket not in existing_buckets]
            
            if missing_buckets:
                print(f"\n❌ Отсутствуют следующие бакеты: {', '.join(missing_buckets)}")
                print("\nНеобходимо создать отсутствующие бакеты через API или интерфейс Supabase.")
            else:
                print("\n✅ Все необходимые бакеты существуют в Supabase Storage")
    
    except Exception as e:
        print(f"❌ Ошибка при проверке бакетов: {e}")

except Exception as e:
    print(f"❌ Ошибка при подключении к Supabase: {e}")
