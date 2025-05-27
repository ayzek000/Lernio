"""
Маршрут для удаления пользователей
"""
from flask import Blueprint, flash, redirect, url_for, request, current_app as app
from flask_login import current_user, login_required
from app import db, csrf
from app.models import User
from app.utils import log_activity
from functools import wraps

# Создаем отдельный блюпринт для удаления пользователей
delete_user_bp = Blueprint('delete_user', __name__, url_prefix='/admin')

# Декоратор для проверки, является ли пользователь администратором
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('У вас нет доступа к этой странице. Требуются права администратора.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@delete_user_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Удаление пользователя из системы"""
    if request.method == 'POST':
        try:
            user = User.query.get_or_404(user_id)
            
            # Проверяем, не пытается ли администратор удалить самого себя
            if user.id == current_user.id:
                flash('Вы не можете удалить свою учетную запись.', 'danger')
                return redirect(url_for('admin.users'))
            
            username = user.username
            
            # Удаляем пользователя
            db.session.delete(user)
            db.session.commit()
            
            # Логируем действие
            log_activity(f'Удален пользователь {username}', 'admin')
            
            flash(f'Пользователь {username} успешно удален.', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Ошибка при удалении пользователя: {str(e)}')
            flash(f'Ошибка при удалении пользователя: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users'))
