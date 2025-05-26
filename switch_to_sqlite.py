import os
from dotenv import load_dotenv
import shutil

# Загружаем переменные окружения из .env
load_dotenv()

# Путь к файлу .env
env_path = os.path.join(os.getcwd(), '.env')
env_backup_path = os.path.join(os.getcwd(), '.env.postgres_backup')

# Создаем резервную копию текущего .env файла
try:
    shutil.copy2(env_path, env_backup_path)
    print(f"✅ Создана резервная копия файла .env: {env_backup_path}")
except Exception as e:
    print(f"❌ Ошибка при создании резервной копии файла .env: {e}")
    exit(1)

# Создаем новый .env файл с SQLite
try:
    # Читаем текущий файл .env
    with open(env_path, 'r', encoding='utf-8') as file:
        env_content = file.read()
    
    # Заменяем или удаляем строку DATABASE_URL
    lines = env_content.split('\n')
    new_lines = []
    
    for line in lines:
        if line.startswith("DATABASE_URL="):
            # Заменяем на SQLite или просто удаляем (будет использоваться SQLite по умолчанию)
            # new_lines.append("# DATABASE_URL=sqlite:///instance/site.db")
            # Или просто пропускаем эту строку
            pass
        else:
            new_lines.append(line)
    
    # Добавляем комментарий о переключении на SQLite
    new_lines.append("\n# Временно отключено подключение к PostgreSQL из-за проблем с кодировкой в Windows")
    new_lines.append("# Используется SQLite по умолчанию")
    
    new_content = '\n'.join(new_lines)
    
    # Записываем обновленный файл .env
    with open(env_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print(f"\n✅ Файл .env обновлен для использования SQLite")
    print("Приложение теперь будет использовать локальную базу данных SQLite")
    print(f"Резервная копия с настройками PostgreSQL сохранена в {env_backup_path}")
    
except Exception as e:
    print(f"\n❌ Ошибка при обновлении файла .env: {e}")

# Обновляем config.py, чтобы принудительно использовать SQLite
config_path = os.path.join(os.getcwd(), 'config.py')
config_backup_path = os.path.join(os.getcwd(), 'config.py.postgres_backup')

try:
    # Создаем резервную копию config.py
    shutil.copy2(config_path, config_backup_path)
    print(f"\n✅ Создана резервная копия файла config.py: {config_backup_path}")
    
    # Читаем текущий файл config.py
    with open(config_path, 'r', encoding='utf-8') as file:
        config_content = file.read()
    
    # Заменяем блок с настройкой SQLALCHEMY_DATABASE_URI
    import re
    pattern = r'# Используем PostgreSQL в Supabase или SQLite локально.*?SQLALCHEMY_DATABASE_URI = database_url or.*?\'sqlite:///\' \+ os\.path\.join\(basedir, \'instance/site\.db\'\)'
    replacement = """# Временно используем только SQLite из-за проблем с кодировкой в Windows при подключении к PostgreSQL
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance/site.db')"""
    
    new_config_content = re.sub(pattern, replacement, config_content, flags=re.DOTALL)
    
    # Записываем обновленный файл config.py
    with open(config_path, 'w', encoding='utf-8') as file:
        file.write(new_config_content)
    
    print(f"✅ Файл config.py обновлен для использования только SQLite")
    
except Exception as e:
    print(f"\n❌ Ошибка при обновлении файла config.py: {e}")

print("\n✅ Готово! Приложение настроено на использование SQLite.")
print("Запустите приложение командой: .\\new_env\\Scripts\\python.exe run.py")
print("Для возврата к PostgreSQL восстановите файлы из резервных копий:")
print(f"1. Замените {env_path} на {env_backup_path}")
print(f"2. Замените {config_path} на {config_backup_path}")
