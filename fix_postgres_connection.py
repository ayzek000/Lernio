import os
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
    # Параметры подключения в формате key=value без URL-кодирования
    db_params = {
        "host": f"db.{project_id}.supabase.co",
        "port": "5432",
        "dbname": "postgres",
        "user": "postgres",
        "password": "Aziz7340015",
        "client_encoding": "utf8",
        "application_name": "sewing_lms"
    }
    
    # Создаем строку параметров в формате key=value
    params_string = " ".join([f"{k}={v}" for k, v in db_params.items()])
    
    # Формируем строку подключения для SQLAlchemy с отдельными параметрами
    connection_string = f"postgresql://{params_string}"
    
    try:
        # Обновляем config.py для использования ключевых параметров вместо URL
        config_path = os.path.join(os.getcwd(), 'config.py')
        
        with open(config_path, 'r', encoding='utf-8') as file:
            config_content = file.read()
        
        # Ищем блок с настройкой SQLALCHEMY_DATABASE_URI
        if "SQLALCHEMY_DATABASE_URI = database_url" in config_content:
            # Заменяем настройку на прямое использование строки подключения
            updated_content = config_content.replace(
                "SQLALCHEMY_DATABASE_URI = database_url",
                f"SQLALCHEMY_DATABASE_URI = '{connection_string}' # Используем прямое подключение без URL"
            )
            
            with open(config_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
            
            print(f"✅ Файл config.py обновлен с новой строкой подключения")
        else:
            print("❌ Не удалось найти строку SQLALCHEMY_DATABASE_URI в config.py")
            
    except Exception as e:
        print(f"❌ Ошибка при обновлении файла config.py: {e}")
    
    print("\nПерезапустите приложение командой:")
    print(".\\new_env\\Scripts\\python.exe run.py")
else:
    print("❌ Не удалось извлечь project_id из SUPABASE_URL")
    print("Пожалуйста, проверьте значение SUPABASE_URL в файле .env")
