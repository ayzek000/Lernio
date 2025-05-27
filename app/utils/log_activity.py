from flask import current_app
from datetime import datetime
import pytz

def get_current_tashkent_time():
    """Возвращает текущее время в часовом поясе Ташкента (UTC+5)"""
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    return datetime.now(tashkent_tz)

def log_activity(user_id, action, details=None):
    """
    Записывает действия пользователя в лог
    
    Args:
        user_id: ID пользователя
        action: Тип действия (например, "login", "upload", "delete")
        details: Дополнительная информация о действии
    """
    try:
        timestamp = get_current_tashkent_time().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] User {user_id}: {action}"
        if details:
            log_message += f" - {details}"
        
        current_app.logger.info(log_message)
        
        # В будущем можно добавить запись в базу данных
        # from app.models import ActivityLog, db
        # log_entry = ActivityLog(user_id=user_id, action=action, details=details)
        # db.session.add(log_entry)
        # db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Error logging activity: {e}")
