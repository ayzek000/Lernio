import os
from dotenv import load_dotenv, set_key

# Путь к файлу .env
env_path = os.path.join(os.getcwd(), '.env')

# Сервисный ключ Supabase
service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhneWJvZXlqbGt2anRhdmxxYXZ2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODA4NjM2MSwiZXhwIjoyMDYzNjYyMzYxfQ.3HLtmhb7nLqIw2STbJFyHWeQR6_lysyIX9LzFIRvxNA"

# Добавляем или обновляем переменные окружения
try:
    # Добавляем SUPABASE_SERVICE_KEY
    print(f"Добавление SUPABASE_SERVICE_KEY в .env файл...")
    os.environ["SUPABASE_SERVICE_KEY"] = service_key
    set_key(env_path, "SUPABASE_SERVICE_KEY", service_key)
    
    print("✅ SUPABASE_SERVICE_KEY успешно добавлен")
    
    # Загружаем обновленные переменные
    load_dotenv(override=True)
    
    # Проверяем, что ключ установлен
    if os.environ.get("SUPABASE_SERVICE_KEY") == service_key:
        print("✅ SUPABASE_SERVICE_KEY успешно загружен в переменные окружения")
    else:
        print("❌ SUPABASE_SERVICE_KEY не был корректно загружен в переменные окружения")
    
except Exception as e:
    print(f"❌ Ошибка при обновлении переменных окружения: {e}")

print("\nТекущие переменные окружения:")
print(f"SUPABASE_URL: {os.environ.get('SUPABASE_URL', 'Не установлен')}")
print(f"SUPABASE_ANON_KEY: {os.environ.get('SUPABASE_ANON_KEY', 'Не установлен')}")
print(f"SUPABASE_SERVICE_KEY: {os.environ.get('SUPABASE_SERVICE_KEY', 'Не установлен')}")
print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'Не установлен')}")
print(f"DATABASE_DSN: {os.environ.get('DATABASE_DSN', 'Не установлен')}")
