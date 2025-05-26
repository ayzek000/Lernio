import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем URL и ключ Supabase из переменных окружения
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")  # Используем сервисный ключ для административных операций

print("\n=== Проверка подключения к Supabase ===\n")

if not supabase_url or not supabase_key:
    print("❌ Отсутствуют необходимые переменные окружения для Supabase")
    exit(1)

try:
    # Создаем клиент Supabase с сервисным ключом
    supabase = create_client(supabase_url, supabase_key)
    print("✅ Подключение к Supabase установлено")
    
    # Список необходимых таблиц
    required_tables = [
        "users", "lessons", "materials", "tests", "questions", 
        "submissions", "glossary_items", "chat_conversations", 
        "chat_participants", "chat_messages"
    ]
    
    # Проверяем наличие таблиц
    print("\n=== Проверка наличия таблиц ===\n")
    
    # Получаем список существующих таблиц
    try:
        response = supabase.table("pg_tables").select("tablename").eq("schemaname", "public").execute()
        
        if response.error:
            print(f"❌ Ошибка при получении списка таблиц: {response.error}")
        else:
            existing_tables = [table["tablename"] for table in response.data]
            print(f"Найдено таблиц: {len(existing_tables)}")
            
            if existing_tables:
                print(f"Существующие таблицы: {', '.join(existing_tables)}")
            
            # Проверяем, какие таблицы отсутствуют
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                print(f"\n❌ Отсутствуют следующие таблицы: {', '.join(missing_tables)}")
                print("\nНеобходимо создать отсутствующие таблицы в Supabase.")
            else:
                print("\n✅ Все необходимые таблицы существуют в Supabase")
    except Exception as e:
        print(f"❌ Ошибка при проверке таблиц: {e}")
    
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
                print("\nНеобходимо создать отсутствующие бакеты.")
            else:
                print("\n✅ Все необходимые бакеты существуют в Supabase Storage")
    
    except Exception as e:
        print(f"❌ Ошибка при проверке бакетов: {e}")

except Exception as e:
    print(f"❌ Ошибка при подключении к Supabase: {e}")
