import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Путь к файлу .env
env_path = os.path.join(os.getcwd(), '.env')

try:
    # Читаем текущий файл .env
    with open(env_path, 'r', encoding='utf-8') as file:
        env_content = file.read()
    
    # Проверяем, есть ли уже SUPABASE_SERVICE_KEY
    if "SUPABASE_SERVICE_KEY=" not in env_content:
        # Запрашиваем у пользователя значение для SUPABASE_SERVICE_KEY
        print("\nДля полной функциональности Supabase необходимо добавить SUPABASE_SERVICE_KEY в файл .env")
        print("Вы можете найти этот ключ в настройках вашего проекта Supabase (Project Settings -> API)")
        
        service_key = input("\nВведите ваш SUPABASE_SERVICE_KEY: ")
        
        if service_key:
            # Добавляем SUPABASE_SERVICE_KEY в файл .env
            with open(env_path, 'a', encoding='utf-8') as file:
                file.write(f"\nSUPABASE_SERVICE_KEY={service_key}\n")
            
            print("\n✅ SUPABASE_SERVICE_KEY успешно добавлен в файл .env")
            print("Перезапустите приложение, чтобы изменения вступили в силу")
        else:
            print("\n❌ SUPABASE_SERVICE_KEY не был введен")
    else:
        print("\n✅ SUPABASE_SERVICE_KEY уже присутствует в файле .env")
    
except Exception as e:
    print(f"\n❌ Ошибка при обновлении файла .env: {e}")

print("\nТекущая конфигурация:")
print(f"SUPABASE_URL: {os.environ.get('SUPABASE_URL', 'Не установлен')}")
print(f"SUPABASE_ANON_KEY: {os.environ.get('SUPABASE_ANON_KEY', 'Не установлен')}")
print(f"SUPABASE_SERVICE_KEY: {os.environ.get('SUPABASE_SERVICE_KEY', 'Не установлен')}")
print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'Не установлен - используется SQLite')}")
