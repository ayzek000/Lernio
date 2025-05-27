import os
import sys

# Добавляем путь к проекту в sys.path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Импортируем приложение
from run import app

# Для Vercel
app.config.update(
    SERVER_NAME=None
)

# Для WSGI серверов (PythonAnywhere, Vercel)
application = app

# Для локального запуска
if __name__ == '__main__':
    app.run()
