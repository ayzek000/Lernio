from flask import Blueprint, request, jsonify, abort
from flask_login import current_user, login_required
from app import db
from app.models import User
from app.models_group import StudentGroup
from app.utils import log_activity
from app.admin_routes import admin_required
from werkzeug.security import generate_password_hash

bp = Blueprint('admin_api', __name__, url_prefix='/api/admin')

@bp.route('/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    """API для создания нового пользователя"""
    data = request.json
    
    # Проверяем обязательные поля
    if not data or not data.get('username') or not data.get('password') or not data.get('role'):
        return jsonify({'success': False, 'message': 'Не все обязательные поля заполнены'}), 400
    
    # Проверяем, что пользователь с таким именем не существует
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'success': False, 'message': f'Пользователь с именем {data["username"]} уже существует'}), 400
    
    # Проверяем роль
    if data['role'] not in ['student', 'teacher', 'admin']:
        return jsonify({'success': False, 'message': 'Некорректная роль'}), 400
    
    # Создаем нового пользователя
    new_user = User(
        username=data['username'],
        full_name=data.get('full_name', ''),
        role=data['role']
    )
    new_user.set_password(data['password'])
    
    # Если пользователь - студент и указана группа, добавляем его в группу
    if data['role'] == 'student' and data.get('group_id'):
        try:
            group_id = int(data['group_id'])
            group = StudentGroup.query.get(group_id)
            if group:
                new_user.group_id = group_id
        except (ValueError, TypeError):
            pass  # Игнорируем некорректный ID группы
    
    db.session.add(new_user)
    db.session.commit()
    
    log_activity(f'Создан новый пользователь: {new_user.username} (роль: {new_user.role})', 'admin')
    
    return jsonify({
        'success': True,
        'message': f'Пользователь {new_user.username} успешно создан',
        'user': {
            'id': new_user.id,
            'username': new_user.username,
            'full_name': new_user.full_name,
            'role': new_user.role,
            'group_id': new_user.group_id
        }
    })

@bp.route('/users/<int:user_id>/update', methods=['POST'])
@login_required
@admin_required
def update_user(user_id):
    """API для обновления данных пользователя"""
    user = User.query.get_or_404(user_id)
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'message': 'Нет данных для обновления'}), 400
    
    # Проверяем, не пытаемся ли мы изменить имя пользователя на уже существующее
    if 'username' in data and data['username'] != user.username:
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'success': False, 'message': f'Пользователь с именем {data["username"]} уже существует'}), 400
        user.username = data['username']
    
    # Обновляем остальные поля
    if 'full_name' in data:
        user.full_name = data['full_name']
    
    if 'role' in data and data['role'] in ['student', 'teacher', 'admin']:
        user.role = data['role']
    
    # Если указан новый пароль, обновляем его
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    
    # Обновляем группу, если пользователь - студент
    if user.role == 'student' and 'group_id' in data:
        if data['group_id']:
            try:
                group_id = int(data['group_id'])
                group = StudentGroup.query.get(group_id)
                if group:
                    user.group_id = group_id
                else:
                    user.group_id = None
            except (ValueError, TypeError):
                user.group_id = None
        else:
            user.group_id = None
    elif user.role != 'student':
        # Если пользователь не студент, убираем его из группы
        user.group_id = None
    
    db.session.commit()
    
    log_activity(f'Обновлен пользователь: {user.username} (ID: {user.id})', 'admin')
    
    return jsonify({
        'success': True,
        'message': f'Пользователь {user.username} успешно обновлен',
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'role': user.role,
            'group_id': user.group_id
        }
    })

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """API для удаления пользователя"""
    # Нельзя удалить самого себя
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'Невозможно удалить текущего пользователя'}), 400
    
    user = User.query.get_or_404(user_id)
    username = user.username
    
    db.session.delete(user)
    db.session.commit()
    
    log_activity(f'Удален пользователь: {username} (ID: {user_id})', 'admin')
    
    return jsonify({
        'success': True,
        'message': f'Пользователь {username} успешно удален'
    })

@bp.route('/groups', methods=['GET'])
@login_required
@admin_required
def get_groups():
    """API для получения списка групп"""
    groups = StudentGroup.query.all()
    return jsonify({
        'success': True,
        'groups': [{
            'id': group.id,
            'name': group.name,
            'description': group.description,
            'students_count': group.students.count()
        } for group in groups]
    })
