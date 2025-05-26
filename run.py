from app import create_app, db
from app.models import User, Lesson, Material, Test, Question, Submission, ActivityLog, TransversalAssessment
from config import Config

# Создаем экземпляр приложения через фабрику, используя конфигурацию из config.py
app = create_app(Config)

# Проверяем используемую базу данных
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