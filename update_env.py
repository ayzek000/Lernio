import os
from dotenv import load_dotenv

# Загружаем текущие переменные окружения
load_dotenv()

# Получаем текущие значения
supabase_url = os.getenv("SUPABASE_URL", "")
project_id = ""

# Извлекаем project_id из URL
if supabase_url:
    # URL имеет формат https://your-project-id.supabase.co
    parts = supabase_url.split("//")
    if len(parts) > 1:
        domain_parts = parts[1].split(".")
        if len(domain_parts) > 0:
            project_id = domain_parts[0]

# Формируем DATABASE_URL на основе SUPABASE_URL
if project_id:
    database_url = f"postgresql://postgres:Aziz7340015@db.{project_id}.supabase.co:5432/postgres"
    
    # Читаем текущий файл .env
    env_path = os.path.join(os.getcwd(), '.env')
    env_content = ""
    
    try:
        with open(env_path, 'r', encoding='utf-8') as file:
            env_content = file.read()
    except Exception as e:
        print(f"Ошибка при чтении файла .env: {e}")
        exit(1)
    
    # Проверяем, есть ли уже DATABASE_URL в файле
    if "DATABASE_URL=" not in env_content:
        # Добавляем DATABASE_URL в файл .env
        with open(env_path, 'a', encoding='utf-8') as file:
            file.write(f"\n# Database URL for Supabase\nDATABASE_URL={database_url}\n")
        print(f"\n✅ DATABASE_URL добавлен в файл .env: {database_url}")
    else:
        print("\n⚠️ DATABASE_URL уже существует в файле .env")
else:
    print("\n❌ Не удалось извлечь project_id из SUPABASE_URL")
    print("Пожалуйста, добавьте DATABASE_URL вручную в файл .env")
    print("Пример: DATABASE_URL=postgresql://postgres:password@db.your-project-id.supabase.co:5432/postgres")
