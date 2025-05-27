#!/usr/bin/env bash
# Exit on error
set -o errexit

# Устанавливаем переменную окружения VERCEL=true
export VERCEL=true

# Выводим диагностическую информацию
echo "Environment variables:" 
echo "VERCEL=$VERCEL"
echo "Running on: $(uname -a)"

# Устанавливаем зависимости
echo "Installing dependencies..."
pip install -r requirements.txt

# Создаем необходимые каталоги
echo "Creating necessary directories..."
mkdir -p instance
mkdir -p app/static/uploads

# Устанавливаем права на запись
echo "Setting permissions..."
chmod -R 777 instance
chmod -R 755 app/static

# Проверяем наличие базы данных SQLite
echo "Checking SQLite database..."
if [ ! -f "instance/site.db" ]; then
    echo "Database file not found, creating empty database..."
    touch instance/site.db
    chmod 666 instance/site.db
else
    echo "Database file found, using existing database."
fi

# Проверяем создание базы данных
if [ -f "instance/site.db" ]; then
    echo "Database file exists!"
    ls -la instance/
else
    echo "WARNING: Database file not found!"
fi

# Запускаем фласковые миграции
if [ -d "migrations" ]; then
    echo "Running database migrations..."
    python -m flask db upgrade || echo "Migrations failed, but continuing..."
fi

# Создаем администратора, если нет
echo "Creating admin user if not exists..."
python -c "from app import create_app; from app.models import db, User; app = create_app(); app.app_context().push(); admin = User.query.filter_by(username='admin').first(); admin = admin or User(username='admin', role='admin'); admin.set_password('admin'); db.session.add(admin); db.session.commit(); print('Admin user created or updated')" || echo "Admin user creation failed, but continuing..."

echo "Build completed successfully!"
