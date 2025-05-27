"""
Маршрут для обновления данных пользователя
"""
from flask import Blueprint, request, jsonify, current_app as app
from flask_login import current_user, login_required
from app import db, csrf
from app.models import User
from app.utils import log_activity
from werkzeug.security import generate_password_hash
from functools import wraps

# Создаем отдельный блюпринт для обновления данных пользователя
update_user_bp = Blueprint('update_user', __name__, url_prefix='/admin')

# Декоратор для проверки, является ли пользователь администратором
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Доступ запрещен'}), 403
        return f(*args, **kwargs)
    return decorated_function

@update_user_bp.route('/update_user', methods=['POST'])
@login_required
@admin_required
def update_user():
    """Обновление данных пользователя"""
    try:
        # Получаем данные из запроса
        data = request.get_json()
        
        # Проверяем наличие обязательных полей
        required_fields = ['user_id', 'username', 'role']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Поле {field} обязательно для заполнения'}), 400
        
        # Получаем пользователя из базы данных
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Проверяем, что пользователь с таким именем не существует (кроме текущего пользователя)
        if data['username'] != user.username:
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user:
                return jsonify({'error': 'Пользователь с таким именем уже существует'}), 400
        
        # Обновляем данные пользователя
        user.username = data['username']
        user.full_name = data.get('full_name', '')
        user.role = data['role']
        
        # Если был указан новый пароль, обновляем его
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        # Сохраняем изменения в базе данных
        db.session.commit()
        
        # Логируем действие
        log_activity(f'Обновлены данные пользователя: {data["username"]}', 'admin')
        
        return jsonify({'success': True, 'message': 'Данные пользователя успешно обновлены'}), 200
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при обновлении данных пользователя: {str(e)}')
        return jsonify({'error': str(e)}), 500
