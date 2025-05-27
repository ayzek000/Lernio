# Импортируем функции из app.utils.py в пакет app.utils
from datetime import datetime, timedelta
import pytz
import uuid
from flask import current_app

def get_current_tashkent_time():
    """Возвращает текущее время в часовом поясе Ташкента"""
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    return datetime.now(tashkent_tz)

def log_activity(user_id, action, details=None):
    """Логирует действие пользователя в локальную базу данных"""
    try:
        # Импортируем модели и db здесь во избежание циклических зависимостей
        from app import db
        from app.models import ActivityLog
        
        activity_log = ActivityLog(
            user_id=user_id,
            action=action,
            details=details,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(activity_log)
        db.session.commit()
        
        # Записываем в лог
        timestamp = get_current_tashkent_time().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] User {user_id}: {action}"
        if details:
            log_message += f" - {details}"
            
        current_app.logger.info(log_message)
    except Exception as e:
        # В случае ошибки только логируем, но не позволяем сбоям логирования прерывать основной процесс
        current_app.logger.error(f"Error logging activity: {str(e)}")
        if 'db' in locals() and db.session.is_active:
            db.session.rollback()
        
# Импортируем функции из модуля storage
try:
    from .storage import upload_file, delete_file, get_file_url
except ImportError:
    # Если модуль storage не найден, создаем заглушки
    def upload_file(*args, **kwargs):
        from flask import current_app
        current_app.logger.warning("Storage module not available, file upload not implemented")
        return None
    
    def delete_file(*args, **kwargs):
        from flask import current_app
        current_app.logger.warning("Storage module not available, file deletion not implemented")
        return False
    
    def get_file_url(*args, **kwargs):
        from flask import current_app
        current_app.logger.warning("Storage module not available, file URL retrieval not implemented")
        return None