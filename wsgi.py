import os
import sys

# Добавляем путь к проекту в sys.path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Для Vercel
os.environ['FLASK_ENV'] = 'production'
os.environ.setdefault('VERCEL', 'true')

# Импортируем приложение
from run import app

# Для Vercel
app.config.update(
    SERVER_NAME=None,
    PREFERRED_URL_SCHEME='https'
)

# Для WSGI серверов (PythonAnywhere, Vercel)
application = app

# Для локального запуска
if __name__ == '__main__':
    app.run()
