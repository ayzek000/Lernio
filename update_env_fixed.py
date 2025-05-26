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

# Формируем DATABASE_URL на основе SUPABASE_URL с параметрами кодировки
if project_id:
    # Используем простой пароль без специальных символов, как указано в памяти
    database_url = f"postgresql://postgres:Aziz7340015@db.{project_id}.supabase.co:5432/postgres?client_encoding=utf8"
    
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
    if "DATABASE_URL=" in env_content:
        # Заменяем существующий DATABASE_URL
        lines = env_content.split('\n')
        new_lines = []
        for line in lines:
            if line.startswith("DATABASE_URL="):
                new_lines.append(f"DATABASE_URL={database_url}")
            else:
                new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
        
        # Записываем обновленный файл .env
        with open(env_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        print(f"\n✅ DATABASE_URL обновлен в файле .env с параметрами кодировки: {database_url}")
    else:
        # Добавляем DATABASE_URL в файл .env
        with open(env_path, 'a', encoding='utf-8') as file:
            file.write(f"\n# Database URL for Supabase с параметрами кодировки\nDATABASE_URL={database_url}\n")
        
        print(f"\n✅ DATABASE_URL добавлен в файл .env с параметрами кодировки: {database_url}")
else:
    print("\n❌ Не удалось извлечь project_id из SUPABASE_URL")
    print("Пожалуйста, добавьте DATABASE_URL вручную в файл .env")
    print("Пример: DATABASE_URL=postgresql://postgres:password@db.your-project-id.supabase.co:5432/postgres?client_encoding=utf8")
