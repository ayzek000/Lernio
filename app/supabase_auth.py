from flask_login import UserMixin
from app.supabase_models import SupabaseUser
from datetime import datetime

class User(UserMixin):
    """Класс пользователя для Flask-Login, адаптированный для Supabase"""
    
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.role = user_data.get('role', 'student')
        self.full_name = user_data.get('full_name')
        self.password_hash = user_data.get('password_hash')
        self.registration_date = user_data.get('registration_date')
        self.last_login = user_data.get('last_login')
    
    @property
    def is_teacher(self):
        return self.role == 'teacher'
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def check_password(self, password):
        return SupabaseUser.check_password({'password_hash': self.password_hash}, password)
    
    def set_password(self, password):
        return SupabaseUser.set_password(self.id, password)
    
    def update_last_login(self):
        return SupabaseUser.update_last_login(self.id)
    
    @staticmethod
    def get_by_id(user_id):
        user_data = SupabaseUser.get_by_id(user_id)
        if user_data:
            return User(user_data)
        return None
    
    @staticmethod
    def get_by_username(username):
        user_data = SupabaseUser.get_by_username(username)
        if user_data:
            return User(user_data)
        return None
    
    @staticmethod
    def create(username, password, role='student', full_name=None):
        """Создает нового пользователя"""
        user_data = SupabaseUser.create(username, password, role, full_name)
        if user_data:
            return User(user_data)
        return None
    
    @staticmethod
    def get_all():
        """Получает всех пользователей"""
        users_data = SupabaseUser.get_all()
        return [User(user_data) for user_data in users_data]
    
    @staticmethod
    def get_students():
        """Получает всех студентов"""
        students_data = SupabaseUser.get_by_role('student')
        return [User(user_data) for user_data in students_data]
    
    @staticmethod
    def get_teachers():
        """Получает всех учителей"""
        teachers_data = SupabaseUser.get_by_role('teacher')
        return [User(user_data) for user_data in teachers_data]
