"""
Модуль для локальной аутентификации без Supabase
"""

import os
import logging
from datetime import datetime
from flask import session, g, current_app
from flask_login import UserMixin, login_user

logger = logging.getLogger(__name__)

# Проверяем, включен ли режим разработки
DEV_MODE = os.environ.get('FLASK_ENV') == 'development'

# Фиктивные пользователи для локальной аутентификации
MOCK_USERS = {
    'teacher': {
        'id': '1',
        'username': 'teacher',
        'role': 'teacher',
        'full_name': 'Olima Mukhidova',
        'password': '1234567890',
        'email': 'teacher@example.com',
        'last_login': datetime.utcnow(),
        'is_active': True
    },
    'admin': {
        'id': '2',
        'username': 'admin',
        'role': 'admin',
        'full_name': 'Администратор',
        'password': 'admin1234',
        'email': 'admin@example.com',
        'last_login': datetime.utcnow(),
        'is_active': True
    },
    'student': {
        'id': '3',
        'username': 'student',
        'role': 'student',
        'full_name': 'Студент',
        'password': 'student1234',
        'email': 'student@example.com',
        'last_login': datetime.utcnow(),
        'is_active': True
    },
    '123': {
        'id': '4',
        'username': '123',
        'role': 'student',
        'full_name': 'Тестовый Студент',
        'password': '123456',
        'email': 'test@example.com',
        'last_login': datetime.utcnow(),
        'is_active': True
    }
}

# Класс пользователя для Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data.get('id')
        self.username = user_data.get('username')
        self.role = user_data.get('role')
        self.full_name = user_data.get('full_name')
        self.email = user_data.get('email')
        self.password = user_data.get('password')
        self.last_login = user_data.get('last_login')
        self._active = user_data.get('is_active', True)
    
    @property
    def is_active(self):
        return self._active
    
    @property
    def is_teacher(self):
        return self.role == 'teacher'
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    def check_password(self, password):
        """Проверка пароля пользователя"""
        logger.info(f"Проверка пароля для пользователя {self.username}")
        return self.password == password
    
    @staticmethod
    def get_by_username(username):
        """Получение пользователя по имени пользователя"""
        if username in MOCK_USERS:
            return User(MOCK_USERS[username])
        return None
    
    @staticmethod
    def get_by_id(user_id):
        """Получение пользователя по ID"""
        for user_data in MOCK_USERS.values():
            if user_data['id'] == user_id:
                return User(user_data)
        return None

# Функция для аутентификации пользователя
def authenticate_user(username, password):
    """Аутентификация пользователя по имени и паролю"""
    # Сначала проверяем в мок-пользователях
    user = User.get_by_username(username)
    if user and user.check_password(password):
        return user
    
    # Если не нашли в мок-пользователях, проверяем в базе данных
    try:
        # Импортируем модель User из app.models
        from app.models import User as DBUser
        from app import db
        
        db_user = DBUser.query.filter_by(username=username).first()
        if db_user and db_user.check_password(password):
            # Создаем объект нашего локального пользователя из пользователя базы данных
            user_data = {
                'id': str(db_user.id),
                'username': db_user.username,
                'role': db_user.role,
                'full_name': db_user.full_name,
                'password': password,  # Сохраняем пароль в открытом виде для локального пользователя
                'email': '',
                'last_login': db_user.last_login,
                'is_active': True
            }
            return User(user_data)
    except Exception as e:
        logger.error(f"Ошибка при попытке аутентификации через базу данных: {str(e)}")
    
    return None

# Функция для входа пользователя
def login_local_user(username, password, remember=False):
    """Вход пользователя в систему"""
    user = authenticate_user(username, password)
    if user:
        login_user(user, remember=remember)
        logger.info(f"Пользователь {username} успешно вошел в систему")
        
        # Сохраняем данные в сессии для надежности
        session['user_id'] = user.id
        session['user_role'] = user.role
        session['user_username'] = user.username
        
        return user
    
    logger.warning(f"Неудачная попытка входа пользователя {username}")
    return None
