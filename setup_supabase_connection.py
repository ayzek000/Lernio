import os
import urllib.parse
from dotenv import load_dotenv, set_key

# Загружаем переменные окружения из .env
load_dotenv()

# Путь к файлу .env
env_path = os.path.join(os.getcwd(), '.env')

# Получаем или устанавливаем сервисный ключ
service_key = os.environ.get("SUPABASE_SERVICE_KEY")
if not service_key:
    service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhneWJvZXlqbGt2anRhdmxxYXZ2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODA4NjM2MSwiZXhwIjoyMDYzNjYyMzYxfQ.3HLtmhb7nLqIw2STbJFyHWeQR6_lysyIX9LzFIRvxNA"
    os.environ["SUPABASE_SERVICE_KEY"] = service_key
    set_key(env_path, "SUPABASE_SERVICE_KEY", service_key)
    print("✅ SUPABASE_SERVICE_KEY добавлен в .env файл")

# Получаем Supabase URL
supabase_url = os.environ.get("SUPABASE_URL")
project_id = ""

if supabase_url:
    # Извлекаем project_id из URL
    parts = supabase_url.split("//")
    if len(parts) > 1:
        domain_parts = parts[1].split(".")
        if len(domain_parts) > 0:
            project_id = domain_parts[0]

print(f"Project ID: {project_id}")

if project_id:
    # Параметры подключения
    host = f"db.{project_id}.supabase.co"
    port = "5432"
    dbname = "postgres"
    user = "postgres"
    password = "Aziz7340015"  # Простой пароль без специальных символов
    
    # Создаем URI строку подключения (классический формат)
    uri_string = f"postgresql://{user}:{urllib.parse.quote_plus(password)}@{host}:{port}/{dbname}"
    
    # Устанавливаем DATABASE_URL
    os.environ["DATABASE_URL"] = uri_string
    set_key(env_path, "DATABASE_URL", uri_string)
    print(f"✅ DATABASE_URL установлен: {uri_string}")
    
    # Загружаем обновленные переменные
    load_dotenv(override=True)
    
    print("\nНастройка базы данных завершена. Теперь вы можете запустить приложение:")
    print(".\new_env\Scripts\python.exe run.py")
else:
    print("❌ Не удалось извлечь project_id из SUPABASE_URL")
    print("Пожалуйста, проверьте значение SUPABASE_URL в файле .env")
