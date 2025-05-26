import os
import sys

# Добавляем путь к проекту в sys.path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Импортируем приложение
from run import app as application

# PythonAnywhere будет искать переменную application
if __name__ == '__main__':
    application.run()
