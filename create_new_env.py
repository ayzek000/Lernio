import os

# Создаем новый файл .env с корректной кодировкой UTF-8
env_content = """# Flask Configuration
FLASK_APP=run.py
FLASK_DEBUG=1
SECRET_KEY='your_very_secret_key_here'

# Supabase Configuration
SUPABASE_URL=https://hgyboeyjlkvjtavlqavv.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhneWJvZXlqbGt2anRhdmxxYXZ2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTYzNjI3NjEsImV4cCI6MTc0ODA4NjM2MX0.b7nLqIw2STbJFyHWeQR6_lysyIX9LzFIRvxNAdCI

# Database URL with encoding parameters
DATABASE_URL=postgresql://postgres:Aziz7340015@db.hgyboeyjlkvjtavlqavv.supabase.co:5432/postgres?client_encoding=utf8
"""

try:
    # Записываем новый файл .env
    with open('.env.new', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Создан новый файл .env.new с корректной кодировкой UTF-8")
    print("Пожалуйста, замените существующий файл .env на .env.new:")
    print("1. Переименуйте .env в .env.backup")
    print("2. Переименуйте .env.new в .env")
except Exception as e:
    print(f"❌ Ошибка при создании файла .env.new: {e}")
