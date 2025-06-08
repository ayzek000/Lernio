import os
from flask import session, g, current_app
from flask_login import login_user, current_user
from datetime import datetime
from functools import wraps

# Фиктивные пользователи для режима разработки
MOCK_USERS = {
    'teacher': {
        'id': 'teacher-mock-id',
        'username': 'teacher',
        'role': 'teacher',
        'full_name': 'Olima Mukhidova (Режим разработки)',
        'password': '1234567890',
        'is_mock': True
    },
    'admin': {
        'id': 'admin-mock-id',
        'username': 'admin',
        'role': 'admin',
        'full_name': 'Администратор (Режим разработки)',
        'password': 'admin1234',
        'is_mock': True
    },
    'student': {
        'id': 'student-mock-id',
        'username': 'student',
        'role': 'student',
        'full_name': 'Студент (Режим разработки)',
        'password': 'student1234',
        'is_mock': True
    }
}

# Класс для фиктивного пользователя
class MockUser:
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.role = user_data['role']
        self.full_name = user_data['full_name']
        self.is_active = True
        self.is_authenticated = True
        self.is_anonymous = False
        self.is_mock = True
    
    def get_id(self):
        return self.id
    
    @property
    def is_teacher(self):
        return self.role == 'teacher'
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_student(self):
        return self.role == 'student'

# Функция для входа фиктивного пользователя
def login_mock_user(username, password):
    if username in MOCK_USERS and MOCK_USERS[username]['password'] == password:
        user = MockUser(MOCK_USERS[username])
        login_user(user)
        current_app.logger.info(f"[DEV MODE] Logged in mock user: {username}")
        # Сохраняем пользователя в сессии Flask
        session['user_id'] = user.id
        session['user_role'] = user.role
        session['user_username'] = user.username
        session['is_mock'] = True
        return user
    return None

# Функция для получения текущего фиктивного пользователя
def get_current_mock_user():
    if 'user_id' in session and session.get('is_mock'):
        user_id = session['user_id']
        for user_data in MOCK_USERS.values():
            if user_data['id'] == user_id:
                return MockUser(user_data)
    return None

# Декоратор для проверки доступа преподавателя (для режима разработки)
def dev_teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Если мы в режиме разработки и у нас есть фиктивный пользователь в сессии
        if os.environ.get('FLASK_ENV') == 'development' and 'user_id' in session:
            if session.get('user_role') == 'teacher':
                # Перед вызовом обработчика устанавливаем g.user
                g.user = get_current_mock_user()
                return f(*args, **kwargs)
            else:
                # Перенаправление на страницу логина с сообщением
                from flask import flash, redirect, url_for
                flash('У вас нет доступа к этой странице. Требуются права преподавателя.', 'danger')
                return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Декоратор для проверки доступа админа (для режима разработки)
def dev_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Если мы в режиме разработки и у нас есть фиктивный пользователь в сессии
        if os.environ.get('FLASK_ENV') == 'development' and 'user_id' in session:
            if session.get('user_role') == 'admin':
                # Перед вызовом обработчика устанавливаем g.user
                g.user = get_current_mock_user()
                return f(*args, **kwargs)
            else:
                # Перенаправление на страницу логина с сообщением
                from flask import flash, redirect, url_for
                flash('У вас нет доступа к этой странице. Требуются права администратора.', 'danger')
                return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Декоратор для проверки доступа студента (для режима разработки)
def dev_student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Если мы в режиме разработки и у нас есть фиктивный пользователь в сессии
        if os.environ.get('FLASK_ENV') == 'development' and 'user_id' in session:
            if session.get('user_role') == 'student':
                # Перед вызовом обработчика устанавливаем g.user
                g.user = get_current_mock_user()
                return f(*args, **kwargs)
            else:
                # Перенаправление на страницу логина с сообщением
                from flask import flash, redirect, url_for
                flash('У вас нет доступа к этой странице. Требуются права студента.', 'danger')
                return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
