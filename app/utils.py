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
        
        current_app.logger.info(f"[{datetime.utcnow()}] User {user_id}: {action}")
    except Exception as e:
        # В случае ошибки только логируем, но не позволяем сбоям логирования прерывать основной процесс
        current_app.logger.error(f"Error logging activity: {str(e)}")
        if db.session.is_active:
            db.session.rollback()