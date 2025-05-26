import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем URL и ключ Supabase из переменных окружения
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")  # Используем анонимный ключ для обычных операций

print("\n=== Проверка подключения к Supabase ===\n")

if not supabase_url or not supabase_key:
    print("❌ Отсутствуют необходимые переменные окружения для Supabase")
    exit(1)

try:
    # Создаем клиент Supabase
    supabase = create_client(supabase_url, supabase_key)
    print("✅ Подключение к Supabase установлено")
    
    # Проверяем наличие бакетов в Storage
    print("\n=== Проверка и создание бакетов в Supabase Storage ===\n")
    
    try:
        # Получаем список существующих бакетов
        existing_buckets_response = supabase.storage.list_buckets()
        
        # Преобразуем ответ в список имен бакетов
        existing_buckets = []
        if isinstance(existing_buckets_response, list):
            existing_buckets = [bucket["name"] for bucket in existing_buckets_response]
        
        print(f"Найдено бакетов: {len(existing_buckets)}")
        
        if existing_buckets:
            print(f"Существующие бакеты: {', '.join(existing_buckets)}")
        
        # Список необходимых бакетов
        required_buckets = ['materials', 'images', 'videos', 'avatars', 'attachments']
        
        # Создаем недостающие бакеты
        for bucket in required_buckets:
            if bucket not in existing_buckets:
                print(f"\nСоздание бакета: {bucket}")
                try:
                    # Создаем бакет с публичным доступом
                    options = {"public": True}
                    response = supabase.storage.create_bucket(bucket, options)
                    print(f"✅ Бакет {bucket} успешно создан")
                except Exception as e:
                    print(f"❌ Ошибка при создании бакета {bucket}: {e}")
            else:
                print(f"\nБакет {bucket} уже существует")
        
        # Получаем обновленный список бакетов
        updated_buckets_response = supabase.storage.list_buckets()
        
        # Преобразуем ответ в список имен бакетов
        updated_buckets = []
        if isinstance(updated_buckets_response, list):
            updated_buckets = [bucket["name"] for bucket in updated_buckets_response]
        
        print(f"\nОбновленный список бакетов: {', '.join(updated_buckets)}")
    
    except Exception as e:
        print(f"❌ Ошибка при работе с бакетами: {e}")

except Exception as e:
    print(f"❌ Ошибка при подключении к Supabase: {e}")
