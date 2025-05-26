import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Проверяем наличие необходимых переменных окружения
required_vars = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_KEY",
    "DATABASE_URL",
    "SECRET_KEY"
]

print("\n=== Проверка переменных окружения ===\n")

all_vars_present = True
for var in required_vars:
    value = os.getenv(var)
    status = "[Установлен]" if value else "[Не установлен]"
    if not value:
        all_vars_present = False
    
    # Для безопасности не выводим полные значения ключей
    if value and ("KEY" in var or "URL" in var):
        masked_value = value[:5] + "..." + value[-5:] if len(value) > 10 else "***"
        print(f"{var}: {status} ({masked_value})")
    else:
        print(f"{var}: {status}")

if all_vars_present:
    print("\n✅ Все необходимые переменные окружения установлены.")
else:
    print("\n❌ Некоторые переменные окружения отсутствуют. Проверьте файл .env")
    
    # Создаем пример файла .env
    print("\nПример файла .env:")
    print("""
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Database URL for Supabase (используйте простой пароль без специальных символов)
DATABASE_URL=postgresql://postgres:password@db.your-project-id.supabase.co:5432/postgres

# Flask Configuration
SECRET_KEY=your-secret-key
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=1

# Timezone
TIMEZONE=Asia/Tashkent
    """)
