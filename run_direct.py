"""
Прямой запуск приложения без использования виртуального окружения
"""
import os
import sys
import importlib.util

# Проверяем наличие необходимых модулей
required_modules = [
    'flask', 'flask_sqlalchemy', 'flask_login', 'flask_wtf',
    'pandas', 'docx', 'PyPDF2', 'openpyxl'
]

missing_modules = []
for module in required_modules:
    try:
        # Пытаемся импортировать модуль
        if module == 'docx':
            # python-docx импортируется как docx
            importlib.import_module('docx')
        else:
            importlib.import_module(module)
        print(f"✓ Модуль {module} найден")
    except ImportError:
        missing_modules.append(module)
        print(f"✗ Модуль {module} не найден")

if missing_modules:
    print("\nОтсутствуют следующие модули:")
    for module in missing_modules:
        print(f"- {module}")
    print("\nУстановите их с помощью pip:")
    pip_commands = []
    for module in missing_modules:
        # Преобразуем имя модуля в имя пакета pip
        if module == 'docx':
            pip_commands.append('python-docx')
        elif module == 'flask_sqlalchemy':
            pip_commands.append('Flask-SQLAlchemy')
        elif module == 'flask_login':
            pip_commands.append('Flask-Login')
        elif module == 'flask_wtf':
            pip_commands.append('Flask-WTF')
        else:
            pip_commands.append(module)
    
    print(f"pip install {' '.join(pip_commands)}")
    sys.exit(1)

# Устанавливаем переменные окружения
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

# Импортируем и запускаем приложение
print("\nЗапускаем приложение...")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Импортируем create_app из app/__init__.py
from app import create_app
from config import Config

app = create_app(Config)

if __name__ == '__main__':
    app.run(debug=True)
