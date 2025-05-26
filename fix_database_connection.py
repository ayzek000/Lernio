import os
import urllib.parse
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Получаем текущие значения
supabase_url = os.getenv("SUPABASE_URL", "")
service_key = os.getenv("SUPABASE_SERVICE_KEY", "")

project_id = ""

# Извлекаем project_id из URL
if supabase_url:
    # URL имеет формат https://your-project-id.supabase.co
    parts = supabase_url.split("//")
    if len(parts) > 1:
        domain_parts = parts[1].split(".")
        if len(domain_parts) > 0:
            project_id = domain_parts[0]

print(f"Project ID: {project_id}")

# Формируем DATABASE_URL с URL-кодированием и psycopg2 DSN форматом
if project_id:
    # Базовые параметры подключения
    host = f"db.{project_id}.supabase.co"
    port = "5432"
    dbname = "postgres"
    user = "postgres"
    password = "Aziz7340015"  # Используем простой пароль без специальных символов
    
    # Создаем строку подключения в формате libpq DSN
    # Документация: https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
    dsn_params = {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
        "client_encoding": "utf8",
        "application_name": "sewing_lms"
    }
    
    # Формируем DSN строку в формате key=value key=value
    dsn_string = " ".join([f"{k}={v}" for k, v in dsn_params.items()])
    
    # Формируем также URI строку для совместимости
    uri_string = f"postgresql://{user}:{urllib.parse.quote_plus(password)}@{host}:{port}/{dbname}?client_encoding=utf8&application_name=sewing_lms"
    
    print(f"\nDSN строка подключения (рекомендуется для Windows):\n{dsn_string}")
    print(f"\nURI строка подключения (альтернатива):\n{uri_string}")
    
    # Обновляем файл .env
    env_path = os.path.join(os.getcwd(), '.env')
    env_content = ""
    
    try:
        with open(env_path, 'r', encoding='utf-8') as file:
            env_content = file.read()
        
        # Создаем обновленное содержимое
        lines = env_content.split('\n')
        new_lines = []
        database_url_updated = False
        dsn_string_added = False
        service_key_added = False
        
        for line in lines:
            if line.startswith("DATABASE_URL="):
                # Заменяем на новую URI строку
                new_lines.append(f"DATABASE_URL={uri_string}")
                database_url_updated = True
            elif line.startswith("DATABASE_DSN="):
                # Обновляем DSN строку
                new_lines.append(f"DATABASE_DSN={dsn_string}")
                dsn_string_added = True
            elif line.startswith("SUPABASE_SERVICE_KEY="):
                if service_key:
                    new_lines.append(f"SUPABASE_SERVICE_KEY={service_key}")
                    service_key_added = True
                else:
                    # Сохраняем строку как есть
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Добавляем DATABASE_DSN, если его нет
        if not dsn_string_added:
            new_lines.append(f"\n# Строка подключения в формате DSN для Windows")
            new_lines.append(f"DATABASE_DSN={dsn_string}")
        
        # Добавляем SUPABASE_SERVICE_KEY, если его нет и есть значение
        if not service_key_added and service_key:
            new_lines.append(f"\n# Service key для административного доступа к Supabase")
            new_lines.append(f"SUPABASE_SERVICE_KEY={service_key}")
        
        # Добавляем DATABASE_URL, если его нет
        if not database_url_updated:
            new_lines.append(f"\n# Строка подключения к базе данных")
            new_lines.append(f"DATABASE_URL={uri_string}")
        
        new_content = '\n'.join(new_lines)
        
        # Записываем обновленный файл .env
        with open(env_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        print(f"\n✅ Файл .env успешно обновлен")
        
    except Exception as e:
        print(f"\n❌ Ошибка при обновлении файла .env: {e}")
else:
    print("\n❌ Не удалось извлечь project_id из SUPABASE_URL")
    print("Пожалуйста, проверьте значение SUPABASE_URL в файле .env")
