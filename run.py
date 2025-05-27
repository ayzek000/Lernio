import os
import sys

try:
    # Проверяем, включен ли режим разработки
    DEV_MODE = os.environ.get('FLASK_ENV') == 'development'
    # Проверяем, запущено ли на Vercel
    IS_VERCEL = os.environ.get('VERCEL') == 'true'
    
    if not IS_VERCEL:  # Выводим информацию только при локальном запуске
        print(f"\nРежим разработки: {'ВКЛЮЧЕН' if DEV_MODE else 'ВЫКЛЮЧЕН'}\n")
        print("\nИспользуем локальную аутентификацию и хранение файлов...\n")
    
    # Импортируем необходимые модули
    from app import create_app, db
    from app.models import User, Lesson, Material, Test, Question, Submission, ActivityLog, TransversalAssessment
    from config import Config
    
    # Убедимся, что папка instance существует
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        
    # Убедимся, что папка uploads существует
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

except Exception as e:
    print(f"\nОшибка при инициализации: {e}\n")
    raise

# Создаем экземпляр приложения через фабрику, используя конфигурацию из config.py
app = create_app(Config)

# Проверяем используемую базу данных
if os.environ.get('VERCEL') != 'true':
    print(f"\nИспользуемая база данных: {app.config['SQLALCHEMY_DATABASE_URI']}\n")

@app.shell_context_processor
def make_shell_context():
    """Добавляет объекты в сессию Flask shell для удобства."""
    return {
        'db': db,
        'User': User,
        'Lesson': Lesson,
        'Material': Material,
        'Test': Test,
        'Question': Question,
        'Submission': Submission,
        'ActivityLog': ActivityLog,
        'TransversalAssessment': TransversalAssessment
    }

if __name__ == '__main__':
    print("\nЗапуск приложения...")
    try:
        # Используем встроенный сервер Flask для разработки.
        # Для продакшена нужен WSGI-сервер (Gunicorn, uWSGI).
        print("\nЗапуск сервера Flask на http://localhost:5000\n")
        app.run(debug=True, host='0.0.0.0', port=5000) # Используем режим отладки для разработки
    except Exception as e:
        print(f"\nОшибка при запуске приложения: {e}\n")