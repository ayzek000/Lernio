from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import os

# Создаем приложение Flask
app = Flask(__name__)

# Загружаем конфигурацию из класса Config
from config import Config
app.config.from_object(Config)

# Инициализируем SQLAlchemy
db = SQLAlchemy(app)

# Определяем модели (аналогично моделям в app/models.py)
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='student')
    full_name = db.Column(db.String(100))
    registration_date = db.Column(db.DateTime, server_default=db.func.now())
    last_login = db.Column(db.DateTime)

# Другие модели можно добавить по аналогии...

def init_db():
    """Инициализирует базу данных и создает администратора."""
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        print("Таблицы успешно созданы!")
        
        # Проверяем, существует ли пользователь admin
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            # Создаем администратора
            admin = User(
                id='00000000-0000-0000-0000-000000000000',
                username='admin',
                password_hash=generate_password_hash('password123'),
                role='admin',
                full_name='Администратор Системы'
            )
            
            db.session.add(admin)
            db.session.commit()
            print("Администратор успешно создан!")
            print("\nДанные для входа:")
            print("Логин: admin")
            print("Пароль: password123")
        else:
            print("Администратор уже существует.")

if __name__ == "__main__":
    print("Инициализация SQLite базы данных...")
    init_db()
    print("Инициализация завершена!")
