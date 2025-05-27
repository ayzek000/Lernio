"""
Маршрут для удаления пользователей
"""
from flask import Blueprint, flash, redirect, url_for, request, current_app as app
from flask_login import current_user, login_required
from app import db
from app.models import User
from app.utils import log_activity
from app.admin_routes import admin_required, bp

@bp.route('/delete_user/<int:user_id>', methods=['POST'])
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
                return redirect(url_for('admin.manage_users'))
            
            username = user.username
            
            # Удаляем пользователя
            db.session.delete(user)
            db.session.commit()
            
            # Логируем действие
            log_activity(f'Удален пользователь {username}')
            
            flash(f'Пользователь {username} успешно удален.', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Ошибка при удалении пользователя: {str(e)}')
            flash(f'Ошибка при удалении пользователя: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_users'))
