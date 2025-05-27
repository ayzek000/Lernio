from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
import uuid

supabase = get_supabase_client()
supabase_admin = get_supabase_admin_client()

class SupabaseUser:
    """Адаптер для работы с пользователями в Supabase"""
    
    @staticmethod
    def create(username, password, role='student', full_name=None):
        """Создает нового пользователя"""
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password, method='pbkdf2:sha256:600000')
        
        user_data = {
            'id': user_id,
            'username': username,
            'password_hash': password_hash,
            'role': role,
            'full_name': full_name,
            'registration_date': datetime.utcnow().isoformat(),
        }
        
        response = supabase_admin.table('users').insert(user_data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(user_id):
        """Получает пользователя по ID"""
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_username(username):
        """Получает пользователя по имени пользователя"""
        response = supabase.table('users').select('*').eq('username', username).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def update(user_id, data):
        """Обновляет данные пользователя"""
        response = supabase.table('users').update(data).eq('id', user_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(user_id):
        """Удаляет пользователя"""
        response = supabase.table('users').delete().eq('id', user_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def check_password(user, password):
        """Проверяет пароль пользователя"""
        if not user or 'password_hash' not in user:
            return False
        return check_password_hash(user['password_hash'], password)
    
    @staticmethod
    def set_password(user_id, password):
        """Устанавливает новый пароль пользователя"""
        password_hash = generate_password_hash(password, method='pbkdf2:sha256:600000')
        return SupabaseUser.update(user_id, {'password_hash': password_hash})
    
    @staticmethod
    def update_last_login(user_id):
        """Обновляет время последнего входа пользователя"""
        return SupabaseUser.update(user_id, {'last_login': datetime.utcnow().isoformat()})

# Аналогичные адаптеры можно создать для других моделей
class SupabaseLesson:
    """Адаптер для работы с уроками в Supabase"""
    
    @staticmethod
    def create(title, description=None, order=0):
        """Создает новый урок"""
        lesson_id = str(uuid.uuid4())
        lesson_data = {
            'id': lesson_id,
            'title': title,
            'description': description,
            'order': order,
            'created_at': datetime.utcnow().isoformat()
        }
        
        response = supabase.table('lessons').insert(lesson_data).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_id(lesson_id):
        """Получает урок по ID"""
        response = supabase.table('lessons').select('*').eq('id', lesson_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_all(order_by='order'):
        """Получает все уроки, отсортированные по указанному полю"""
        response = supabase.table('lessons').select('*').order(order_by).execute()
        return response.data if response.data else []
    
    @staticmethod
    def update(lesson_id, data):
        """Обновляет данные урока"""
        response = supabase.table('lessons').update(data).eq('id', lesson_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def delete(lesson_id):
        """Удаляет урок"""
        response = supabase.table('lessons').delete().eq('id', lesson_id).execute()
        return response.data[0] if response.data else None

# Добавьте аналогичные адаптеры для других моделей