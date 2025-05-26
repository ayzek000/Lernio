import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем URL и ключ Supabase из переменных окружения
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

# Проверяем наличие необходимых переменных окружения
if not supabase_url or not supabase_key or not supabase_service_key:
    print("\n\033[91mОшибка: Отсутствуют необходимые переменные окружения для Supabase\033[0m")
    print(f"SUPABASE_URL: {'[Установлен]' if supabase_url else '[Не установлен]'}")
    print(f"SUPABASE_ANON_KEY: {'[Установлен]' if supabase_key else '[Не установлен]'}")
    print(f"SUPABASE_SERVICE_KEY: {'[Установлен]' if supabase_service_key else '[Не установлен]'}")
    print("\nПроверьте файл .env и убедитесь, что все необходимые переменные установлены.\n")

# Создаем клиенты Supabase
supabase = None
supabase_admin = None

try:
    print("\nСоздание клиента Supabase...")
    supabase = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None
    supabase_admin = create_client(supabase_url, supabase_service_key) if supabase_url and supabase_service_key else None
    
    if supabase:
        print("Клиент Supabase успешно создан")
    else:
        print("\033[91mОшибка: Не удалось создать клиент Supabase\033[0m")
        
    if supabase_admin:
        print("Административный клиент Supabase успешно создан")
    else:
        print("\033[91mОшибка: Не удалось создать административный клиент Supabase\033[0m")
        
except Exception as e:
    print(f"\033[91mОшибка при создании клиента Supabase: {e}\033[0m")

def get_supabase_client():
    """Возвращает клиент Supabase с обычным ключом"""
    if not supabase:
        print("\033[93mПредупреждение: Клиент Supabase не инициализирован. Проверьте настройки в файле .env\033[0m")
    return supabase

def get_supabase_admin_client():
    """Возвращает клиент Supabase с сервисным ключом для административных операций"""
    if not supabase_admin:
        print("\033[93mПредупреждение: Административный клиент Supabase не инициализирован. Проверьте настройки в файле .env\033[0m")
    return supabase_admin
