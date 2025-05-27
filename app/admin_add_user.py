"""
Маршрут для добавления пользователей
"""
from flask import Blueprint, request, jsonify, current_app as app
from flask_login import current_user, login_required
from app import db, csrf
from app.models import User
from app.utils import log_activity
from werkzeug.security import generate_password_hash
from functools import wraps

# Создаем отдельный блюпринт для добавления пользователей
add_user_bp = Blueprint('add_user', __name__, url_prefix='/admin')

# Декоратор для проверки, является ли пользователь администратором
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Доступ запрещен'}), 403
        return f(*args, **kwargs)
    return decorated_function

@add_user_bp.route('/add_user', methods=['POST'])
@login_required
@admin_required
def add_user():
    """Добавление нового пользователя"""
    try:
        # Получаем данные из запроса
        data = request.get_json()
        
        # Проверяем наличие обязательных полей
        required_fields = ['username', 'password', 'role']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Поле {field} обязательно для заполнения'}), 400
        
        # Проверяем, что пользователь с таким именем не существует
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'error': 'Пользователь с таким именем уже существует'}), 400
        
        # Создаем нового пользователя
        new_user = User(
            username=data['username'],
            full_name=data.get('full_name', ''),
            role=data['role']
        )
        
        # Устанавливаем пароль
        new_user.set_password(data['password'])
        
        # Сохраняем пользователя в базе данных
        db.session.add(new_user)
        db.session.commit()
        
        # Логируем действие
        log_activity(f'Добавлен новый пользователь: {data["username"]}', 'admin')
        
        return jsonify({'success': True, 'message': 'Пользователь успешно добавлен'}), 201
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при добавлении пользователя: {str(e)}')
        return jsonify({'error': str(e)}), 500
