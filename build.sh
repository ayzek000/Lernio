#!/usr/bin/env bash
# Exit on error
set -o errexit

# Устанавливаем переменную окружения RENDER=true
export RENDER=true

# Выводим диагностическую информацию
echo "Environment variables:" 
echo "RENDER=$RENDER"
echo "Running on: $(uname -a)"

# Устанавливаем зависимости
echo "Installing dependencies..."
pip install -r requirements.txt

# Создаем необходимые каталоги
echo "Creating necessary directories..."
mkdir -p data
mkdir -p instance
mkdir -p app/static/uploads

# Устанавливаем права на запись
echo "Setting permissions..."
chmod -R 777 data
chmod -R 777 instance
chmod -R 755 app/static

# Инициализируем базу данных SQLite
echo "Initializing SQLite database..."
python init_sqlite.py

# Проверяем создание базы данных
if [ -f "data/site.db" ]; then
    echo "Database file created successfully!"
    ls -la data/
else
    echo "WARNING: Database file not found!"
fi

# Запускаем фласковые миграции, если они есть
if [ -d "migrations" ]; then
    echo "Running database migrations..."
    flask db upgrade || echo "Migrations failed, but continuing..."
fi

echo "Build completed successfully!"
