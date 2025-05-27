"""
Скрипт для настройки и запуска приложения
"""
import os
import sys
import subprocess
import time

def main():
    print("Начинаем настройку приложения...")
    
    # Проверяем, существует ли виртуальное окружение
    if not os.path.exists('venv'):
        print("Создаем виртуальное окружение...")
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
    
    # Путь к pip в виртуальном окружении
    pip_path = os.path.join('venv', 'Scripts', 'pip.exe')
    python_path = os.path.join('venv', 'Scripts', 'python.exe')
    
    # Устанавливаем зависимости
    print("Устанавливаем зависимости...")
    packages = [
        'Flask>=2.0',
        'Flask-SQLAlchemy>=2.5',
        'Flask-Migrate>=3.0',
        'Flask-Login>=0.5',
        'Flask-WTF>=1.0',
        'python-dotenv>=0.19',
        'bcrypt>=3.2',
        'psycopg2-binary>=2.9.5',
        'requests>=2.28.0',
        'gunicorn>=20.1.0',
        'Werkzeug>=2.0.0',
        'Jinja2>=3.0.0',
        'itsdangerous>=2.0.0',
        'click>=8.0.0',
        'MarkupSafe>=2.0.0',
        'pandas>=1.5.0',
        'python-docx>=0.8.11',
        'PyPDF2>=2.10.0',
        'openpyxl>=3.0.10',
        'WTForms>=3.0.0'
    ]
    
    for package in packages:
        print(f"Устанавливаем {package}...")
        try:
            subprocess.run([pip_path, 'install', package], check=True)
        except subprocess.CalledProcessError:
            print(f"Ошибка при установке {package}, продолжаем...")
    
    # Запускаем приложение
    print("Запускаем приложение...")
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    subprocess.run([python_path, 'run.py'])

if __name__ == "__main__":
    main()
