import os
import urllib.parse
from dotenv import load_dotenv, set_key

# Загружаем переменные окружения из .env
load_dotenv()

# Путь к файлу .env
env_path = os.path.join(os.getcwd(), '.env')

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
    
    # Создаем URI строку подключения с параметрами кодировки
    uri_string = f"postgresql://{user}:{urllib.parse.quote_plus(password)}@{host}:{port}/{dbname}?client_encoding=utf8"
    
    try:
        # Устанавливаем DATABASE_URL
        os.environ["DATABASE_URL"] = uri_string
        set_key(env_path, "DATABASE_URL", uri_string)
        print(f"✅ DATABASE_URL обновлен: {uri_string}")
        
        # Перезагружаем переменные окружения
        load_dotenv(override=True)
        
        print("\nТеперь приложение будет использовать PostgreSQL в Supabase.")
        print("Перезапустите приложение командой:")
        print(".\\new_env\\Scripts\\python.exe run.py")
    except Exception as e:
        print(f"❌ Ошибка при обновлении DATABASE_URL: {e}")
else:
    print("❌ Не удалось извлечь project_id из SUPABASE_URL")
    print("Пожалуйста, проверьте значение SUPABASE_URL в файле .env")
