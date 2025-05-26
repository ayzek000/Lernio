#!/usr/bin/env bash
# Exit on error
set -o errexit

# Устанавливаем переменную окружения RENDER=true
export RENDER=true

# Выводим список переменных окружения для диагностики
echo "Environment variables:" 
if [ -n "$SUPABASE_URL" ]; then
    echo "SUPABASE_URL is set"
else
    echo "SUPABASE_URL is NOT set"
fi

if [ -n "$SUPABASE_SERVICE_KEY" ]; then
    echo "SUPABASE_SERVICE_KEY is set"
else
    echo "SUPABASE_SERVICE_KEY is NOT set"
fi

echo "RENDER=$RENDER"

# Устанавливаем зависимости
pip install -r requirements.txt

# Проверяем соединение с Supabase и создаем необходимые таблицы
echo "Starting Supabase connection test and table creation..."
python ensure_supabase_connection.py

# Создаем каталог instance на всякий случай
mkdir -p instance

# Даем права на чтение и запись для каталога статических файлов
chmod -R 755 app/static

# Запускаем фласковые миграции, если они есть
if [ -d "migrations" ]; then
    echo "Running database migrations..."
    flask db upgrade
fi

echo "Build completed successfully!"
